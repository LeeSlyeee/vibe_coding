import requests
import datetime
import json
import random

BASE_URL = "http://localhost:5050/api"
USERNAME = f"bug_test_user_{random.randint(1000, 9999)}"
PASSWORD = "password123"

def run_test():
    # 0. Check connection
    try:
        r = requests.get(f"{BASE_URL}/test/hello")
        print(f"0. Health Check: {r.status_code} {r.text}")
    except Exception as e:
        print(f"0. Connection failed: {e}")
        return

    # 1. Login/Register
    print("1. Authenticating...")
    requests.post(f"{BASE_URL}/register", json={"username": USERNAME, "password": PASSWORD})
    resp = requests.post(f"{BASE_URL}/login", json={"username": USERNAME, "password": PASSWORD})
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} {resp.text}")
        return
    token = resp.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Try to create a diary for YESTERDAY using 'date' field
    yesterday_dt = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    yesterday_str = yesterday_dt.strftime('%Y-%m-%d')
    print(f"2. Attempting to create diary for {yesterday_str} using key 'date'...")
    
    payload_wrong = {
        "date": yesterday_str,
        "event": "Test Event Yesterday",
        "mood_level": 3
    }
    
    resp = requests.post(f"{BASE_URL}/diaries", json=payload_wrong, headers=headers)
    if resp.status_code == 201:
        diary = resp.json()
        saved_date = diary.get('created_at') # 2026-01-29T...
        print(f"   Response created_at: {saved_date}")
        
        # Check if it matches yesterday
        if saved_date and saved_date.startswith(yesterday_str):
             print(f"   ✅ SUCCESS! 'date' field processed correctly. Saved as {saved_date}")
        else:
             print(f"   ❌ FAILED. Saved as {saved_date} (Expected {yesterday_str})")
             
    else:
        print(f"   ❌ Creation Failed: {resp.status_code} {resp.text}")
        return

    # 3. Verify List Visibility
    print("3. Verify List Check...")
    resp = requests.get(f"{BASE_URL}/diaries", headers=headers)
    diaries = resp.json()
    found = False
    for d in diaries:
        if d.get('created_at', '').startswith(yesterday_str):
            found = True
            print(f"   ✅ List Check: Found entry for {yesterday_str}")
            break
    
    if not found:
        print(f"   ❌ List Check: Entry for {yesterday_str} NOT found. List: {len(diaries)} items")

if __name__ == "__main__":
    run_test()
