import httpx
import asyncio

async def test_api_connection():
    """Test basic API connectivity"""
    url = "http://localhost:8700/orders"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            print("\nTesting API Connection:")
            print(f"GET {url}")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:100]}..." if len(response.text) > 100 else f"Response: {response.text}")
            
            return response.status_code == 200
    except Exception as e:
        print(f"Connection Error: {e}")
        return False

async def test_add_order():
    """Test the add_order endpoint with correctly formatted data"""
    url = "http://localhost:8700/add_order"
    headers = {"Content-Type": "application/json"}
    
    # Only includes "orders" field as expected by the API
    request_data = {
        "orders": {
            "product_1": 10,
            "product_2": 5
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=request_data, headers=headers)
            print("\nTesting Add Order:")
            print(f"POST {url}")
            print(f"Request Data: {request_data}")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:100]}..." if len(response.text) > 100 else f"Response: {response.text}")
            
            return response.status_code == 200
    except Exception as e:
        print(f"Add Order Error: {e}")
        return False

async def debug_tests():
    """Run tests to debug the connection between frontend and backend"""
    print("===== ORDERS API DEBUG TESTS =====")
    
    # Test 1: Basic API connection
    print("\nTest 1: API Connection")
    api_ok = await test_api_connection()
    print(f"API Connection Test: {'PASSED' if api_ok else 'FAILED'}")
    
    # Test 2: Adding an order
    print("\nTest 2: Add Order")
    add_ok = await test_add_order()
    print(f"Add Order Test: {'PASSED' if add_ok else 'FAILED'}")
    
    # Summary
    print("\n===== TEST SUMMARY =====")
    print(f"API Connection: {'OK' if api_ok else 'NOT WORKING'}")
    print(f"Add Order: {'OK' if add_ok else 'NOT WORKING'}")
    
    if not api_ok:
        print("\nTROUBLESHOOTING TIPS:")
        print("1. Make sure your orders backend server is running at http://localhost:8540")
        print("2. Check for any firewall or network issues")
        print("3. Verify the backend is accepting connections")
    
    if api_ok and not add_ok:
        print("\nTROUBLESHOOTING TIPS:")
        print("1. Check if the API expects a different request format")
        print("2. Look at server logs for validation errors")
        print("3. Verify that the 'orders' field is properly formatted")

if __name__ == "__main__":
    asyncio.run(debug_tests())