
from pymongo import MongoClient
from datetime import datetime
import sys

# Connect to Local MongoDB (217)
client = MongoClient("mongodb://localhost:27017/")
db = client['mood_diary_db']

print("--- Searching for Jan 29 Diaries ---")

# Try String Match
d1 = db.diaries.find_one({"date": "2026-01-29"})
if d1:
    print(f"[Match by DateString] Found ID: {d1['_id']}")
else:
    print(f"[Match by DateString] NOT FOUND")

# Try Date Object Range (Just in case)
start = datetime(2026, 1, 28)
end = datetime(2026, 1, 30)
cursor = db.diaries.find({"created_at": {"$gte": start, "$lt": end}})

count = 0
for d in cursor:
    print(f"[Match by CreatedAt] Found ID: {d['_id']} | Date: {d.get('date')} | Created: {d.get('created_at')}")
    count += 1
    
if count == 0:
    print("No diaries found near Jan 29 via CreatedAt.")
