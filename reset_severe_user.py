from pymongo import MongoClient
from werkzeug.security import generate_password_hash

client = MongoClient('mongodb://localhost:27017/mood_diary_db')
db = client.get_database()

username = "severe_test"
new_password = "password123"

user = db.users.find_one({"username": username})

if user:
    print(f"User {username} found.")
    print(f"Current Risk Level: {user.get('risk_level')}")
    
    # Reset Password
    db.users.update_one(
        {"username": username},
        {"$set": {
            "password_hash": generate_password_hash(new_password),
            "risk_level": 5 # Ensure Red Mode
        }}
    )
    print(f"✅ Password reset to: {new_password}")
else:
    print(f"❌ User {username} NOT found.")
    # Create if missing
    db.users.insert_one({
        "username": username,
        "password_hash": generate_password_hash(new_password),
        "risk_level": 5,
        "assessment_completed": True
    })
    print(f"✅ Created User: {username} with password: {new_password}")
