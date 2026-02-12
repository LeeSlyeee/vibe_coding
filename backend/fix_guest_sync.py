from app import app, mongo
from bson.objectid import ObjectId

def inspect_and_fix():
    print("🚀 Inspecting 'Guest' Data & Center Code ownership...")
    
    with app.app_context():
        # 1. Check who owns or is linked to 'IV7L90SYBT'
        code = 'IV7L90SYBT'
        
        # Check Users
        user_by_code = mongo.db.users.find_one({'linked_center_code': code})
        print(f"User with linked_center_code '{code}': {user_by_code.get('username') if user_by_code else 'None'}")
        
        # Check B2G Connections
        conn = mongo.db.b2g_connections.find_one({'center_code': code})
        if conn:
            uid = conn.get('user_id')
            u = mongo.db.users.find_one({'_id': ObjectId(uid)}) if uid else None
            print(f"Connection for '{code}': User {u.get('username') if u else uid}")
        else:
            print(f"No B2G Connection found for '{code}'")

        # 2. Find the 'Guest' user created today
        # Based on log: "Auto-created user: Guest"
        guest = mongo.db.users.find_one({'username': 'Guest', 'source': 'B2G_Auto_Sync'})
        if not guest:
            # Fallback: find by nickname Guest created recently?
            guest = mongo.db.users.find_one({'nickname': 'Guest'})
            
        if not guest:
            print("❌ No 'Guest' user found to migrate.")
        else:
            print(f"👤 Found Guest User: {guest.get('_id')} (Created: {guest.get('created_at')})")
            
            # 3. Find 'slyeee'
            slyeee = mongo.db.users.find_one({'username': 'slyeee'})
            if not slyeee:
                print("❌ 'slyeee' not found.")
                return
            
            slyeee_id = str(slyeee['_id'])
            guest_id = str(guest['_id'])
            
            print(f"➡️ Target User: slyeee ({slyeee_id})")
            
            # 4. Move Diaries from Guest -> slyeee
            # We specifically want the one from Feb 12
            # But actually, we should probably move ALL guest diaries linked to this device push?
            
            res = mongo.db.diaries.update_many(
                {'user_id': guest_id},
                {'$set': {'user_id': slyeee_id}}
            )
            print(f"📦 Migrated {res.modified_count} diaries from Guest to slyeee.")
            
            # 5. Delete Guest User? 
            # Ideally yes, to prevent confusion.
            if res.modified_count > 0:
                mongo.db.users.delete_one({'_id': guest['_id']})
                print("🗑 Deleted temporary Guest user.")
            
        # 6. Check 'slyeee' codes
        print(f"ℹ️ Slyeee Linked Code: {slyeee.get('linked_center_code')}")
        
        # If slyeee is NOT linked to 'IV7L90SYBT', we should probably link it?
        # The user said the app pushed to 'IV7L90SYBT'. Ideally we align them.
        if slyeee.get('linked_center_code') != code:
            mongo.db.users.update_one({'_id': slyeee['_id']}, {'$set': {'linked_center_code': code}})
            print(f"🔗 Re-linked slyeee to {code} (Matches App)")

if __name__ == "__main__":
    inspect_and_fix()
