import requests
import json

base_url = "http://127.0.0.1:5000"

# 1. Login
login_payload = {
    "username": "slyeee",
    "password": "mechin12qw!!"  # Updated to match user attempt
}
print(f"Logging in as {login_payload['username']}...")
try:
    resp = requests.post(f"{base_url}/api/login", json=login_payload)
    print(f"Login Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Login Failed: {resp.text}")
        exit(1)
    
    data = resp.json()
    token = data.get('access_token') or data.get('token')
    print(f"Token received: {token[:20]}...")
except Exception as e:
    print(f"Login Exception: {e}")
    exit(1)

# 2. Access Protected Route
headers = {
    "Authorization": f"Bearer {token}"
}
print("\nAccessing /api/user/me...")
resp = requests.get(f"{base_url}/api/user/me", headers=headers)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")

# 3. Access Diaries
print("\nAccessing /api/diaries...")
resp = requests.get(f"{base_url}/api/diaries?year=2026&month=2", headers=headers)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:200]}...")
