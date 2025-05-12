#hz-start
#consul agent -dev
# python .\api\api_gateway.py --port 8005

import argparse
from fastapi import FastAPI, HTTPException, Request
import httpx
import hazelcast
import os, sys
import uvicorn

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.consul_utils import register_service, deregister_service, fetch_instances, get_consul_kv

class APIService:
    def __init__(self, cluster_name, queue_name, service_name="api-service"):
        self.hz_client = hazelcast.HazelcastClient(cluster_name=cluster_name)
        self.service_name = service_name
        self.msg_queue = self.hz_client.get_queue(queue_name)
        self.service_id = f"{service_name}-{os.getpid()}"

        self.inventory_service_instances = []
        self.orders_service_instances = []
        self.repairs_service_instances = []
        self.order_parts_service_instances = []

    async def fetch_service_addresses(self):
        self.inventory_service_instances = await fetch_instances("inventory-service")
        self.orders_service_instances = await fetch_instances("orders-service")
        self.repairs_service_instances = await fetch_instances("repairs-service")
        self.order_parts_service_instances = await fetch_instances("order-parts-service")

        print(self.inventory_service_instances)
        print(self.orders_service_instances)
        print(self.repairs_service_instances)
        print(self.order_parts_service_instances)
    
    async def get_alive_instance(self, instances):
        for instance in instances:
            try:
                async with httpx.AsyncClient(timeout=1.0) as client:
                    health_url = f"{instance}/health"
                    resp = await client.get(health_url)
                    print(f"In get alive from {health_url}, got response {resp}")
                    if resp.status_code == 200:
                        return instance
            except Exception:
                continue
        return None

    async def proxy_request(self, service_name: str, method: str, path: str, request: Request):
        if service_name == "inventory":
            instances = self.inventory_service_instances
            print(f"Looking for inventory: {instances}")
        elif service_name == "orders":
            instances = self.orders_service_instances
        elif service_name == "repairs":
            instances = self.repairs_service_instances
        elif service_name == "order-parts":
            instances = self.order_parts_service_instances
        else:
            raise HTTPException(status_code=400, detail="Unknown service")

        if not instances:
            print("No instances, fetching new")
            await self.fetch_service_addresses()

        instance_url = await self.get_alive_instance(instances)
        if not instance_url:
            raise HTTPException(status_code=503, detail=f"No alive instances for {service_name}-service")

        url = f"{instance_url}{path}"
        headers = dict(request.headers)
        body = await request.body()

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.request(method, url, headers=headers, content=body)

        return response.json() if 'application/json' in response.headers.get("content-type", "") else response.text

    def shutdown(self):
        self.hz_client.shutdown()
        print("Hazelcast client shutdown")


app = FastAPI()
api_service = None

# -------------- DEFAULT ENDPOINTS ---------------

@app.on_event("startup")
async def startup_event():
    global api_service
    cluster_name_ = await get_consul_kv("cluster_name")
    queue_name_ = await get_consul_kv("queue_name")
    api_service = APIService(cluster_name=cluster_name_, queue_name = queue_name_)
    port = int(os.environ["APP_PORT"])
    await register_service(api_service.service_name, api_service.service_id, "localhost", port)
    await api_service.fetch_service_addresses()

@app.on_event("shutdown")
async def shutdown():
    await deregister_service(api_service.service_id)
    api_service.shutdown()
    print("API Service shutdown")

@app.get("/health")
async def health_check():
    return {"status": "OK"}

# -------------- ORDER ENDPOINTS ---------------
@app.post("/log_order")
async def log_order(request: Request):
    return await api_service.proxy_request("orders", "POST", "/log_order", request)

@app.get("/orders")
async def get_orders(request: Request):
    return await api_service.proxy_request("orders", "GET", "/orders", request)

@app.get("/orders/{order_id}")
async def get_order(order_id: str, request: Request):
    return await api_service.proxy_request("orders", "GET", f"/orders/{order_id}", request)

# -------------- REPAIR ENDPOINTS ---------------
@app.post("/log_repair")
async def log_repair(request: Request):
    return await api_service.proxy_request("repairs", "POST", "/log_repair", request)

@app.get("/repairs")
async def get_repairs(request: Request):
    return await api_service.proxy_request("repairs", "GET", "/repairs", request)

@app.get("/repairs/{repair_id}")
async def get_repair(repair_id: str, request: Request):
    return await api_service.proxy_request("repairs", "GET", f"/repairs/{repair_id}", request)

# -------------- INVENTORY ENDPOINTS ---------------
@app.post("/log_inventory")
async def log_inventory(request: Request):
    return await api_service.proxy_request("inventory", "POST", "/log_inventory", request)

@app.get("/inventory")
async def get_inventory(request: Request):
    return await api_service.proxy_request("inventory", "GET", "/inventory", request)

@app.get("/inventory/{product_id}")
async def get_inventory_item(product_id: str, request: Request):
    return await api_service.proxy_request("inventory", "GET", f"/inventory/{product_id}", request)

# -------------- ORDER PARTS ENDPOINTS ---------------
@app.get("/order-parts")
async def log_inventory(request: Request):
    return await api_service.proxy_request("order-parts", "GET", "/order-parts", request)

# -------------- STARTUP ---------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    os.environ["APP_PORT"] = str(args.port)

    uvicorn.run("api_gateway:app", host="0.0.0.0", port=args.port, reload=False)