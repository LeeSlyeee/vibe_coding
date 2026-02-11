from app import app, mongo

with app.app_context():
    # 1. Global Count
    total = mongo.db.diaries.count_documents({})
    print(f"🌍 Global Diary Count (All Users): {total}")
    
    # 2. Slyeee Count
    slyeee = mongo.db.users.find_one({'username': 'slyeee'})
    if slyeee:
        sid = str(slyeee['_id'])
        c1 = mongo.db.diaries.count_documents({'user_id': sid})
        print(f"👤 Slyeee ({sid}) Count: {c1}")
        
    # 3. User_39ca9a Count
    u39 = mongo.db.users.find_one({'username': 'user_39ca9a'})
    if u39:
        uid = str(u39['_id'])
        c2 = mongo.db.diaries.count_documents({'user_id': uid})
        print(f"🤖 User_39ca9a ({uid}) Count: {c2}")
        
    # 4. Old Slyeee ID Count
    old_id = "6969bc2a7bc218506b52ab05" # From backup
    c3 = mongo.db.diaries.count_documents({'user_id': old_id})
    print(f"👻 Old Slyeee ID ({old_id}) Count: {c3}")
