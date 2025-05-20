#hz-start
#consul agent -dev
# python .\inventory_service\inventory_service.py --port 8006

import argparse
from fastapi import FastAPI, HTTPException, Request
import httpx
import hazelcast
import os, sys
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.consul_utils import register_service, deregister_service, fetch_instances, get_consul_kv

class InventoryItem(BaseModel):
    id: str
    name: str
    quantity: int
    available_quantity: int
    price: float
    category: str = "General"

class InventoryLogRequest(BaseModel):
    items: list[InventoryItem]

class InventoryService:
    def __init__(self, cluster_name, queue_name, map_name, service_name="inventory-service"):
        self.hz_client = hazelcast.HazelcastClient(cluster_name=cluster_name)
        self.service_name = service_name
        self.map_name = map_name
        self.msg_queue = self.hz_client.get_queue(queue_name)
        self.service_id = f"{service_name}-{os.getpid()}"
        self.order_parts_service_instances = []

    async def fetch_service_addresses(self):
        order_parts_instances = await fetch_instances("order-parts-service")

        print(order_parts_instances)

        if order_parts_instances:
            self.order_parts_service_instances = order_parts_instances
            return True

        return False
    
    async def check_and_reserve(self, requested_parts: dict):
        map_ = self.hz_client.get_map(self.map_name).blocking()
        missing_parts = {}

        for part_id, quantity in requested_parts.items():
            item = map_.get(part_id)
            print(item)
            if item and item["available_quantity"] >= quantity:
                item["available_quantity"] -= quantity
                map_.put(part_id, item)
            else:
                missing_parts[part_id] = quantity - (item["available_quantity"] if item else 0)
                if item:
                    item["available_quantity"] = 0
                    map_.put(part_id, item)

        if missing_parts:
            print("Missing parts detected")
            print(missing_parts)
            await self.send_missing_to_order_service(missing_parts)

        return {"reserved": requested_parts, "missing": missing_parts}

    
    async def send_missing_to_order_service(self, missing_parts: dict):
        if not self.order_parts_service_instances:
            print("Order-parts service not available")
            return

        url = f"{self.order_parts_service_instances[0]}/order"
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                payload = {"parts": [{"id": k, "quantity": v} for k, v in missing_parts.items()]}
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    print("Order service acknowledged missing parts")
                else:
                    print("Order service responded with error:", resp.status_code)
            except Exception as e:
                print("Failed to send missing parts:", e)

    async def get_inventory(self):
        map_ = self.hz_client.get_map(self.map_name).blocking()
        all_keys = map_.key_set()
        inventory = {key: map_.get(key) for key in all_keys}
        return inventory
    async def get_inventory_instance(self, product_id: str):
        map_ = self.hz_client.get_map(self.map_name).blocking()
        quantity = map_.get(product_id)
        if quantity is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return {product_id: quantity}


    def shutdown(self):
        self.hz_client.shutdown()
        print("Hazelcast client shutdown")


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or replace "*" with the frontend's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
api_service = None

# -------------- DEFAULT ENDPOINTS ---------------

@app.on_event("startup")
async def startup_event():
    global inventory_service
    cluster_name_ = await get_consul_kv("cluster-name")
    queue_name_ = await get_consul_kv("queue-name")
    map_name_ = await get_consul_kv("inventory-map")
    inventory_service = InventoryService(cluster_name=cluster_name_, queue_name = queue_name_, map_name=map_name_)
    port = int(os.environ["APP_PORT"])
    await register_service(inventory_service.service_name, inventory_service.service_id, "localhost", port)
    await inventory_service.fetch_service_addresses()

@app.on_event("shutdown")
async def shutdown():
    await deregister_service(inventory_service.service_id)
    inventory_service.shutdown()
    print("Inventory Service shutdown")

@app.get("/health")
async def health_check():
    return {"status": "OK"}

# -------------- INVENTORY ENDPOINTS ---------------
@app.post("/log_inventory")
async def log_inventory(data: InventoryLogRequest):
    map_ = inventory_service.hz_client.get_map(inventory_service.map_name).blocking()
    for item in data.items:
        existing = map_.get(item.id)
        if existing:
            existing["quantity"] += item.quantity
            existing["available_quantity"] += item.available_quantity
            map_.put(item.id, existing)
        else:
            map_.put(item.id, item.dict())
    return {"status": "inventory updated", "added": [item.id for item in data.items]}

@app.post("/reserve_inventory")
async def reserve_inventory(request: Request):
    data = await request.json()
    print(data)
    requested_parts = data.get("items", {})
    print(requested_parts)
    return await inventory_service.check_and_reserve(requested_parts)


@app.get("/inventory")
async def get_inventory(request: Request):
    return await inventory_service.get_inventory()

@app.get("/inventory/{product_id}")
async def get_inventory_item(product_id: str, request: Request):
    return await inventory_service.get_inventory_instance(product_id)

# -------------- STARTUP ---------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    os.environ["APP_PORT"] = str(args.port)

    uvicorn.run("inventory_service:app", host="0.0.0.0", port=args.port, reload=False)