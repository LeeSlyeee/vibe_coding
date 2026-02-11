from app import app, mongo

with app.app_context():
    pipeline = [
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    results = list(mongo.db.diaries.aggregate(pipeline))
    
    print("Top 5 Data Owners:")
    for res in results[:5]:
        uid = res['_id']
        count = res['count']
        
        # Resolve Username
        try:
            from bson import ObjectId
            u = mongo.db.users.find_one({'_id': ObjectId(uid)})
            username = u['username'] if u else "Unknown/Deleted"
        except:
            u = mongo.db.users.find_one({'_id': uid}) # Try string
            username = u['username'] if u else "Unknown/Deleted"
            if not u:
                 # Check by string ID
                 u = mongo.db.users.find_one({'_id': str(uid)})
                 username = u['username'] if u else "Unknown/Deleted"

        print(f" - {username} (ID: {uid}): {count} items")
