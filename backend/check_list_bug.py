import requests
import datetime
import json
import random

BASE_URL = "http://localhost:5050/api"
# Use hardcoded creds or ensure user exists
USERNAME = "bug_test_user_6464" 
PASSWORD = "password123"

def run_test():
    # 1. Login (or Register if needed)
    print("1. Authenticating...")
    # Try login first
    resp = requests.post(f"{BASE_URL}/login", json={"username": USERNAME, "password": PASSWORD})
    if resp.status_code != 200:
        # Register
        requests.post(f"{BASE_URL}/register", json={"username": USERNAME, "password": PASSWORD})
        resp = requests.post(f"{BASE_URL}/login", json={"username": USERNAME, "password": PASSWORD})
        
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code}")
        return
        
    token = resp.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Check List (No Filter)
    print("2. Fetching All Diaries...")
    resp = requests.get(f"{BASE_URL}/diaries", headers=headers)
    diaries = resp.json()
    print(f"   Total Count: {len(diaries)}")
    
    found_29 = False
    for d in diaries:
        c = d.get('created_at', '')
        # print(f"   - {c}")
        if c.startswith('2026-01-29'):
            found_29 = True
            print(f"   ✅ Found 2026-01-29 entry: {d.get('event')}")
            
    if not found_29:
        print("   ❌ 2026-01-29 entry NOT found in list.")
        
    # 3. Check List (With Filter Year/Month)
    print("3. Fetching Jan 2026 Diaries (Filter)...")
    resp = requests.get(f"{BASE_URL}/diaries?year=2026&month=1", headers=headers)
    diaries_jan = resp.json()
    print(f"   Jan Count: {len(diaries_jan)}")
     
    found_29_jan = False
    for d in diaries_jan:
        c = d.get('created_at', '')
        if c.startswith('2026-01-29'):
            found_29_jan = True
    
    if found_29_jan:
        print("   ✅ Found 2026-01-29 entry in Jan Filter.")
    else:
        print("   ❌ 2026-01-29 entry NOT found in Jan Filter (Timezone Issue?).")

if __name__ == "__main__":
    run_test()
