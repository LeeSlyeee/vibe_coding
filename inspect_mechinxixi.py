
from pymongo import MongoClient
from datetime import datetime

# Connect to Local DB (217)
client = MongoClient("mongodb://localhost:27017/")
db = client['mood_diary_db']

target_user = "mechinxixi" # or partial match if needed
print(f"--- 🔍 Inspecting Diaries for '{target_user}' ---")

# 1. Find User ID
user = db.users.find_one({"username": target_user})
if not user:
    print(f"❌ User '{target_user}' NOT FOUND in 'users' collection.")
    # Check if there are diaries with string username instead of ID?
else:
    user_id = str(user['_id'])
    print(f"✅ Found User ID: {user_id}")

    # 2. Count Diaries
    count = db.diaries.count_documents({"user_id": user_id})
    print(f"📊 Total Diaries for {target_user}: {count}")
    
    # 3. List recent ones
    cursor = db.diaries.find({"user_id": user_id}).sort("created_at", -1).limit(10)
    for d in cursor:
        print(f" - [{d.get('date', 'NO_DATE')}] ID:{d['_id']} (Task: {d.get('task_id', 'None')})")

print("\n--- 🕵️ Checking 'Orphaned' Diaries (No User ID or different user) ---")
# Check totally random diaries that I fixed
cursor = db.diaries.find().sort("created_at", -1).limit(5)
for d in cursor:
    print(f" - Owner: {d.get('user_id')} | Date: {d.get('date')}")
