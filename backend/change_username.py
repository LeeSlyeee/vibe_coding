import os
from dotenv import load_dotenv
from pymongo import MongoClient
import sys

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    print("⚠️ MONGO_URI not found in environment variables. Checking default.")
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/mood_diary_db')

def change_username(old_name, new_name):
    print(f"🔌 Connecting to MongoDB...")
    try:
        client = MongoClient(MONGO_URI)
        db = client.get_database() 
        users_col = db.users
        
        # 1. Find Old User
        old_user = users_col.find_one({'username': old_name})
        if not old_user:
            print(f"❌ User '{old_name}' not found.")
            # Case-insensitive suggestion
            old_user_ci = users_col.find_one({'username': {'$regex': f'^{old_name}$', '$options': 'i'}})
            if old_user_ci:
                print(f"   Did you mean '{old_user_ci['username']}'?")
            return

        print(f"✅ Found User '{old_name}' (ID: {old_user['_id']})")
        
        # 2. Check New User Conflict
        existing_new = users_col.find_one({'username': new_name})
        if existing_new:
            print(f"⚠️ Warning: The username '{new_name}' is ALREADY taken by another account (ID: {existing_new['_id']}).")
            print(f"🗑️ FORCE MODING: Automatically deleting existing user document for '{new_name}' to proceed...")
            users_col.delete_one({'_id': existing_new['_id']})

        # 3. Update Username
        result = users_col.update_one(
            {'_id': old_user['_id']},
            {'$set': {'username': new_name}}
        )
        
        if result.modified_count > 0:
            print(f"✨ Successfully changed username from '{old_name}' to '{new_name}'.")
            print("   You can now login with the new username.")
        else:
            print("⚠️ No changes were made (Maybe name was already same?).")
            
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        old_u = sys.argv[1]
        new_u = sys.argv[2]
        change_username(old_u, new_u)
    else:
        print("Usage: python change_username.py <old_username> <new_username>")
        # Interactive mode
        o = input("Enter current username: ")
        n = input("Enter new username: ")
        if o and n:
            change_username(o, n)
