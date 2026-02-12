import requests
import json
from datetime import datetime

def test_guest_sync():
    url = "http://127.0.0.1:5050/api/v1/centers/sync-data/"
    
    payload = {
        "center_code": "IV7L90SYBT",
        "user_nickname": "Guest",
        "risk_level": 0,
        "mood_metrics": [
            {
                "content": "TEST_DIARY_FEB_10_GUEST_SYNC",
                "created_at": "2026-02-10 12:00:00",
                "date": "2026-02-10",
                "mood_score": 50,
                "emotions": ["happy"],
                "keywords": ["test"]
            }
        ]
    }
    
    print(f"🚀 Sending Guest Sync Request to {url}...")
    try:
        resp = requests.post(url, json=payload)
        print(f"Response Status: {resp.status_code}")
        print(f"Response specific: {resp.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_guest_sync()
