from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime
from config import Config

# Connect to DB
client = MongoClient('mongodb://localhost:27017/mood_diary_db')
db = client.get_database()

username = "mild_test"
password = "password123"

# Check if exists
existing = db.users.find_one({"username": username})

if existing:
    print(f"User {username} exists. Updating to MILD risk level...")
    db.users.update_one(
        {"username": username},
        {"$set": {
            "risk_level": 1, 
            "phq9_score": 3,
            "assessment_completed": True
        }}
    )
else:
    print(f"Creating new MILD user {username}...")
    db.users.insert_one({
        "username": username,
        "password_hash": generate_password_hash(password),
        "created_at": datetime.utcnow(),
        "risk_level": 1, # Mild -> Green Mode
        "phq9_score": 3, # Minimal
        "assessment_completed": True
    })

print(f"✅ Created/Updated User: {username}")
print(f"🔑 Password: {password}")
print("🌿 Risk Level: 1 (Green Mode UI Enabled)")
