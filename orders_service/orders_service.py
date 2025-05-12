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

class OrderService:
    def __init__(self, cluster_name, queue_name, service_name="order-service"):
        self.hz_client = hazelcast.HazelcastClient(cluster_name=cluster_name)
        self.service_name = service_name
        self.msg_queue = self.hz_client.get_queue(queue_name)
        self.service_id = f"{service_name}-{os.getpid()}"
        self.inventory_service_instances = []

    async def get_orders(self):
        map_ = self.hz_client.get_map("orders").blocking()
        all_keys = map_.key_set()
        orders = {key: map_.get(key) for key in all_keys}
        return orders
    
    async def reserve_parts(self, items: list[OrderPart]):
        if not self.inventory_service_instances:
            print("Inventory service not available")
            return False

        url = f"{self.inventory_service_instances[0]}/reserve_inventory"
        requested_parts = {
            item.id: item.quantity  # Part ID is the key, and quantity is the value
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
order_service = None

# -------------- DEFAULT ENDPOINTS ---------------

@app.on_event("startup")
async def startup_event():
    global order_service
    cluster_name_ = await get_consul_kv("cluster_name")
    queue_name_ = await get_consul_kv("queue_name")
    order_service = OrderService(cluster_name=cluster_name_, queue_name = queue_name_)
    port = int(os.environ["APP_PORT"])
    await register_service(order_service.service_name, order_service.service_id, "localhost", port)
    await order_service.fetch_service_addresses()
@app.on_event("shutdown")
async def shutdown():
    await deregister_service(order_service.service_id)
    order_service.shutdown()
    print("Orders Service shutdown")

@app.get("/health")
async def health_check():
    return {"status": "OK"}

# -------------- ORDER PARTS ENDPOINTS ---------------
@app.post("/add_order")
async def add_order(data: OrderPartsRequest):
    parts = [OrderPart(id=k, quantity=v) for k, v in data.orders.items()]
    reserved = await order_service.reserve_parts(parts)
    if not reserved:
        raise HTTPException(status_code=400, detail="Could not reserve all parts")

    # If reserved, write to order map
    map_ = order_service.hz_client.get_map("orders").blocking()
    for item in parts:
        map_.put(item.id, item.dict())

    return {"status": "order placed", "added": [item.id for item in parts]}

@app.get("/orders")
async def get_orders(request: Request):
    return await order_service.get_orders()

# -------------- STARTUP ---------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    os.environ["APP_PORT"] = str(args.port)

    uvicorn.run("orders_service:app", host="0.0.0.0", port=args.port, reload=False)