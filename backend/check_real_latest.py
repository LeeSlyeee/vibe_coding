from app import app, mongo
from bson.objectid import ObjectId

def check_latest_by_id():
    print("🚀 Checking LATEST 5 Diaries by _id (Real Insert Time)...")
    with app.app_context():
        # Sort by _id descending to get true latest inserts
        diaries = list(mongo.db.diaries.find().sort("_id", -1).limit(5))
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
            
            print(f"🔹 User: {uname} ({uid}) | Date: {d.get('date')} | Content: {d.get('event')[:20]}... | ID Time: {d.get('_id').generation_time}")

if __name__ == "__main__":
    check_latest_by_id()
