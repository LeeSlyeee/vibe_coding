from pymongo import MongoClient
from config import Config
from datetime import datetime

def seed_center():
    uri = Config.MONGO_URI
    client = MongoClient(uri)
    db = client.get_database()
    
    # 1. Existing Code (from User Screenshot)
    target_code = "HUYXSPLCNN"
    
    existing = db.centers.find_one({"code": target_code})
    
    if existing:
        print(f"✅ Center '{target_code}' already exists.")
    else:
        db.centers.insert_one({
            "code": target_code,
            "name": "도봉구 보건소 (Test)",
            "region": "도봉구",
            "created_at": datetime.utcnow()
        })
        print(f"🎉 Created Center '{target_code}'")

    # 2. Simple Test Code
    simple_code = "TEST-001"
    if not db.centers.find_one({"code": simple_code}):
        db.centers.insert_one({
            "code": simple_code,
            "name": "테스트 보건소",
            "region": "테스트",
            "created_at": datetime.utcnow()
        })
        print(f"🎉 Created Simple Code '{simple_code}'")

if __name__ == "__main__":
    seed_center()
