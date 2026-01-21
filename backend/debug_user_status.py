import os
from pymongo import MongoClient
import sys
from dotenv import load_dotenv

# Load env
load_dotenv()
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/mood_diary_db')

def check_status(username="slyeee"):
    print(f"🔌 Connecting to MongoDB...")
    try:
        client = MongoClient(MONGO_URI)
        db = client.get_database()
        
        print(f"\n📊 [Diagnosis Report] Target: {username}")
        
        # 1. Target User Check
        target_user = db.users.find_one({'username': username})
        
        if target_user:
            uid = str(target_user['_id'])
            d_count = db.diaries.count_documents({'user_id': uid})
            print(f"✅ User Found: '{username}'")
            print(f"   - User ID: {uid}")
            print(f"   - Diaries linked to this ID: {d_count}")
        else:
            print(f"❌ User '{username}' NOT found.")
            # Alias check
            regex_user = db.users.find_one({'username': {'$regex': f'^{username}$', '$options': 'i'}})
            if regex_user:
                print(f"   (But found '{regex_user['username']}' via case-insensitive search)")

        # 2. Global User List
        print("\n📋 [Current User List & Data Count]")
        print(f"{'Username':<20} | {'User ID':<26} | {'Diaries'}")
        print("-" * 60)
        
        all_users = db.users.find()
        for u in all_users:
            uid = str(u['_id'])
            count = db.diaries.count_documents({'user_id': uid})
            print(f"{u['username']:<20} | {uid:<26} | {count}")
            
        print("-" * 60)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "slyeee"
    check_status(target)
