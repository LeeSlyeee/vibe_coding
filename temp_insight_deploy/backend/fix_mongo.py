from pymongo import MongoClient
import os

try:
    client = MongoClient('mongodb://localhost:27017')
    # Check DB List
    dbs = client.list_database_names()
    print(f"Databases: {dbs}")
    
    db_name = 'maumdata'
    if 'maumdata' not in dbs and 'test' in dbs:
        db_name = 'test' # Fallback
    
    db = client[db_name]
    
    # 1. Update slyeee (ID: 21)
    res = db.users.update_one({'username': 'slyeee'}, {'$set': {'django_id': 21}})
    print(f"Update 'slyeee' Result: matched={res.matched_count}, modified={res.modified_count}")

    # 2. Update tig1179 (ID: ? - Find from Django)
    # Just update slyeee for now.

except Exception as e:
    print(f"Error: {e}")
