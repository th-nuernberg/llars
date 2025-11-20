"""
Integration Test: Login und LiteLLM
Tests Backend-Authentifizierung und LiteLLM-Integration
"""

import requests
import json
import time

BASE_URL = "http://localhost:55081"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("Test 1: Health Check")
    print("="*60)

    response = requests.get(f"{BASE_URL}/auth/health_check")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 200, "Health check failed"
    print("✓ Health check passed")
    return True

def test_registration():
    """Test user registration"""
    print("\n" + "="*60)
    print("Test 2: User Registration")
    print("="*60)

    username = f"testuser_{int(time.time())}"
    email = f"test_{int(time.time())}@example.com"

    data = {
        "username": username,
        "email": email,
        "password": "TestPass123!",
        "first_name": "Test",
        "last_name": "User"
    }

    response = requests.post(
        f"{BASE_URL}/auth/register",
        json=data,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 201, f"Registration failed: {response.text}"
    print(f"✓ Registration successful for user: {username}")

    return username, "TestPass123!"

def test_login(username, password):
    """Test user login"""
    print("\n" + "="*60)
    print("Test 3: User Login")
    print("="*60)

    data = {
        "username": username,
        "password": password
    }

    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=data,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status: {response.status_code}")
    response_data = response.json()
    print(f"Response keys: {list(response_data.keys())}")

    assert response.status_code == 200, f"Login failed: {response.text}"
    assert "access_token" in response_data or "token" in response_data, "No token in response"

    print(f"✓ Login successful for user: {username}")
    return response_data

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("LLARS Integration Test: Login & LiteLLM")
    print("="*60)

    try:
        # Test 1: Health Check
        test_health()

        # Test 2: Registration
        username, password = test_registration()

        # Test 3: Login
        login_data = test_login(username, password)

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nSummary:")
        print("✓ Backend is healthy")
        print("✓ User registration works")
        print("✓ User login works")
        print("✓ Authentication system functional")
        print("\nNote: LiteLLM integration tested separately via app/llm/test_litellm.py")

        return True

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
