import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5001/api"

def run_test():
    session = requests.Session()
    
    # 1. Login or Register
    print("🔹 1. Login...")
    login_payload = {"username": "slyeee_test", "password": "password123"}
    res = session.post(f"{BASE_URL}/login", json=login_payload)
    
    if res.status_code != 200:
        print("   Login failed, trying register...")
        res = session.post(f"{BASE_URL}/register", json=login_payload)
        if res.status_code == 201:
            print("   Registered. Logging in again...")
            res = session.post(f"{BASE_URL}/login", json=login_payload)
        else:
            print(f"   Register failed: {res.text}")
            return

    token = res.json().get('access_token')
    headers = {"Authorization": f"Bearer {token}"}
    print(f"   Login Success. Token: {token[:10]}...")

    # 2. Check Insight (Empty State)
    print("\n🔹 2. Getting Insight (Before creating diary)...")
    try:
        res = session.get(f"{BASE_URL}/insight", headers=headers, params={"weather": "맑음"})
        print(f"   Response: {res.json()}")
    except Exception as e:
        print(f"   Error: {e}")

    # 3. Create a Test Diary (Yesterday) to provide context
    print("\n🔹 3. Creating Past Diary...")
    yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
    diary_payload = {
        "date": yesterday,
        "event": "어제는 정말 힘든 하루였어. 코딩이 너무 안 돼서 스트레스 받았어.",
        "mood_level": 2,
        "weather": "흐림",
        "mode": "green"
    }
    res = session.post(f"{BASE_URL}/diaries", json=diary_payload, headers=headers)
    print(f"   Created Diary: {res.status_code}")

    # 4. Check Insight Again (With Context)
    print("\n🔹 4. Getting Insight (With Context)...")
    try:
        res = session.get(f"{BASE_URL}/insight", headers=headers, params={"weather": "맑음"})
        print(f"   Response: {res.json()}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    run_test()
