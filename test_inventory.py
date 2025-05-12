import httpx
import asyncio

async def test_reserve_inventory():
    url = "http://localhost:8009/reserve_inventory"
    headers = {"Content-Type": "application/json"}
    request_data = {
        "parts": {
            "product_1": 40,
            "product_2": 30
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=request_data, headers=headers)
        print("Status Code:", response.status_code)
        print("Response:", response.json())

asyncio.run(test_reserve_inventory())
