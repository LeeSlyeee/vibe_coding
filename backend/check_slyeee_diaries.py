from app import app, mongo
from datetime import datetime

def check_and_fix():
    print("🚀 Checking Slyeee Diaries...")
    with app.app_context():
        u = mongo.db.users.find_one({'username': 'slyeee'})
        if not u:
            print("❌ User not found")
            return
            
        uid = str(u['_id'])
        diaries = list(mongo.db.diaries.find({'user_id': uid}))
        print(f"✅ Found {len(diaries)} diaries for slyeee ({uid})")
        
        for d in diaries:
            did = d['_id']
            date_val = d.get('date')
            created_at = d.get('created_at')
            
            print(f"🔹 Diary {did} | Date: {date_val} | Created: {created_at}")
            
            if not date_val and created_at:
                # Fix missing date
                new_date = created_at.strftime("%Y-%m-%d")
                mongo.db.diaries.update_one({'_id': did}, {'$set': {'date': new_date}})
                print(f"   🛠 Fixed missing date -> {new_date}")

if __name__ == "__main__":
    check_and_fix()
