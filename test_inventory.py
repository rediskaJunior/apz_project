import httpx
import asyncio

async def test_reserve_inventory():
    url = "http://localhost:8025/add_order"
    headers = {"Content-Type": "application/json"}
    request_data = {
        "orders": {
            "part-123": 2,
            "part-456": 1
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=request_data, headers=headers)
        print("Status Code:", response.status_code)
        print("Response:", response.json())

asyncio.run(test_reserve_inventory())
