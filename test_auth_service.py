import httpx
import asyncio

AUTH_BASE_URL = "http://localhost:8591/auth"  # change if different port or path

async def test_register():
    """Test user registration"""
    url = f"{AUTH_BASE_URL}/register"
    data = {
        "login": "test_user",
        "password": "test_password"
        }


    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            print("\nTesting Registration:")
            print(f"POST {url}")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return response.status_code in [200, 201, 400]  # 400 — user already exists
    except Exception as e:
        print(f"Registration Error: {e}")
        return False

async def test_login():
    """Test user login"""
    url = f"{AUTH_BASE_URL}/login"
    data = {
        "login": "test_user",
        "password": "test_password"
        }


    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            print("\nTesting Login:")
            print(f"POST {url}")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return response.status_code == 200
    except Exception as e:
        print(f"Login Error: {e}")
        return False

async def debug_auth():
    print("===== AUTH SERVICE TESTS =====")

    reg_ok = await test_register()
    print(f"Register Test: {'PASSED' if reg_ok else 'FAILED'}")

    login_ok = await test_login()
    print(f"Login Test: {'PASSED' if login_ok else 'FAILED'}")

    print("\n===== SUMMARY =====")
    print(f"Register: {'OK' if reg_ok else 'NOT WORKING'}")
    print(f"Login: {'OK' if login_ok else 'NOT WORKING'}")

    if not reg_ok:
        print("❗ Register might not be working — check the request format or service logic.")
    if not login_ok:
        print("❗ Login failed — either the password is incorrect or the API has an issue.")

if __name__ == "__main__":
    asyncio.run(debug_auth())
    input("\nНатисни Enter, щоб вийти...")
