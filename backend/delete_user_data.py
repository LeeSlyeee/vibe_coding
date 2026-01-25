import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson.objectid import ObjectId
import sys

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    # If not in env, try to look for config.py or default local
    print("⚠️ MONGO_URI not found in environment variables. Checking default.")
    # Default to local if not set, or prompt
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/mood_diary_db')

def delete_user(username):
    print(f"🔌 Connecting to MongoDB...")
    try:
        client = MongoClient(MONGO_URI)
        # Check connection
        client.server_info()
        
        # Get DB from URI, or default
        db = client.get_database() 
        print(f"✅ Connected to database: {db.name}")
        
        users_col = db.users
        diaries_col = db.diaries
        reports_col = db.reports 
        
        # 1. Find User
        print("\n🔍 Debug: Current Users in DB:")
        for u in users_col.find():
            print(f" - {u.get('username')} (ID: {u.get('_id')})")
        print("------------------------------------------------")

        user = users_col.find_one({'username': username})
        if not user:
            # Try case-insensitive search
            user_ci = users_col.find_one({'username': {'$regex': f'^{username}$', '$options': 'i'}})
            if user_ci:
                print(f"❌ User '{username}' not found, BUT found '{user_ci['username']}'.")
                confirm_ci = input(f"Did you mean to delete '{user_ci['username']}'? (yes/no): ")
                if confirm_ci.lower() == 'yes':
                    user = user_ci
                    username = user['username'] # Update target username
                else:
                    print("❌ Operation cancelled.")
                    return
            else:
                print(f"❌ User '{username}' not found in database '{db.name}'.")
                return

        user_id_obj = user['_id']
        user_id_str = str(user_id_obj)
        print(f"✅ Found User '{username}' (ID: {user_id_str})")
        print("------------------------------------------------Data Summary")
        
        # Count items to delete
        diary_count = diaries_col.count_documents({'user_id': user_id_str})
        report_count = 0
        if 'reports' in db.list_collection_names():
             report_count = reports_col.count_documents({'user_id': user_id_str})
             
        print(f" - Diaries: {diary_count}")
        print(f" - Reports: {report_count}")
        print("------------------------------------------------")
        
        confirm = input(f"⚠️ Are you sure you want to PERMANENTLY DELETE user '{username}'? (type 'delete' to confirm): ")
        if confirm != 'delete':
            print("❌ Operation cancelled.")
            return
        
        # 2. Delete Diaries
        diary_result = diaries_col.delete_many({'user_id': user_id_str})
        print(f"🗑️ Deleted {diary_result.deleted_count} diaries.")
        
        # 3. Delete Reports (if any)
        if report_count > 0:
            report_result = reports_col.delete_many({'user_id': user_id_str})
            print(f"🗑️ Deleted {report_result.deleted_count} reports.")
        
        # 4. Delete User
        user_result = users_col.delete_one({'_id': user_id_obj})
        
        if user_result.deleted_count > 0:
            print(f"✅ Successfully deleted user '{username}' and all related data.")
        else:
            print(f"⚠️ User document was not deleted (maybe already gone?).")
            
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_username = sys.argv[1]
    else:
        target_username = "Slyeee"
        
    print(f"Target User: {target_username}")
    delete_user(target_username)
