from app import app, mongo
import datetime

with app.app_context():
    user = mongo.db.users.find_one({'username': 'slyeee'})
    if not user:
        print("User Not Found")
        exit()
        
    uid = str(user['_id'])
    
    # 1. Count Total
    total = mongo.db.diaries.count_documents({'user_id': uid})
    print(f"Total Diaries before cleanup: {total}")
    
    # 2. Delete Junk (Restored Items)
    # Junk items have date < Today?
    # Or specifically created recently?
    # Restoration script set created_at = datetime.now()
    # But new diary also has created_at = datetime.now() (approx)
    
    # Safer: Delete based on DATE field.
    # User's new diary is 2026-02-11.
    # Restored junk is Jan 17 or older.
    
    res = mongo.db.diaries.delete_many({
        'user_id': uid,
        'date': {'$ne': '2026-02-11'}
    })
    
    print(f"Deleted {res.deleted_count} items (Old/Junk).")
    
    # 3. Verify Remaining
    remaining = mongo.db.diaries.find({'user_id': uid})
    print(f"Remaining Diaries:")
    for d in remaining:
        print(f" - {d.get('date')} : {d.get('event')}")
