from app import app, mongo
from b2g_routes import pull_from_insight_mind
from datetime import datetime

def sync_remote():
    """
    This script fixes the missing diaries for 'slyeee' on the 217 server (or local).
    1. Links user 'slyeee' to 'SEOUL-001' center (required for sync).
    2. Ensures nickname is 'slyeee' to match 150 server.
    3. Pulls missing data from InsightMind (150) server.
    """
    print("🚀 Starting Slyeee Diary Recovery...")
    
    with app.app_context():
        # --- Step 1: Link User to Center & Fix Nickname ---
        user = mongo.db.users.find_one({'username': 'slyeee'})
        if not user:
            print("❌ User 'slyeee' not found!")
            return
            
        current_code = user.get("linked_center_code")
        current_nick = user.get("nickname")
        print(f"👤 User: slyeee | Nick: {current_nick} | Center: {current_code}")
        
        updates = {}
        target_code = "SEOUL-001"
        if current_code != target_code:
            updates['linked_center_code'] = target_code
            print(f"➡️ Will Update Link: {target_code}")
            
        if current_nick != 'slyeee':
            updates['nickname'] = 'slyeee'
            print(f"➡️ Will Update Nickname: slyeee")
            
        if updates:
            mongo.db.users.update_one(
                {'_id': user['_id']},
                {'$set': updates}
            )
            print("✅ User Updated Successfully.")
        else:
            print("✅ User Config OK.")
            
        # Ensure Center Exists in DB (Placeholder)
        if not mongo.db.centers.find_one({'code': target_code}):
            mongo.db.centers.insert_one({
                'code': target_code,
                'name': '도봉구 정신건강복지센터 (Sync)',
                'created_at': datetime.now()
            })
            print("✅ Created Placeholder Center: SEOUL-001")
            
        # --- Step 2: Pull from 150 Server ---
        user_id = str(user['_id'])
        print(f"🔄 Pulling Data from InsightMind (150)...")
        
        # Call the B2G Sync Logic
        # run_async=False to block and show logs
        pull_from_insight_mind(user_id, run_async=False)
        
        print("\n🎉 Recovery Complete. Please check the App.")

if __name__ == "__main__":
    sync_remote()
