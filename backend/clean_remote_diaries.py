from app import app, mongo
from datetime import datetime, timedelta

def clean_diaries_remote():
    """
    Deletes ALL diaries for 'slyeee' that are NOT from Feb 11 or Feb 12, 2026.
    """
    print("🚀 Starting Precise Cleanup for 'slyeee' on THIS Server...")
    
    with app.app_context():
        # 1. Find User
        user = mongo.db.users.find_one({'username': 'slyeee'})
        if not user:
            print("❌ User 'slyeee' not found!")
            return
            
        user_id = str(user['_id'])
        print(f"👤 Found User: slyeee ({user_id})")
        
        # 2. Count before
        total = mongo.db.diaries.count_documents({'user_id': user_id})
        print(f"📊 Total Diaries BEFORE: {total}")
        
        # 3. Define Keep Window (Feb 11 & 12)
        # We will use string matching on 'date' field if available, 
        # AND 'created_at' range as fallback.
        
        keep_dates = ['2026-02-11', '2026-02-12']
        
        # Query: 
        # DELETE WHERE user_id == slyeee AND (date NOT IN keep_dates)
        # Note: If 'date' is missing, we rely on created_at.
        # Let's use a robust approach: Fetch all, check logic in python, retrieve IDs to delete.
        # (Safer than complex mongo query if data is messy)
        
        cursor = mongo.db.diaries.find({'user_id': user_id})
        ids_to_delete = []
        kept_count = 0
        
        print(f"🔍 Scanning {total} entries...")
        for d in cursor:
            # Check 'date' string first (YYYY-MM-DD)
            d_date = d.get('date')
            
            # If no date string, try created_at
            if not d_date and d.get('created_at'):
                try:
                    d_date = d.get('created_at').strftime("%Y-%m-%d")
                except:
                    pass
            
            # Decision
            if d_date in keep_dates:
                kept_count += 1
                # print(f"  ✅ KEEP: {d_date} ({d.get('_id')})")
            else:
                ids_to_delete.append(d.get('_id'))
                # print(f"  ❌ DELETE: {d_date} ({d.get('_id')})")
        
        print(f"📋 Scan Result: Keep {kept_count} | Delete {len(ids_to_delete)}")
        
        if ids_to_delete:
            res = mongo.db.diaries.delete_many({'_id': {'$in': ids_to_delete}})
            print(f"🗑 Deleted {res.deleted_count} entries.")
        else:
            print("✨ No entries to delete.")
            
        # 4. Final Verification
        final_count = mongo.db.diaries.count_documents({'user_id': user_id})
        print(f"✅ Final Count: {final_count}")
        
        if final_count > 0:
            print("📅 Remaining Dates:")
            for d in mongo.db.diaries.find({'user_id': user_id}):
                print(f" - {d.get('date')} : {d.get('event')[:20] if d.get('event') else 'No Content'}")

if __name__ == "__main__":
    clean_diaries_remote()
