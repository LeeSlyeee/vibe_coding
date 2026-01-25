from pymongo import MongoClient
import os
from config import Config

def check_users():
    try:
        # Use URI from config or default
        uri = Config.MONGO_URI
        print(f"Connecting to: {uri}")
        client = MongoClient(uri)
        db = client.get_database()
        
        users_count = db.users.count_documents({})
        print(f"Total Users: {users_count}")
        
        users = list(db.users.find({}, {'username': 1, '_id': 0}))
        print("Users found:", users)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_users()
