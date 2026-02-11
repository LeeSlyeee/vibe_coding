from app import app, mongo
from datetime import datetime

with app.app_context():
    print("🔍 Starting Date Repair...")
    
    # query dict for date: null or date: "" or date missing
    query = {"$or": [{"date": None}, {"date": ""}, {"date": {"$exists": False}}]}
    target_count = mongo.db.diaries.count_documents(query)
    print(f"Found {target_count} diaries with missing date.")
    
    cursor = mongo.db.diaries.find(query)
    fixed_count = 0
    
    for d in cursor:
        created_at = d.get('created_at')
        if not created_at:
            # Maybe 'created' field?
            created_at = d.get('created')
            
        if created_at:
            new_date = None
            if isinstance(created_at, datetime):
                new_date = created_at.strftime('%Y-%m-%d')
            elif isinstance(created_at, str):
                # Try simple slicing 2026-01-01
                if len(created_at) >= 10:
                    new_date = created_at[:10]
            
            if new_date:
                mongo.db.diaries.update_one({'_id': d['_id']}, {'$set': {'date': new_date}})
                print(f"✅ Fixed {d['_id']} -> {new_date}")
                fixed_count += 1
            else:
                print(f"⚠️ Could not parse created_at: {created_at}")
        else:
            print(f"❌ Document {d['_id']} has NO timestamp.")

    print(f"🎉 Repair Complete. Fixed {fixed_count} documents.")
