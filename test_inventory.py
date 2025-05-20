import httpx
import asyncio

async def test_inventory_connection():
    url = "http://localhost:5680/inventory"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            print("\nTesting Inventory API Connection:")
            print(f"GET {url}")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:100]}..." if len(response.text) > 100 else f"Response: {response.text}")
            return response.status_code == 200
    except Exception as e:
        print(f"Connection Error: {e}")
        return False

async def test_log_inventory():
    url = "http://localhost:5680/log_inventory"
    headers = {"Content-Type": "application/json"}

    request_data = {
        "items": [
            {
                "id": "product_test_1",
                "name": "Test Component 1",
                "quantity": 20,
                "available_quantity": 15,
                "price": 9.99,
                "category": "component"
            },
            {
                "id": "product_test_2",
                "name": "Test Phone 2",
                "quantity": 10,
                "available_quantity": 8,
                "price": 199.99,
                "category": "phone"
            }
        ]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=request_data, headers=headers)
            print("\nTesting Log Inventory:")
            print(f"POST {url}")
            print(f"Request Data: {request_data}")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:100]}..." if len(response.text) > 100 else f"Response: {response.text}")
            return response.status_code == 200
    except Exception as e:
        print(f"Log Inventory Error: {e}")
        return False

async def debug_inventory_tests():
    print("===== INVENTORY API DEBUG TESTS =====")

    # Test 1: Basic API connection
    print("\nTest 1: Inventory API Connection")
    conn_ok = await test_inventory_connection()
    print(f"Inventory Connection Test: {'PASSED' if conn_ok else 'FAILED'}")

    # Test 2: Logging inventory
    print("\nTest 2: Log Inventory")
    log_ok = await test_log_inventory()
    print(f"Log Inventory Test: {'PASSED' if log_ok else 'FAILED'}")

    # Summary
    print("\n===== TEST SUMMARY =====")
    print(f"Inventory API Connection: {'OK' if conn_ok else 'NOT WORKING'}")
    print(f"Log Inventory: {'OK' if log_ok else 'NOT WORKING'}")

    if not conn_ok:
        print("\nTROUBLESHOOTING TIPS:")
        print("1. Ensure inventory backend is running at http://localhost:8700")
        print("2. Verify /inventory is a GET endpoint")
        print("3. Check firewall or port blocking")

    if conn_ok and not log_ok:
        print("\nTROUBLESHOOTING TIPS:")
        print("1. Check that /log_inventory accepts your JSON format")
        print("2. Inspect server logs for validation or type errors")
        print("3. Confirm item structure matches InventoryLogRequest")

if __name__ == "__main__":
    asyncio.run(debug_inventory_tests())
