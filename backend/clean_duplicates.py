from app import app, mongo
from bson import ObjectId

with app.app_context():
    # 1. Get User
    user = mongo.db.users.find_one({'username': 'slyeee'})
    if not user:
        print("User slyeee not found")
        exit()
        
    print(f"Cleaning diaries for {user['username']} ({user['_id']})...")
    
    # 2. Get All Diaries (String ID)
    diaries = list(mongo.db.diaries.find({'user_id': str(user['_id'])}))
    print(f"Total entries found: {len(diaries)}")
    
    # 3. Group by Date
    by_date = {}
    for d in diaries:
        date_str = d.get('date')
        if not date_str:
            date_str = "MISSING_DATE"
            
        if date_str not in by_date:
            by_date[date_str] = []
        by_date[date_str].append(d)
        
    # 4. Cleanup
    deleted_count = 0
    for date_str, items in by_date.items():
        if len(items) > 1:
            # Sort: Keep entry with MOST fields, then Latest ID (Newest import)
            def score(doc):
                s = 0
                if doc.get('event'): s += 10
                if doc.get('ai_advice'): s += 5
                if doc.get('created_at'): s += 1
                return s
            
            # Sort descending
            items.sort(key=lambda x: (score(x), x['_id']), reverse=True)
            
            keep = items[0]
            remove = items[1:]
            
            print(f"⚠️ Date {date_str}: Found {len(items)} entries. Keeping {keep['_id']} (Score {score(keep)}). Deleting {len(remove)}.")
            
            for r in remove:
                mongo.db.diaries.delete_one({'_id': r['_id']})
                deleted_count += 1
                
    print(f"♻️ Cleanup Complete. Deleted {deleted_count} duplicates.")
    
    final_count = mongo.db.diaries.count_documents({'user_id': str(user['_id'])})
    print(f"📊 Final Count: {final_count}")
