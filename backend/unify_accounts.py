from app import app, mongo

with app.app_context():
    # 1. Fetch Both Users
    slyeee = mongo.db.users.find_one({'username': 'slyeee'})
    u39 = mongo.db.users.find_one({'username': 'user_39ca9a'})
    
    if not slyeee:
        print("CRITICAL: Slyeee does not exist! Cannot unify.")
        exit()
        
    slyeee_id = str(slyeee['_id'])
    
    if u39:
        u39_id = str(u39['_id'])
        print(f"Found impostor 'user_39ca9a' (ID: {u39_id}).")
        
        # 2. Move Diaries
        res = mongo.db.diaries.update_many(
            {'user_id': u39_id},
            {'$set': {'user_id': slyeee_id}}
        )
        print(f"📦 Moved {res.modified_count} diaries from user_39ca9a -> slyeee.")
        
        # 3. Delete Impostor
        mongo.db.users.delete_one({'_id': u39['_id']})
        print("🔥 Deleted 'user_39ca9a' user object.")
    else:
        print("Impostor 'user_39ca9a' not found (Already clean?).")
        
    # 4. Verify Final State
    total_sly = mongo.db.diaries.count_documents({'user_id': slyeee_id})
    print(f"✅ Final Count for 'slyeee': {total_sly}")
    
    # 5. Check if any orphans remain?
    # Global count
    global_cnt = mongo.db.diaries.count_documents({})
    if global_cnt != total_sly:
        print(f"⚠️ Warning: Global Count ({global_cnt}) != Slyeee Count ({total_sly}).")
        # Purge orphans?
        # User said "Burn Everything Else".
        if global_cnt > total_sly:
             mongo.db.diaries.delete_many({'user_id': {'$ne': slyeee_id}})
             print("🔥 Incinerated remaining orphans.")
    else:
        print("✨ Database is Pure (Only slyeee exists).")
