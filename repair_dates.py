
from pymongo import MongoClient
from datetime import datetime

# Connect to Local DB (217)
client = MongoClient("mongodb://localhost:27017/")
db = client['mood_diary_db']

print("--- 🔧 Starting Date Field Repair ---")

# Find diaries where 'date' is missing but 'created_at' exists
cursor = db.diaries.find({
    "date": {"$exists": False},
    "created_at": {"$exists": True}
})

fixed_count = 0
for d in cursor:
    created = d.get('created_at')
    if isinstance(created, datetime):
        date_str = created.strftime("%Y-%m-%d")
        
        # Update
        db.diaries.update_one(
            {'_id': d['_id']},
            {'$set': {'date': date_str}}
        )
        print(f"✅ Fixed Diary {d['_id']} -> Set date to {date_str}")
        fixed_count += 1
    else:
        print(f"⚠️ Skipped {d['_id']} (created_at is not datetime: {type(created)})")

print(f"--- 🏁 Repair Complete. Fixed {fixed_count} diaries. ---")
