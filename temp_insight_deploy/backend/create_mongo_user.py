from pymongo import MongoClient
from datetime import datetime
import os

try:
    client = MongoClient('mongodb://localhost:27017')
    db = client['mood_diary_db'] # Correct DB Name
    
    username = 'slyeee'
    django_id = 21
    
    user = db.users.find_one({'username': username})
    
    if not user:
        # Create New User
        res = db.users.insert_one({
            'username': username,
            'django_id': django_id,
            'nickname': '관리자',
            'created_at': datetime.now(),
            'is_premium': True, # Admin Premium
            'assessment_completed': False # Force assessment? Or True? Let's keep False to test logic.
        })
        print(f"Created Mongo User: {username} (ID: {res.inserted_id})")
    else:
        # Update Existing
        res = db.users.update_one({'username': username}, {'$set': {'django_id': django_id}})
        print(f"Updated Mongo User: {username}, matched={res.matched_count}, modified={res.modified_count}")

except Exception as e:
    print(f"Error: {e}")
