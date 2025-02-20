import requests

BASE_URL = "http://localhost:8000/api"

def test_register():
    response = requests.post(f"{BASE_URL}/register", json={"username": "test_user", "customer_id": "cust_123"})
    assert response.status_code == 200
    print("✅ Registration API working!")

def test_login():
    response = requests.post(f"{BASE_URL}/login", json={"username": "test_user"})
    assert response.status_code == 200
    print("✅ Login API working!")

def test_products():
    response = requests.get(f"{BASE_URL}/products")
    assert response.status_code == 200
    print("✅ Products API working!")

def test_fraud_detection():
    response = requests.get(f"{BASE_URL}/fraud_detection")
    assert response.status_code == 200
    print("✅ Fraud Detection API working!")

if __name__ == "__main__":
    test_register()
    test_login()
    test_products()
    test_fraud_detection()
    print("🎯 All API tests passed successfully!")
