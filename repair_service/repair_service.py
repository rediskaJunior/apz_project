#hz-start
#consul agent -dev
# python .\inventory_service\inventory_service.py --port 8006

import argparse
from typing import Dict
from fastapi import FastAPI, HTTPException, Request
import httpx
import hazelcast
import os, sys
from pydantic import BaseModel
import uvicorn

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.consul_utils import register_service, deregister_service, fetch_instances, get_consul_kv

class OrderPart(BaseModel):
    id: str
    quantity: int

class OrderPartsRequest(BaseModel):
    orders: Dict[str, int]

class RepairService:
    def __init__(self, cluster_name, queue_name, map_name, service_name="repair-service"):
        self.hz_client = hazelcast.HazelcastClient(cluster_name=cluster_name)
        self.service_name = service_name
        self.map_name = map_name
        self.msg_queue = self.hz_client.get_queue(queue_name)
        self.service_id = f"{service_name}-{os.getpid()}"
        self.inventory_service_instances = []

    async def get_repairs(self):
        map_ = self.hz_client.get_map(self.map_name).blocking()
        all_keys = map_.key_set()
        orders = {key: map_.get(key) for key in all_keys}
        return orders
    
    async def reserve_parts(self, items: list[OrderPart]):
        if not self.inventory_service_instances:
            print("Inventory service not available")
            return False

        url = f"{self.inventory_service_instances[0]}/reserve_inventory"
        requested_parts = {
            item.id: item.quantity
            for item in items
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                resp = await client.post(url, json={"items": requested_parts})
                if resp.status_code == 200:
                    print("Reserved parts in inventory")
                    return True
                else:
                    print("Inventory service error:", resp.status_code, resp.text)
            except Exception as e:
                print("Failed to reserve parts:", e)
        return False

    
    async def fetch_service_addresses(self):
        self.inventory_service_instances = await fetch_instances("inventory-service")
        print(self.inventory_service_instances)

    def shutdown(self):
        self.hz_client.shutdown()
        print("Hazelcast client shutdown")


app = FastAPI()
repair_service = None

# -------------- DEFAULT ENDPOINTS ---------------

@app.on_event("startup")
async def startup_event():
    global repair_service
    print("cluster")
    cluster_name_ = await get_consul_kv("cluster-name")
    print("queue")
    queue_name_ = await get_consul_kv("queue-name")
    print("map")
    map_name_ = await get_consul_kv("repairs-map")
    repair_service = RepairService(cluster_name=cluster_name_, queue_name = queue_name_, map_name=map_name_)
    port = int(os.environ["APP_PORT"])
    print("register")
    await register_service(repair_service.service_name, repair_service.service_id, "localhost", port)
    print("fetch addresses")
    await repair_service.fetch_service_addresses()
@app.on_event("shutdown")
async def shutdown():
    await deregister_service(repair_service.service_id)
    repair_service.shutdown()
    print("Repairs Service shutdown")

@app.get("/health")
async def health_check():
    return {"status": "OK"}

# -------------- ORDER PARTS ENDPOINTS ---------------
@app.post("/add_repair")
async def add_repair(data: OrderPartsRequest):
    parts = [OrderPart(id=k, quantity=v) for k, v in data.orders.items()]
    reserved = await repair_service.reserve_parts(parts)
    if not reserved:
        raise HTTPException(status_code=400, detail="Could not reserve all parts")

    map_ = repair_service.hz_client.get_map(repair_service.map_name).blocking()
    for item in parts:
        map_.put(item.id, item.dict())

    return {"status": "reapir logged", "added": [item.id for item in parts]}

@app.get("/repairs")
async def get_repairs(request: Request):
    return await repair_service.get_repairs()

# -------------- STARTUP ---------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    os.environ["APP_PORT"] = str(args.port)

    uvicorn.run("repair_service:app", host="0.0.0.0", port=args.port, reload=False)