import requests
import json
import time

# Based on config/urls.py
BASE_URL = "https://150.230.7.76.nip.io"
API_PREFIX = "/api/v1"

def print_result(step, response):
    status_code = response.status_code
    try:
        data = response.json()
    except:
        data = response.text[:200]  # First 200 chars if not JSON

    if 200 <= status_code < 300:
        print(f"✅ {step}: SUCCESS ({status_code})")
        # print(json.dumps(data, indent=2, ensure_ascii=False))
        return True
    else:
        print(f"❌ {step}: FAILED ({status_code})")
        print(f"   Response: {data}")
        return False

def test_flow():
    print(f"🚀 Starting 150 Server Verification on {BASE_URL}...")
    
    unique_id = int(time.time())
    user_uuid = f"test_uuid_{unique_id}"
    
    # 1. Connectivity Check (Swagger)
    print("\n--- 1. Connectivity Check (Swagger) ---")
    try:
        resp = requests.get(f"{BASE_URL}/swagger/", timeout=10)
        if resp.status_code == 200:
            print("✅ Swagger UI: REACHABLE (200 OK)")
        else:
            print(f"⚠️ Swagger UI: {resp.status_code}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    # 2. Verify Linkage Code (Expecting 'Institution not found' or similar)
    print("\n--- 2. Linkage Code Check (centers/verify-code/) ---")
    # Endpoint from centers/urls.py: path('verify-code/', ...) -> /api/v1/centers/verify-code/
    target_url = f"{BASE_URL}{API_PREFIX}/centers/verify-code/"
    payload = {"code": "INVALID_CODE_999", "uuid": user_uuid}
    
    try:
        resp = requests.post(target_url, json=payload, timeout=10)
        # We expect 404 (if code checks DB) or 400.
        # If it returns 404 HTML (Nginx), then routing is still wrong.
        # If it returns JSON error, routing is CORRECT.
        print_result("Verify Invalid Code", resp)
    except Exception as e:
        print(f"❌ Request Error: {e}")

    # 3. Sync Data Probe
    print("\n--- 3. Sync Data Probe (centers/sync-data/) ---")
    target_url = f"{BASE_URL}{API_PREFIX}/centers/sync-data/"
    sync_payload = {"uuid": user_uuid, "diaries": []}
    
    try:
        resp = requests.post(target_url, json=sync_payload, timeout=10)
        print_result("Sync Empty Data", resp)
    except Exception as e:
        print(f"❌ Request Error: {e}")

if __name__ == "__main__":
    test_flow()
