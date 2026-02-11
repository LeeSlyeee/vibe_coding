import json
from datetime import datetime


backup_file = '/home/ubuntu/mood_diary_backup.json'

try:
    with open(backup_file, 'r') as f:
        data = json.load(f)
        
    print("Backup Loaded.")
    
    # 1. Find User
    users = data.get('users', [])
    old_id = None
    
    for u in users:
        if u.get('username') == 'slyeee':
            # Handle Mongo Extended JSON {$oid: ...}
            uid = u.get('_id')
            if isinstance(uid, dict) and '$oid' in uid:
                old_id = uid['$oid']
            else:
                old_id = str(uid)
            print(f"Found Old Slyeee: {old_id}")
            break
            
    if not old_id:
        print("Slyeee not found in backup.")
        exit()
        
    # 2. Find Diaries for Old ID
    diaries = data.get('diaries', [])
    count = 0
    restore_candidates = []
    
    for d in diaries:
        # Check user_id
        duid = d.get('user_id')
        # d['user_id'] might be string or oid dict or int?
        d_uid_str = ""
        if isinstance(duid, dict) and '$oid' in duid:
            d_uid_str = duid['$oid']
        else:
            d_uid_str = str(duid)
            
        if d_uid_str == old_id:
            restore_candidates.append(d)
            count += 1
            
    print(f"Found {count} diaries for Old Slyeee.")
    
    # 3. Insert into DB (Mapped to NEW ID)
    # We need New ID. Fetch from DB.
    from app import app, mongo
    with app.app_context():
        curr_user = mongo.db.users.find_one({'username': 'slyeee'})
        if not curr_user:
            print("Current Slyeee not found in DB!")
            exit()
            
        new_id = str(curr_user['_id'])
        print(f"Current Slyeee ID: {new_id}")
        
        inserted = 0
        for item in restore_candidates:
            # Prepare Item
            # Date check to avoid duplicates?
            date_str = item.get('date')
            if not date_str and item.get('created_at'):
                 # Try extract from created_at dict or str
                 c_at = item.get('created_at')
                 if isinstance(c_at, dict) and '$date' in c_at:
                     date_str = c_at['$date'][:10]
                 elif isinstance(c_at, str):
                     date_str = c_at[:10]
                     
            if not date_str: continue
            
            # Allow Overwrite? Or Skip if exists?
            # User currently has 0 items (except new one).
            # Check exist
            exists = mongo.db.diaries.find_one({'user_id': new_id, 'date': date_str})
            if not exists:
                # Construct
                # Need to map fields from Backup Schema to Current Schema
                # Backup Schema: likely 'content', 'mood_score'
                # Current Schema: 'event', 'mood_level'
                
                # Assume backup matches 217 schema? 
                # Step 909 showed 'emotion_keywords'.
                # Backup might be from 150 (Different Schema) or 217 (Same Schema).
                # Checking keys in next step.
                
                new_doc = {
                    'user_id': new_id,
                    'date': date_str,
                    'event': item.get('content') or item.get('event') or '',
                    'mood_level': item.get('mood_score') or item.get('mood_level') or item.get('mood', 3),
                    'weather': item.get('weather') or '',
                    'sleep_condition': item.get('sleep_score') or item.get('sleep_condition') or 3,
                    'ai_advice': item.get('ai_comment') or item.get('ai_advice') or '',
                    'emotion': item.get('emotion') or 'Neutral',
                    'created_at': datetime.now() # Reset time
                }
                
                mongo.db.diaries.insert_one(new_doc)
                inserted += 1
                
        print(f"Successfully Restored {inserted} diaries from Backup.")

except Exception as e:
    print(f"Error: {e}")

