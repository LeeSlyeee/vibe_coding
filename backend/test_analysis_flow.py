
import requests
import json
import time

BASE_URL = "http://localhost:5001/api"


def run_user_test(username, risk_target_score):
    print(f"\n\n=============================================")
    print(f"👤 Testing User: {username} (Target Score: {risk_target_score})")
    print(f"=============================================")
    
    # 1. Register/Login
    payload = {"username": username, "password": "password123"} 
    requests.post(f"{BASE_URL}/register", json=payload) # Ensure exists
    resp = requests.post(f"{BASE_URL}/login", json=payload)
    
    if resp.status_code != 200:
        print("❌ Login Failed")
        return

    token = resp.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Set Risk Level via Assessment
    # Score 0-4 (Level 1), 20+ (Level 5)
    assess_payload = {"score": risk_target_score, "answers": []}
    requests.post(f"{BASE_URL}/assessment", json=assess_payload, headers=headers)
    print(f"📊 Risk Level Set (Score {risk_target_score})")
    
    # 3. Create Diary (Trigger Content)
    diary_payload = {
        "date": "2026-01-26",
        "mood": "sad",
        "question1": "너무 힘들어서 죽고 싶다는 생각이 들어. 아무 희망이 없어.", 
        "question2": "절망적이야.",
        "question_sleep": "잠을 못 잤어."
    }
    
    print("🚀 Sending Diary...")
    resp = requests.post(f"{BASE_URL}/diaries", json=diary_payload, headers=headers)
    
    if resp.status_code != 201:
        print("❌ Failed to create diary")
        return

    diary_id = resp.json()['id']
    
    # 4. Poll
    for i in range(15):
        time.sleep(2)
        print(f"⏳ Polling {i+1}...", end="\r")
        res = requests.get(f"{BASE_URL}/diaries/{diary_id}", headers=headers)
        if res.status_code == 200:
            data = res.json()
            ai_pred = data.get('ai_prediction', '')
            
            if "분석 중" not in ai_pred and ai_pred:
                print(f"\n✅ Analysis Complete! [{username}]")
                print(f"   Prediction: {data.get('ai_prediction')}")
                print(f"   Followup Required: {data.get('followup_required')}")
                print(f"   Question: {data.get('followup_question')}")
                return

if __name__ == "__main__":
    # Test Mild User (Score 3 -> Level 1)
    run_user_test("mild_test", 3)
    
    # Test Severe User (Score 22 -> Level 5)
    run_user_test("severe_test", 22)

