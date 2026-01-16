
import sys
import os
import json
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient

# JSON Encoder for MongoDB Types
class MongoEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return {'$oid': str(obj)}
        if isinstance(obj, datetime):
            return {'$date': obj.isoformat()}
        return json.JSONEncoder.default(self, obj)

def mongo_hook(dct):
    if '$oid' in dct:
        return ObjectId(dct['$oid'])
    if '$date' in dct:
        return datetime.fromisoformat(dct['$date'])
    return dct

# Configuration
LOCAL_URI = 'mongodb://localhost:27017/mood_diary_db'
FILENAME = 'mood_diary_backup.json'

def export_data():
    print("📤 Exporting data from Local DB...")
    try:
        client = MongoClient(LOCAL_URI)
        db = client.get_database()
        
        data = {}
        collections = ['users', 'diaries', 'emotion_keywords']
        
        for col_name in collections:
            docs = list(db[col_name].find())
            data[col_name] = docs
            print(f"   - {col_name}: {len(docs)} docs")
            
        with open(FILENAME, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=MongoEncoder, ensure_ascii=False, indent=2)
            
        print(f"✅ Export successful! File saved as: {FILENAME}")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")

def import_data():
    print("📥 Importing data to Local DB (OCI)...")
    if not os.path.exists(FILENAME):
        print(f"❌ Backup file not found: {FILENAME}")
        return

    try:
        # Ask for OCI DB Credentials if running on server
        # Or assume localhost with auth if configured, but let's try standard localhost first
        # If OCI uses auth, we might need URI input.
        # Let's assume the user configures the URI or we use the one from config.
        
        # Try finding .env or Config? 
        # For simplicity, let's use the standard URI structure for OCI local connection
        # If user runs this ON the server, localhost:27017 is correct.
        # But if auth is enabled, we need user/pass.
        
        uri = input("Enter MongoDB URI (Press Enter for localhost:27017): ").strip()
        if not uri:
            uri = "mongodb://localhost:27017/mood_diary_db"
            
        client = MongoClient(uri)
        db = client.get_database()
        
        print(f"   Connected to: {db.name}")
        
        with open(FILENAME, 'r', encoding='utf-8') as f:
            data = json.load(f, object_hook=mongo_hook)
            
        for col_name, docs in data.items():
            if not docs:
                continue
                
            col = db[col_name]
            # Replace existing docs based on _id to prevent duplicates
            count = 0
            for doc in docs:
                col.replace_one({'_id': doc['_id']}, doc, upsert=True)
                count += 1
            print(f"   - {col_name}: {count} docs imported.")
            
        print("✅ Import successful!")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python db_transfer.py [export|import]")
        sys.exit(1)
        
    mode = sys.argv[1]
    if mode == 'export':
        export_data()
    elif mode == 'import':
        import_data()
    else:
        print("Invalid mode. Use 'export' or 'import'")
