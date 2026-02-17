import requests
import json
import time
from datetime import datetime

BASE_URL = "https://217.142.253.35.nip.io/api"
# BASE_URL = "http://localhost:5000/api" # For local testing if needed

def generate_user():
    timestamp = int(time.time())
    return {
        "username": f"verifier_{timestamp}",
        "password": "password123",
        "nickname": f"Verifier_{timestamp}",
        "email": f"verifier_{timestamp}@test.com"
    }

def run_test():
    print(f"🚀 Starting Self-Verification Test against {BASE_URL}...")
    
    # 1. Register
    user_data = generate_user()
    print(f"\n1️⃣ Registering User: {user_data['username']}...")
    try:
        res = requests.post(f"{BASE_URL}/register", json=user_data, verify=False)
        if res.status_code == 201:
            print("✅ Registration Success")
        else:
            print(f"❌ Registration Failed: {res.status_code} {res.text}")
            return
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    # 2. Login
    print(f"\n2️⃣ Logging In...")
    login_payload = {
        "username": user_data['username'],
        "password": user_data['password']
    }
    res = requests.post(f"{BASE_URL}/login", json=login_payload, verify=False)
    if res.status_code != 200:
        print(f"❌ Login Failed: {res.status_code} {res.text}")
        return
    
    token = res.json().get('access_token')
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login Success")

    # 3. Create Diary
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"\n3️⃣ Creating Diary for {today_str}...")
    diary_payload = {
        "date": today_str,
        "event": "Test Event content",
        "mood_level": 4,
        "sleep_condition": "Good sleep",
        "emotion_desc": "Feeling tested",
        "emotion_meaning": "Verification is important",
        "self_talk": "I strictly use PostgreSQL",
        "question1": "Test Q1", # Fallback check
        "question2": "Test Q2",
        "question3": "Test Q3",
        "question4": "Test Q4"
    }
    
    res = requests.post(f"{BASE_URL}/diaries", json=diary_payload, headers=headers, verify=False)
    if res.status_code == 201:
        diary_id = res.json().get('id')
        print(f"✅ Diary Created! ID: {diary_id}")
    else:
        print(f"❌ Create Diary Failed: {res.status_code} {res.text}")
        return

    # 4. Fetch Diary by Date (The new endpoint)
    print(f"\n4️⃣ Fetching Diary by Date ({today_str})...")
    res = requests.get(f"{BASE_URL}/diaries/date/{today_str}", headers=headers, verify=False)
    if res.status_code == 200:
        data = res.json()
        print(f"✅ Fetch by Date Success: ID={data.get('id')}, Source={data.get('source', 'PostgreSQL')}")
        if data.get('event') == "Test Event content":
             print("   -> Content Verified")
        else:
             print(f"   -> Content Mismatch: {data.get('event')}")
    else:
        print(f"❌ Fetch by Date Failed: {res.status_code} {res.text}")

    # 5. Update Diary
    print(f"\n5️⃣ Updating Diary...")
    update_payload = {
        "event": "Updated Test Event",
        "mood_level": 5
    }
    res = requests.post(f"{BASE_URL}/diaries/{diary_id}/upt", json=update_payload, headers=headers, verify=False)
    if res.status_code == 200:
        print("✅ Update Success")
    else:
        print(f"❌ Update Failed: {res.status_code} {res.text}")

    # 6. Verify Update
    print(f"\n6️⃣ Verifying Update...")
    res = requests.get(f"{BASE_URL}/diaries/{diary_id}", headers=headers, verify=False)
    if res.status_code == 200:
        data = res.json()
        if data.get('event') == "Updated Test Event" and data.get('mood_level') == 5:
            print("✅ Update Verified Correctly")
        else:
            print(f"❌ Update Verification Failed: {data}")

    # 7. Delete Diary
    print(f"\n7️⃣ Deleting Diary...")
    res = requests.delete(f"{BASE_URL}/diaries/{diary_id}", headers=headers, verify=False)
    if res.status_code == 200:
        print("✅ Delete Success")
    else:
        print(f"❌ Delete Failed: {res.status_code} {res.text}")

    # 8. Verify Deletion
    print(f"\n8️⃣ Verifying Deletion...")
    res = requests.get(f"{BASE_URL}/diaries/{diary_id}", headers=headers, verify=False)
    if res.status_code == 404:
        print("✅ Deletion Verified (404 returned)")
    else:
        print(f"❌ Deletion Verification Failed: Expected 404, got {res.status_code}")

    print("\n🎉 Self-Verification Complete!")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    run_test()
