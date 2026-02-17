from pymongo import MongoClient
import os

def find_missing_user():
    # Check MongoDB (The abandoned one)
    MONGO_URI = "mongodb://localhost:27017/mood_diary_db"
    try:
        client = MongoClient(MONGO_URI)
        db = client.get_database()
        
        target = "tig1179"
        print(f"Searching for '{target}' in MongoDB...")
        
        user = db.users.find_one({'$or': [{'username': target}, {'nickname': target}]})
        
        if user:
            print(f"✅ FOUND in MongoDB!")
            print(f"ID: {user.get('_id')}")
            print(f"Username: {user.get('username')}")
            print(f"Nickname: {user.get('nickname')}")
            print(f"Role: {user.get('role')}")
            
            # Count Diaries
            d_count = db.diaries.count_documents({'user_id': str(user.get('_id'))})
            print(f"Diary Count: {d_count}")
        else:
            print("❌ NOT FOUND in MongoDB either.")
            
    except Exception as e:
        print(f"Error checking MongoDB: {e}")

if __name__ == "__main__":
    find_missing_user()
