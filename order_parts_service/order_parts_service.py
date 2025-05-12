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
    parts: list[OrderPart]

class OrderPartsService:
    def __init__(self, cluster_name, queue_name, service_name="order-parts-service"):
        self.hz_client = hazelcast.HazelcastClient(cluster_name=cluster_name)
        self.service_name = service_name
        self.msg_queue = self.hz_client.get_queue(queue_name)
        self.service_id = f"{service_name}-{os.getpid()}"

    async def get_order_parts(self):
        map_ = self.hz_client.get_map("order-parts").blocking()
        all_keys = map_.key_set()
        order_parts = {key: map_.get(key) for key in all_keys}
        return order_parts

    def shutdown(self):
        self.hz_client.shutdown()
        print("Hazelcast client shutdown")


app = FastAPI()
order_parts_service = None

# -------------- DEFAULT ENDPOINTS ---------------

@app.on_event("startup")
async def startup_event():
    global order_parts_service
    cluster_name_ = await get_consul_kv("cluster_name")
    queue_name_ = await get_consul_kv("queue_name")
    order_parts_service = OrderPartsService(cluster_name=cluster_name_, queue_name = queue_name_)
    port = int(os.environ["APP_PORT"])
    await register_service(order_parts_service.service_name, order_parts_service.service_id, "localhost", port)

@app.on_event("shutdown")
async def shutdown():
    await deregister_service(order_parts_service.service_id)
    order_parts_service.shutdown()
    print("Inventory Service shutdown")

@app.get("/health")
async def health_check():
    return {"status": "OK"}

# -------------- ORDER PARTS ENDPOINTS ---------------
@app.post("/order")
async def add_order(data: OrderPartsRequest):
    print(data)
    map_ = order_parts_service.hz_client.get_map("order-parts").blocking()
    for item in data.parts:
        existing = map_.get(item.id)
        if existing:
            existing["quantity"] += item.quantity
            map_.put(item.id, existing)
        else:
            map_.put(item.id, item.dict())
    return {"status": "inventory updated", "added": [item.id for item in data.parts]}

@app.get("/order-parts")
async def get_order_parts(request: Request):
    return await order_parts_service.get_order_parts()

# -------------- STARTUP ---------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    os.environ["APP_PORT"] = str(args.port)

    uvicorn.run("order_parts_service:app", host="0.0.0.0", port=args.port, reload=False)