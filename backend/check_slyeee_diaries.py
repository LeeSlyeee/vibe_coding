from flask import Flask
from flask_pymongo import PyMongo
from config import Config
from bson.objectid import ObjectId
from datetime import datetime, timedelta

app = Flask(__name__)
app.config.from_object(Config)
# [Fix] Use 'app' context explicitly
mongo = PyMongo(app)

def check_diaries():
    with app.app_context():
        # 1. User Check
        user = mongo.db.users.find_one({'username': 'slyeee'})
        if not user:
            print("❌ User 'slyeee' not found!")
            return
        
        user_id = str(user['_id'])
        print(f"👤 Found User 'slyeee' (_id: {user_id})")

        # 2. Check Recent Diaries (This Month)
        one_month_ago = datetime.now() - timedelta(days=30)
        recent_diaries = list(mongo.db.diaries.find({
            'user_id': user_id,
            'created_at': {'$gte': one_month_ago}
        }).sort('created_at', -1))
        
        print(f"\n📅 Diaries within last 30 days ({len(recent_diaries)} found):")
        
        if not recent_diaries:
            print("⚠️ No recent diaries found. SYNC FAILED or NO DATA.")
            # Check total count
            total = mongo.db.diaries.count_documents({'user_id': user_id})
            print(f"   (Total Diaries: {total})")
            
            # Check most recent one
            latest = mongo.db.diaries.find_one({'user_id': user_id}, sort=[('created_at', -1)])
            if latest:
                print(f"   Last entry was on: {latest.get('created_at')}")
        else:
            for d in recent_diaries:
                print(f" - {d.get('date')} (created: {d.get('created_at')}) | Mood: {d.get('mood_level')}")

if __name__ == "__main__":
    check_diaries()
