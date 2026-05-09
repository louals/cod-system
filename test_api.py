import httpx
import json

BASE_URL = "http://127.0.0.1:8000"

def test_root():
    response = httpx.get(f"{BASE_URL}/")
    print(f"Root: {response.json()}")

def test_get_products():
    response = httpx.get(f"{BASE_URL}/products")
    print(f"Products: {json.dumps(response.json(), indent=2)}")

def test_create_order():
    order_data = {
        "customer_name": "John Doe",
        "customer_phone": "123456789",
        "customer_address": "123 Main St",
        "customer_city": "New York",
        "items": [
            {
                "product_id": "REPLACE_WITH_REAL_ID",
                "quantity": 1
            }
        ]
    }
    response = httpx.post(f"{BASE_URL}/orders", json=order_data)
    print(f"Order Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    print("Run this after starting the server with 'uvicorn main:app --reload'")
    # test_root()
    # test_get_products()
