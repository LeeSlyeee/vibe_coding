from app import app, mongo
from bson.objectid import ObjectId

def check_latest():
    print("🚀 Checking LATEST 5 Diaries in System...")
    with app.app_context():
        diaries = list(mongo.db.diaries.find().sort("created_at", -1).limit(5))
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
            
            print(f"🔹 User: {uname} ({uid}) | Date: {d.get('date')} | Created: {d.get('created_at')}")

if __name__ == "__main__":
    check_latest()
