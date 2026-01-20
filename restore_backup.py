import json
from pymongo import MongoClient
from datetime import datetime
import sys

def restore():
    try:
        # Load JSON
        print("Reading backup file (this may take a moment)...")
        with open('mood_diary_backup.json', 'r') as f:
            data = json.load(f)
            
        client = MongoClient('mongodb://localhost:27017/')
        db = client['mood_diary_db']
        
        # Collections to restore
        collections = data.keys()
        
        for col_name in collections:
            docs = data[col_name]
            if not docs:
                continue
                
            print(f"Restoring {col_name} ({len(docs)} documents)...")
            
            # Handle ObjectIds and Dates if they are in $oid format (common in mongo export)
            # The head output showed "$oid". PyMongo won't automatically convert unless we use bson.json_util
            # But simpler is to direct insert if they are compatible, or let's use json_util
            
            # Actually, standard json.load makes "$oid" a nested dict. 
            # We need to convert these to proper BSON types before inserting.
            from bson import ObjectId
            from bson.json_util import loads, dumps
            
            # Better approach: Use bson.json_util.loads on the string content if possible, 
            # but since we already loaded it as dict, we have to traverse.
            # OR, just re-read using json_util.loads
            
        # Re-reading with json_util
        print("Re-parsing with BSON support...")
        from bson import json_util
        with open('mood_diary_backup.json', 'r') as f:
            bson_data = json_util.loads(f.read())
            
        for col_name, docs in bson_data.items():
            if not docs: continue
            print(f"Inserting into {col_name}...")
            # Drop existing to avoid dupes? Or just insert?
            # Let's drop for clean restore since checking users showed 0.
            db[col_name].drop()
            if docs:
                db[col_name].insert_many(docs)
                print(f"✅ Restored {len(docs)} docs to {col_name}")
                
        print("Restore Complete!")
        
    except Exception as e:
        print(f"Restore Failed: {e}")

if __name__ == "__main__":
    restore()
