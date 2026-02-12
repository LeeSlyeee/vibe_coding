from app import app, mongo
from bson.objectid import ObjectId
from datetime import datetime, timezone

def fix_wrong_date_entry():
    print("🚀 scanning for misplaced diary (Feb 10 content on Feb 12)...")
    # Target: 2026-02-12 10:30 UTC to 10:50 UTC (19:30-19:50 KST)
    target_time_start = datetime(2026, 2, 12, 10, 30, 0, tzinfo=timezone.utc)
    target_time_end = datetime(2026, 2, 12, 10, 50, 0, tzinfo=timezone.utc)
    
    with app.app_context():
        # Fetch latest 10 diaries by insertion order (_id)
        # Using list() to avoid cursor timeouts if we modify during iteration
        diaries = list(mongo.db.diaries.find().sort("_id", -1).limit(10))
        
        found = False
        for d in diaries:
            doc_id = d['_id']
            gen_time = doc_id.generation_time # aware datetime in UTC
            
            # Check if this document was created in the target window
            if target_time_start < gen_time < target_time_end:
                date_val = d.get('date')
                user_id = d.get('user_id')
                
                print(f"🔍 Found candidate {doc_id} | User: {user_id} | Date: {date_val} | Time: {gen_time}")
                
                # Verify user is slyeee
                u = mongo.db.users.find_one({'_id': ObjectId(user_id)})
                if u and u.get('username') == 'slyeee':
                    print("   ✅ User matched: slyeee")
                    
                    if date_val == '2026-02-12':
                        print("   ⚠️ Incorrect date detected (2026-02-12). Should be 2026-02-10.")
                        print("   🩹 Moving this diary to 2026-02-10...")
                        
                        mongo.db.diaries.update_one(
                            {'_id': doc_id},
                            {'$set': {
                                'date': '2026-02-10', 
                                # Also update created_at to a reasonable time on Feb 10
                                'created_at': datetime(2026, 2, 10, 12, 0, 0) 
                            }}
                        )
                        print("   ✅ Fixed successfully.")
                        found = True
                        # Break? No, check if multiple (autosave might create duplicates)
                    elif date_val == '2026-02-10':
                        print("   ✅ Date is already correct.")
                else:
                    print(f"   ❌ User mismatch: {u.get('username') if u else 'None'}")

        if not found:
            print("❌ No matching entry found in the time window.")

if __name__ == "__main__":
    fix_wrong_date_entry()
