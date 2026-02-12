from app import app, mongo
from b2g_routes import pull_from_insight_mind
from bson.objectid import ObjectId

def trigger():
    print("🚀 Triggering Pull from InsightMind (150) for 'slyeee'...")
    
    with app.app_context():
        # 1. Find User
        user = mongo.db.users.find_one({'username': 'slyeee'})
        if not user:
            print("❌ User 'slyeee' not found locally.")
            return
            
        user_id = str(user['_id'])
        print(f"✅ Found User: slyeee ({user_id})")
        
        # 2. Check Link
        center_code = user.get("linked_center_code") or user.get("center_code")
        if not center_code:
            print("⚠️ User is not linked to any center. Pull might fail or be empty.")
            # Verify if we can find a code from backup knowledge? SEOUL-001
            # We could inject it if missing?
            # db.users.update_one({'_id': user['_id']}, {'$set': {'linked_center_code': 'SEOUL-001'}})
        else:
            print(f"🔗 Linked Center Code: {center_code}")

        # 3. Pull
        # run_async=False to see output
        pull_from_insight_mind(user_id, run_async=False)
        
        print("\n✅ Trigger Complete.")

if __name__ == "__main__":
    trigger()
