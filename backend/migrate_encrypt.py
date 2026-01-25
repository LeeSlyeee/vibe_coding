from pymongo import MongoClient
from crypto_utils import EncryptionManager
from config import Config
import os
from dotenv import load_dotenv

# Load Env
load_dotenv()

def migrate_to_encrypted():
    print("🔐 Starting Data Encryption Migration...")
    
    # 1. Connect DB
    client = MongoClient(os.environ.get('MONGO_URI') or Config.MONGO_URI)
    db = client.get_database()
    
    # 2. Init Crypto
    crypto = EncryptionManager(os.environ.get('ENCRYPTION_KEY'))
    
    # 3. Fetch All Diaries
    diaries = list(db.diaries.find({}))
    total = len(diaries)
    print(f"📄 Found {total} diaries.")
    
    count = 0
    sensitive_fields = ['event', 'emotion_desc', 'emotion_meaning', 'self_talk', 'ai_prediction', 'ai_comment']
    
    for d in diaries:
        updates = {}
        for field in sensitive_fields:
            val = d.get(field)
            if val and isinstance(val, str):
                # Check if already encrypted (Fernet tokens start with gAAAA...)
                # Simple check: Try decrypting. If success, it's already encrypted.
                is_encrypted = False
                try:
                    res = crypto.decrypt(val)
                    if res != val: # Decryption changed it -> it was encrypted
                         is_encrypted = True
                except:
                    pass
                
                if not is_encrypted:
                    encrypted_val = crypto.encrypt(val)
                    updates[field] = encrypted_val
        
        if updates:
            db.diaries.update_one({'_id': d['_id']}, {'$set': updates})
            count += 1
            if count % 10 == 0:
                print(f"   Processed {count}/{total}...")

    print(f"✅ Migration Complete! Encrypted {count} documents.")

if __name__ == "__main__":
    migrate_to_encrypted()
