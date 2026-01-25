
import os
import sys
from pymongo import MongoClient

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import Config

def migrate(target_uri):
    print("🚀 Starting Migration from Local to OCI MongoDB...")
    
    # 1. Connect to Local (Source)
    local_uri = Config.MONGO_URI
    try:
        source_client = MongoClient(local_uri)
        source_db = source_client.get_database()
        print(f"✅ Connected to Source: {local_uri} (DB: {source_db.name})")
    except Exception as e:
        print(f"❌ Source Connection Failed: {e}")
        return

    # 2. Connect to Remote (Target)
    try:
        target_client = MongoClient(target_uri)
        target_db = target_client.get_database() # Uses DB name from URI
        print(f"✅ Connected to Target: {target_uri.split('@')[-1]} (DB: {target_db.name})")
    except Exception as e:
        print(f"❌ Target Connection Failed: {e}")
        return

    # 3. Collections to Migrate
    collections = ['users', 'diaries', 'emotion_keywords']
    
    for col_name in collections:
        print(f"\n📦 Migrating collection: {col_name}...")
        
        source_col = source_db[col_name]
        target_col = target_db[col_name]
        
        # Fetch all docs
        docs = list(source_col.find())
        total = len(docs)
        
        if total == 0:
            print("   (Skipping empty collection)")
            continue
            
        print(f"   Found {total} documents.")
        
        # Insert/Upsert
        # We use replace_one with upsert=True to avoid duplicates
        count = 0
        for doc in docs:
            try:
                # _id is preserved
                target_col.replace_one({'_id': doc['_id']}, doc, upsert=True)
                count += 1
                if count % 50 == 0:
                    print(f"   Transferred {count}/{total}...")
            except Exception as e:
                print(f"   ❌ Error doc {doc.get('_id')}: {e}")
                
        print(f"   ✅ Completed {col_name}: {count}/{total} transferred.")

    print("\n🎉 Migration Complete!")
    print("Don't forget to update your .env file in the backend folder:")
    print(f"MONGO_URI='{target_uri}'")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate_to_oci.py <YOUR_OCI_MONGO_URI>")
        print("Example: python migrate_to_oci.py 'mongodb+srv://user:pass@host/db?retryWrites=true&w=majority'")
        sys.exit(1)
        
    target_uri = sys.argv[1]
    migrate(target_uri)
