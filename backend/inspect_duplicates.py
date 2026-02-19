
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

from app import app, db, User, Diary
from crypto_utils import EncryptionManager

# Initialize Crypto
crypto = EncryptionManager(app.config.get('ENCRYPTION_KEY'))

def safe_decrypt(text):
    if not crypto: return text
    try:
        return crypto.decrypt(text)
    except:
        return text

def inspect_duplicates():
    with app.app_context():
        user = User.query.filter_by(username='slyeee').first()
        if not user: return

        print(f"👤 Examining User: {user.username} (ID: {user.id})")
        
        # Check Feb 9
        print("\n📅 [Feb 9] Analysis (Total: 53)")
        diaries_9 = Diary.query.filter_by(user_id=user.id, date='2026-02-09').all()
        content_map_9 = {}
        for d in diaries_9:
            content = safe_decrypt(d.event)[:30] # First 30 chars
            if content not in content_map_9: content_map_9[content] = []
            content_map_9[content].append(d.id)
            
        for c, ids in content_map_9.items():
            print(f"- Content: '{c}...' -> Count: {len(ids)} (IDs: {ids[:3]}...)")

        # Check Feb 16
        print("\n📅 [Feb 16] Analysis (Total: 5)")
        diaries_16 = Diary.query.filter_by(user_id=user.id, date='2026-02-16').all()
        content_map_16 = {}
        for d in diaries_16:
            content = safe_decrypt(d.event)[:30]
            if content not in content_map_16: content_map_16[content] = []
            content_map_16[content].append(d.id)
            
        for c, ids in content_map_16.items():
            print(f"- Content: '{c}...' -> Count: {len(ids)} (IDs: {ids})")

if __name__ == "__main__":
    inspect_duplicates()
