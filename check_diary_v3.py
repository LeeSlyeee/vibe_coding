
from pymongo import MongoClient
import sys
from datetime import datetime, timedelta

try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client['mood_diary_db'] # Correct DB Name
    
    print(f"Connected to {db.name}")
    
    # 1. Total Count
    count = db.diaries.count_documents({})
    print(f"Total Diaries: {count}")
    
    # 2. Search for Jan 19 (UTC logic might shift it, so checking Date String if possible or wide range)
    # Checking specific string '2026-01-19' if 'date' field exists and is string
    
    target_date_str = "2026-01-19"
    diary_by_str = db.diaries.find_one({"date": target_date_str})
    
    if diary_by_str:
        print(f"Found by string '2026-01-19': {diary_by_str['_id']}")
        print(f"AI_Pred: {diary_by_str.get('ai_prediction')}")
        print(f"AI_Comment: {diary_by_str.get('ai_comment')}")
        print(f"TaskID: {diary_by_str.get('task_id')}")
    else:
        print(f"No diary with date='{target_date_str}'")
        
        # Fallback: Date Range on created_at
        start = datetime(2026, 1, 18)
        end = datetime(2026, 1, 21)
        cursor = db.diaries.find({"created_at": {"$gte": start, "$lt": end}})
        print("Checking created_at range (Jan 18-21)...")
        for d in cursor:
             print(f" - Found {d.get('date')} (ID: {d['_id']})")
             print(f"   AI: {d.get('ai_prediction')}")
        
except Exception as e:
    print(f"ERROR: {e}")
