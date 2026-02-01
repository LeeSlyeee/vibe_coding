
from pymongo import MongoClient
import sys
from datetime import datetime, timedelta

try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client['mood_diary']
    
    print("--- Searching Diaris ---")
    # Search wider range
    start = datetime(2026, 1, 18)
    end = datetime(2026, 1, 21)
    
    diaries = list(db.diaries.find({
        "created_at": {"$gte": start, "$lt": end}
    }))
    
    print(f"Found {len(diaries)} diaries around Jan 19.")
    
    for d in diaries:
        print(f"Date: {d.get('date')} | Created: {d.get('created_at')}")
        print(f"ID: {d.get('_id')}")
        # Check encrypted/decrypted status roughly
        ai_pred = d.get('ai_prediction')
        print(f"AI_Pred (Raw): {ai_pred}")
        print(f"TaskID: {d.get('task_id')}")
        print("-" * 20)
        
except Exception as e:
    print(f"ERROR: {e}")
