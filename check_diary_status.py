
from pymongo import MongoClient
import sys
from datetime import datetime, timedelta

try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client['mood_diary']
    
    # Target Date: 2026-01-19
    start = datetime(2026, 1, 19)
    end = start + timedelta(days=1)
    
    diary = db.diaries.find_one({
        "created_at": {"$gte": start, "$lt": end}
    })
    
    if not diary:
        print("DIARY_NOT_FOUND")
    else:
        print(f"ID: {diary.get('_id')}")
        print(f"TaskID: {diary.get('task_id')}")
        print(f"AI_Pred: {diary.get('ai_prediction')}")
        print(f"AI_Comment: {diary.get('ai_comment')}")
        
except Exception as e:
    print(f"ERROR: {e}")
