from app import app, mongo
from datetime import datetime

def delete_unwanted_diaries():
    """
    Deletes all diaries for 'slyeee' except those on Feb 11 and Feb 12, 2026.
    """
    print("🚀 Starting Cleanup for 'slyeee'...")
    
    with app.app_context():
        # 1. Find User
        user = mongo.db.users.find_one({'username': 'slyeee'})
        if not user:
            print("❌ User 'slyeee' not found!")
            return
            
        user_id = str(user['_id'])
        print(f"👤 Found User: slyeee ({user_id})")
        
        # 2. Define Keep Range (Feb 11 & 12, 2026)
        # We need to be careful with time components. 
        # The safest way is to check the 'date' string field if it exists, or 'created_at'.
        # Let's count totals first.
        
        total = mongo.db.diaries.count_documents({'user_id': user_id})
        print(f"📊 Total Diaries before cleanup: {total}")
        
        # 3. Construct Query for Deletion
        # Keep: 2026-02-11 00:00:00 <= date < 2026-02-13 00:00:00
        start_keep = datetime(2026, 2, 11)
        end_keep = datetime(2026, 2, 13)
        
        # Delete query: User is slyeee AND (date < Feb 11 OR date >= Feb 13)
        # using $or operator
        
        delete_query = {
            'user_id': user_id,
            '$or': [
                {'created_at': {'$lt': start_keep}},
                {'created_at': {'$gte': end_keep}}
            ]
        }
        
        # 4. Execute Delete
        result = mongo.db.diaries.delete_many(delete_query)
        print(f"🗑 Deleted {result.deleted_count} entries.")
        
        remaining = mongo.db.diaries.count_documents({'user_id': user_id})
        print(f"✅ Remaining Diaries: {remaining}")
        
        # 5. Verify Remaining Dates
        cursor = mongo.db.diaries.find({'user_id': user_id})
        print("\n--- Remaining Entries (First 10) ---")
        for d in cursor:
            print(f"📅 {d.get('date')} | {d.get('created_at')} | {d.get('event')[:20] if d.get('event') else 'No Content'}")

if __name__ == "__main__":
    delete_unwanted_diaries()
