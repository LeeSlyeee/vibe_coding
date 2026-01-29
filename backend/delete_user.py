from pymongo import MongoClient
from config import Config

def delete_user():
    client = MongoClient(Config.MONGO_URI)
    db = client.get_database()
    
    # Delete 'test' user
    result = db.users.delete_one({"username": "test"})
    
    if result.deleted_count > 0:
        print("✅ User 'test' successfully deleted.")
    else:
        print("⚠️ User 'test' check: User already does not exist.")

if __name__ == "__main__":
    delete_user()
