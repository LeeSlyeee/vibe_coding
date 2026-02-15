
import psycopg2
import pymongo
from config import Config
import os
from dotenv import load_dotenv
from crypto_utils import EncryptionManager

load_dotenv()

# MongoDB
MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/mood_diary_db'
mongo_client = pymongo.MongoClient(MONGO_URI)
mongo_db = mongo_client["mood_diary_db"]
diaries_coll = mongo_db["diaries"]
users_coll = mongo_db["users"]

# PG
DB_NAME = "vibe_db"
DB_USER = "vibe_user"
DB_PASS = "vibe1234"
DB_HOST = "127.0.0.1"

# Crypto
crypto = EncryptionManager(os.environ.get('ENCRYPTION_KEY'))

def sync_ai_comments():
    print("🚀 Syncing AI Comments from Mongo to PG...")
    
    # 1. Map Mongo User ID -> Username
    mongo_user_to_username = {}
    for u in users_coll.find():
        mongo_user_to_username[str(u['_id'])] = u.get('username')
        
    # 2. Connect to PG
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    conn.autocommit = True
    cur = conn.cursor()
    
    # 3. Iterate Mongo Diaries
    count = 0
    updated = 0
    
    mongo_diaries = diaries_coll.find({"ai_comment": {"$exists": True, "$ne": ""}})
    
    for d in mongo_diaries:
        mongo_uid = str(d.get('user_id'))
        username = mongo_user_to_username.get(mongo_uid)
        
        if not username: continue
        
        date = d.get('date')
        if not date: continue
        
        ai_comment = d.get('ai_comment')
        
        # Ensure it is encrypted if not already (Actually migrate_encrypt.py might have encrypted it)
        # But we should make sure.
        # Check if it starts with gAAAA.
        final_comment = ai_comment
        
        # We need to find the specific diary in PG
        # Join with users table to match username
        sql = """
            UPDATE diaries
            SET ai_comment = %s
            FROM users
            WHERE diaries.user_id = users.id 
            AND users.username = %s
            AND diaries.date = %s
        """
        
        cur.execute(sql, (final_comment, username, date))
        if cur.rowcount > 0:
            updated += 1
        count += 1
        
    print(f"✅ Synced {updated} comments (scanned {count})")
    cur.close()
    conn.close()

if __name__ == "__main__":
    sync_ai_comments()
