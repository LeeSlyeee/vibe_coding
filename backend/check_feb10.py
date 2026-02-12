from app import app, mongo
from bson.objectid import ObjectId

def check_feb10():
    print("🚀 Checking FEB 10 Diaries...")
    with app.app_context():
        # Check specifically for Feb 10
        diaries = list(mongo.db.diaries.find({'date': '2026-02-10'}))
        print(f"🔥 Found {len(diaries)} diaries for 2026-02-10")
        
        for d in diaries:
            uid = d.get('user_id')
            uname = "UNKNOWN"
            if uid:
                try:
                    user = mongo.db.users.find_one({'_id': ObjectId(str(uid))})
                    if user:
                        uname = user.get('username')
                except:
                    pass
            
            print(f"🔹 User: {uname} ({uid}) | Event: {d.get('event')[:20]}... | Created: {d.get('created_at')}")

if __name__ == "__main__":
    check_feb10()
