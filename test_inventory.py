import httpx

async def send_inventory_data():
    url = "http://localhost:8005/log_inventory"  # Your FastAPI inventory service URL
    headers = {"Content-Type": "application/json"}
    inventory_data = {
        "items": [
            {
                "id": "product_1",
                "name": "Product 1",
                "quantity": 150,
                "available_quantity": 100,
                "price": 19.99,
                "category": "Electronics"
            },
            {
                "id": "product_2",
                "name": "Product 2",
                "quantity": 75,
                "available_quantity": 50,
                "price": 29.99,
                "category": "Furniture"
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=inventory_data, headers=headers)
        print("Response Status:", response.status_code)
        print("Response Body:", response.json())

# Run the function to send data
import asyncio
asyncio.run(send_inventory_data())
