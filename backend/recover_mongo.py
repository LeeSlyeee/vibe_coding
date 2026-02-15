
from pymongo import MongoClient
from config import Config
from datetime import datetime

def recover_feb10_from_mongo():
    try:
        client = MongoClient(Config.MONGO_URI)
        db = client.get_database()
        
        # 1. Find slyeee user
        user = db.users.find_one({'username': 'slyeee'})
        if not user:
            print("User slyeee not found in Mongo")
            return

        print(f"User ID (Mongo): {user['_id']}")
        
        # 2. Find Diary
        # Mongo stores date as datetime usually, let's check range for 2026-02-10
        start = datetime(2026, 2, 10)
        end = datetime(2026, 2, 11)
        
        diary = db.diaries.find_one({
            'user_id': user['_id'],
            'created_at': {'$gte': start, '$lt': end}
        })
        
        if diary:
            print(f"Found Diary ID: {diary['_id']}")
            print(f"Event: {diary.get('event')}")
            print(f"Emotion Desc: {diary.get('emotion_desc')}")
            print(f"Emotion Meaning: {diary.get('emotion_meaning')}")
            print(f"Self Talk: {diary.get('self_talk')}")
        else:
            print("No diary found in Mongo for 2026-02-10")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    recover_feb10_from_mongo()
