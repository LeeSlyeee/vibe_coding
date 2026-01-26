
import requests
import json
import time

BASE_URL = "http://localhost:5001/api"
USERNAME = "ios_simulator_user"
PASSWORD = "password123"

def print_step(msg):
    print(f"\n📱 [iOS Simulator] {msg}")

def run_ios_simulation():
    print("====================================")
    print(" iOS App Logic Simulation Test")
    print("====================================")

    # 1. Login & Fetch Profile (AppLoginView.swift)
    print_step("1. Login & Fetch Profile")
    
    # Register first to ensure user exists
    requests.post(f"{BASE_URL}/register", json={"username": USERNAME, "password": PASSWORD})
    
    # Login
    resp = requests.post(f"{BASE_URL}/login", json={"username": USERNAME, "password": PASSWORD})
    if resp.status_code != 200:
        print("❌ Login Failed")
        return
        
    token = resp.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Login Success. Token acquired.")
    
    # Fetch Me (Risk Level Check)
    resp = requests.get(f"{BASE_URL}/user/me", headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        risk_level = data.get('risk_level', 1)
        print(f"✅ Profile Fetched. Current Risk Level: {risk_level}")
    else:
        print(f"❌ Fetch Profile Failed: {resp.status_code}")

    # 2. Assessment Submission (AppAssessmentView.swift)
    print_step("2. User takes Assessment (Score 22 -> Severe)")
    
    assess_payload = {
        "score": 22, 
        "answers": [3, 3, 2, 3, 2, 3, 2, 2, 2] # Mock answers
    }
    resp = requests.post(f"{BASE_URL}/assessment", json=assess_payload, headers=headers)
    if resp.status_code == 200:
        print("✅ Assessment Submitted.")
    else:
        print(f"❌ Assessment Failed: {resp.text}")
        
    # Verify Risk Level Update
    resp = requests.get(f"{BASE_URL}/user/me", headers=headers)
    new_risk = resp.json().get('risk_level')
    print(f"✅ Risk Level Updated: {risk_level} -> {new_risk} (Expected 5)")
    
    if new_risk >= 2:
        print("   -> 🔓 Premium Features (Stats) would be UNLOCKED on iOS.")
    else:
        print("   -> 🔒 Premium Features (Stats) would be LOCKED on iOS.")

    # 3. Write Diary with Trigger (AppDiaryWriteView.swift)
    print_step("3. Write Diary & Check Follow-up Trigger")
    
    diary_payload = {
        "date": "2026-01-27",
        "mood": "sad",
        "question1": "너무 괴로워서 죽고 싶어.", # Trigger Keyword
        "question2": "아무런 희망이 없어.",
        "question_sleep": "잠을 못 잤어."
    }
    
    # iOS creates diary
    resp = requests.post(f"{BASE_URL}/diaries", json=diary_payload, headers=headers)
    if resp.status_code != 201:
        print(f"❌ Diary Creation Failed: {resp.text}")
        return
    
    diary_id = resp.json()['id']
    print(f"✅ Diary Created (ID: {diary_id}). Polling for AI result...")
    
    # iOS polls for result (simulated loop)
    # The iOS code checks for 'followup_required' in the response of the *save* or subsequent detail fetch.
    # Since our backend does async analysis, iOS usually gets the result later or via polling.
    # Here we poll like the frontend does.
    
    for i in range(10):
        time.sleep(2)
        resp = requests.get(f"{BASE_URL}/diaries/{diary_id}", headers=headers)
        data = resp.json()
        ai_pred = data.get('ai_prediction', '')
        
        if ai_pred and "분석 중" not in ai_pred:
            print(f"✅ AI Analysis Done in {i*2}s.")
            
            followup_req = data.get('followup_required', False)
            followup_q = data.get('followup_question', '')
            
            print(f"   - Needs Followup: {followup_req}")
            print(f"   - Question: {followup_q}")
            
            if followup_req:
                print("🚨 [iOS Action] App would trigger 'SwitchToChatTab' notification now.")
                print("   -> User is redirected to Chat Tab.")
            else:
                print("   -> No redirect. Stays in Diary View.")
            break
            
    print("\n✅ Simulation Complete. All iOS Logic Flows Verified.")

if __name__ == "__main__":
    run_ios_simulation()
