import requests
import json
from datetime import datetime, timezone
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://217.142.253.35.nip.io/api"

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc3Mjk0OTc0MiwianRpIjoiNWVmZDgwMGQtMWQ1YS00MWU1LTg0YjktN2QwMmQ5OGMzNzcwIiwidHlwZSI6ImFjY2VzcyIsInVzZXJfaWQiOiIzNiIsIm5iZiI6MTc3Mjk0OTc0MiwiY3NyZiI6IjFmY2NhNDNlLWJlZGMtNGIwNC04ZDE5LTUxNGI0MTY5Mjk1MyIsImV4cCI6MjA4ODMwOTc0Mn0.PevWTXfkF7jO-zezOzAqYmSm9V6EbpIP3cRtY2EPCuE"
headers = {"Authorization": f"Bearer {token}"}
print("Using predefined token.")

# 2. Get today's diary
today = datetime.now().strftime("%Y-%m-%d")
print(f"2. Getting diaries to find today's ({today})")
resp = requests.get(f"{BASE_URL}/diaries", headers=headers, verify=False)
if resp.status_code == 200:
    diaries = resp.json()
    today_diary = next((d for d in diaries if d["date"] == today), None)
    if today_diary:
        print(f"Found today's diary (ID: {today_diary['id']}). Deleting...")
        del_resp = requests.delete(f"{BASE_URL}/diaries/{today_diary['id']}", headers=headers, verify=False)
        print("Delete response:", del_resp.status_code)
    else:
        print("No diary found for today.")
else:
    print("Failed to get diaries:", resp.text)

time.sleep(1)

# 3. Create new diary
print("3. Creating new diary for today")
new_diary = {
    "date": today,
    "event": "오늘은 기분이 정말 우울하고 힘들어요. 아무것도 하기 싫고, 그냥 누워만 있고 싶네요. 내 삶의 의미를 못 찾겠어요... 도와주세요.",
    "mood_level": 1,
    "weather": "비",
    "diary_type": "text"
}
resp = requests.post(f"{BASE_URL}/diaries", json=new_diary, headers=headers, verify=False)
print("Create response:", resp.status_code, resp.text)
if resp.status_code == 201:
    print("Diary created successfully. Wait a few seconds for AI analysis and push notification...")
else:
    print("Failed to create diary.")
