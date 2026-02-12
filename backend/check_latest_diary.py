from app import app, mongo
import datetime

with app.app_context():
    user = mongo.db.users.find_one({'username': 'slyeee'})
    if not user:
        print("User slyeee not found")
        exit()
        
    user_id = str(user['_id'])
    print(f"Checking diaries for User ID: {user_id}")
    
    # Check latest entry
    latest = mongo.db.diaries.find_one({'user_id': user_id}, sort=[('created_at', -1)])
    if latest:
        print(f"Latest Diary Date (created_at): {latest.get('created_at')}")
        print(f"Latest Diary ID: {latest.get('_id')}")
        from app import decrypt_doc
        print(f"Latest Diary Content: {decrypt_doc(latest)}")
    else:
        print("No diaries found for slyeee")
        
    # Check if there are any entries in Feb 2026
    start = datetime.datetime(2026, 2, 1)
    end = datetime.datetime(2026, 3, 1)
    count = mongo.db.diaries.count_documents({
        'user_id': user_id,
        'created_at': {'$gte': start, '$lt': end}
    })
    print(f"Entries in Feb 2026: {count}")

    # Check for any entries in 2026
    start_y = datetime.datetime(2026, 1, 1)
    end_y = datetime.datetime(2027, 1, 1)
    count_y = mongo.db.diaries.count_documents({
        'user_id': user_id,
        'created_at': {'$gte': start_y, '$lt': end_y}
    })
    print(f"Entries in 2026: {count_y}")
