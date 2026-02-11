from app import app, mongo

with app.app_context():
    # 1. Identify the Valid Diary
    # It belongs to user_39ca9a
    u39 = mongo.db.users.find_one({'username': 'user_39ca9a'})
    if not u39:
        print("CRITICAL: User user_39ca9a NOT FOUND. Aborting.")
        exit()
        
    valid_diary = mongo.db.diaries.find_one({'user_id': str(u39['_id'])})
    if not valid_diary:
        print("CRITICAL: Valid Diary NOT FOUND. Aborting to prevent full wipe.")
        exit()
        
    valid_id = valid_diary['_id']
    print(f"🔒 Preserving Diary ID: {valid_id} (Date: {valid_diary.get('date')})")
    
    # 2. Delete All Others
    res = mongo.db.diaries.delete_many({'_id': {'$ne': valid_id}})
    print(f"🔥 Incinerated {res.deleted_count} junk diaries.")
    
    # 3. Verify
    total = mongo.db.diaries.count_documents({})
    print(f"✨ Total Remaining: {total}")
    
    # 4. Burn Junk Users?
    # Keep slyeee and user_39ca9a
    # sys_users = ['slyeee', 'user_39ca9a', 'admin']
    # res_u = mongo.db.users.delete_many({'username': {'$nin': sys_users}})
    # print(f"🔥 Incinerated {res_u.deleted_count} junk users.")
