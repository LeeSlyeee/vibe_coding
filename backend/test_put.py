
import requests
import json

BASE_URL = "http://127.0.0.1:5000/api"

# 1. Login
login_payload = {
    "username": "slyeee",
    "password": "mechin12qw!!" 
}

try:
    print("Trying login...")
    r = requests.post(f"{BASE_URL}/login", json=login_payload)
    if r.status_code != 200:
        print(f"Login failed: {r.status_code} {r.text}")
        exit(1)
        
    token = r.json().get('access_token')
    print(f"Got token: {token[:10]}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 2. Get Diary (to find an ID)
    print("Fetching diaries...")
    r = requests.get(f"{BASE_URL}/diaries", headers=headers)
    diaries = r.json()
    if not diaries:
        print("No diaries found.")
        exit(1)
        
    target_id = diaries[0]['id']
    print(f"Target Diary ID: {target_id}")
    
    # 3. PUT Request
    print(f"Testing PUT on /diaries/{target_id}...")
    update_data = {
        "event": "Automated Test Update",
        "mood_level": 5
    }
    
    r = requests.put(f"{BASE_URL}/diaries/{target_id}", json=update_data, headers=headers)
    
    print(f"PUT Status: {r.status_code}")
    print(f"PUT Response: {r.text}")

except Exception as e:
    print(f"Error: {e}")
