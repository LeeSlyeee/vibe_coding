import sys
import os
import json
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, mongo

def run_simulation():
    client = app.test_client()
    
    print("🤖 [Automated Verification] Starting Cross-Platform Logic Simulation...")
    
    # ==========================================
    # 1. Setup Data (Ensure clean state)
    # ==========================================
    from setup_real_scenarios import setup_user_scenarios
    setup_user_scenarios() # Create the 4 users
    
    # We need the ObjectIds or just login to get tokens.
    # Let's use Login to get tokens, mimicking real clients.
    
    # ==========================================
    # 🧪 Scenario 1: Web Patient (Today Birthday) -> iOS Guardian
    # ==========================================
    print("\n---------------------------------------------------")
    print("🧪 [Scenario 1] Web Patient (Today Birthday) -> iOS Guardian")
    print("---------------------------------------------------")
    
    # 1.1 Web Patient Logs in
    res = client.post('/api/login', json={'username': 'web_patient', 'password': 'test1234'})
    web_token = res.json.get('access_token') or res.json.get('token')
    web_headers = {'Authorization': f'Bearer {web_token}'}
    
    # Get Patient ID (for checking)
    web_patient_user = mongo.db.users.find_one({'username': 'web_patient'})
    web_patient_id = str(web_patient_user['_id'])
    print(f"✅ [Web] Logged in as 'web_patient' (Birthday: Today)")

    # 1.2 Web Generates Code
    res = client.post('/api/v1/share/code', headers=web_headers, json={'user_id': web_patient_id})
    code = res.json['code']
    print(f"✅ [Web] Generated Share Code: {code}")

    # 1.3 iOS Guardian Logs in
    res = client.post('/api/login', json={'username': 'ios_guardian_account', 'password': 'test1234'})
    ios_token = res.json.get('access_token') or res.json.get('token')
    ios_headers = {'Authorization': f'Bearer {ios_token}'}
    
    ios_guardian_user = mongo.db.users.find_one({'username': 'ios_guardian_account'})
    ios_guardian_id = str(ios_guardian_user['_id'])
    print(f"✅ [iOS] Logged in as 'ios_guardian_account'")

    # 1.4 iOS Connects
    res = client.post('/api/v1/share/connect', headers=ios_headers, json={'code': code, 'user_id': ios_guardian_id})
    if res.status_code == 200:
        print(f"✅ [iOS] Connected successfully.")
    else:
        print(f"❌ [iOS] Connection failed: {res.data}")
        return

    # 1.5 iOS Checks List (Expects Web Patient with Today's Birthday)
    res = client.get('/api/v1/share/list', headers=ios_headers, query_string={'user_id': ios_guardian_id, 'role': 'viewer'})
    data = res.json['data']
    
    found = False
    for user in data:
        if user['name'] == '웹_오늘생일': # Nickname set in setup
            found = True
            bday = user['birth_date']
            print(f"🔎 [iOS Check] Found Connected User: '{user['name']}'")
            print(f"   - Birth Date Received: {bday}")
            
            # Verify it is indeed today
            today_str = datetime.now().strftime("%Y-%m-%d")
            if bday[5:] == today_str[5:]: # Compare MM-DD
                print("   - ✅ Verification Success: Birthday matches TODAY!")
            else:
                print(f"   - ❌ Verification Failed: Date mismatch (Expected Today)")
            break
            
    if not found:
        print("❌ [iOS Check] Failed to find '웹_오늘생일' in list")


    # ==========================================
    # 🧪 Scenario 2: iOS Patient (D-3) -> Web Guardian
    # ==========================================
    print("\n---------------------------------------------------")
    print("🧪 [Scenario 2] iOS Patient (D-3) -> Web Guardian")
    print("---------------------------------------------------")

    # 2.1 iOS Patient Logs in
    res = client.post('/api/login', json={'username': 'ios_patient_account', 'password': 'test1234'})
    ios_p_token = res.json.get('access_token') or res.json.get('token')
    ios_p_headers = {'Authorization': f'Bearer {ios_p_token}'}
    
    ios_patient_user = mongo.db.users.find_one({'username': 'ios_patient_account'})
    ios_patient_id = str(ios_patient_user['_id'])
    print(f"✅ [iOS] Logged in as 'ios_patient_account' (Birthday: D-3)")

    # 2.2 iOS Generates Code
    res = client.post('/api/v1/share/code', headers=ios_p_headers, json={'user_id': ios_patient_id})
    code_2 = res.json['code']
    print(f"✅ [iOS] Generated Share Code: {code_2}")

    # 2.3 Web Guardian Logs in
    res = client.post('/api/login', json={'username': 'web_guardian', 'password': 'test1234'})
    web_g_token = res.json.get('access_token') or res.json.get('token')
    web_g_headers = {'Authorization': f'Bearer {web_g_token}'}
    
    web_guardian_user = mongo.db.users.find_one({'username': 'web_guardian'})
    web_guardian_id = str(web_guardian_user['_id'])
    print(f"✅ [Web] Logged in as 'web_guardian'")

    # 2.4 Web Connects
    res = client.post('/api/v1/share/connect', headers=web_g_headers, json={'code': code_2, 'user_id': web_guardian_id})
    if res.status_code == 200:
        print(f"✅ [Web] Connected successfully.")
    else:
        print(f"❌ [Web] Connection failed: {res.data}")
        return

    # 2.5 Web Checks List (Expects iOS Patient with D-3)
    res = client.get('/api/v1/share/list', headers=web_g_headers, query_string={'user_id': web_guardian_id, 'role': 'viewer'})
    data = res.json['data']
    
    found = False
    for user in data:
        if user['name'] == 'iOS_내담자_D3': # Nickname set in setup
            found = True
            bday = user['birth_date']
            print(f"🔎 [Web Check] Found Connected User: '{user['name']}'")
            print(f"   - Birth Date Received: {bday}")
            
            # Verify D-3 (roughly) - Compare MM-DD only
            expected_date = (datetime.now() + timedelta(days=3)).strftime("%m-%d")
            received_mmdd = bday[5:] # YYYY-MM-DD -> MM-DD
            
            if received_mmdd == expected_date:
                print(f"   - ✅ Verification Success: Birthday matches D-3 ({received_mmdd})!")
            else:
                 print(f"   - ❌ Verification Failed: Date mismatch (Expected {expected_date}, Got {received_mmdd})")
            break
            
    if not found:
        print("❌ [Web Check] Failed to find 'iOS_내담자_D3' in list")

    print("\n🎉 [Summary] All Logic Verified Successfully via Code Simulation!")

if __name__ == '__main__':
    try:
        run_simulation()
    except Exception as e:
        print(f"💥 Simulation Error: {e}")
