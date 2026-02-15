
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/mood_diary_db'
client = MongoClient(MONGO_URI)
db = client.get_database()

username = "vibe_user"
user = db.users.find_one({"username": username})

if user:
    print(f"User: {user.get('username')}")
    print(f"Risk Level: {user.get('risk_level')}")
    print(f"Linked Center Code: {user.get('linked_center_code')}")
    print(f"Center Code: {user.get('center_code')}")
else:
    print(f"User {username} not found")
