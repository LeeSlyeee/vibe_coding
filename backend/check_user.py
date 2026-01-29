from pymongo import MongoClient
from config import Config

def check_user():
    client = MongoClient(Config.MONGO_URI)
    db = client.get_database()
    
    user = db.users.find_one({"nickname": "test"})
    if user:
        print(f"✅ Found user 'test': {user.get('_id')}")
        # print(f"Password Hash: {user.get('password')}") # Security risk, but debugging
    else:
        print("❌ User 'test' not found.")

if __name__ == "__main__":
    check_user()
