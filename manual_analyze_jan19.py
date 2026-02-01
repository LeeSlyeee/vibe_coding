
from pymongo import MongoClient
from bson.objectid import ObjectId
import sys
import os

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_brain import EmotionAnalysis
from crypto_utils import crypto_manager
from config import Config

# Initialize
client = MongoClient("mongodb://localhost:27017/")
db = client['mood_diary_db']
brain = EmotionAnalysis()

target_ids = [
    '69716983d4e7ae84925e62eb'
    # Add others if needed, but let's just search for Jan 19 range to be dynamic
]

# Or dynamic search for Jan 19
from datetime import datetime
start = datetime(2026, 1, 19)
end = datetime(2026, 1, 20)
cursor = db.diaries.find({"created_at": {"$gte": start, "$lt": end}})

print("--- Starting Manual Analysis for Jan 19 ---")

for doc in cursor:
    diary_id = doc['_id']
    print(f"Processing {diary_id}...")
    
    # 1. Decrypt
    def safe_decrypt(t):
        if not t: return ""
        try: return crypto_manager.decrypt(t)
        except: return ""

    event = safe_decrypt(doc.get('event'))
    emotion_desc = safe_decrypt(doc.get('emotion_desc'))
    self_talk = safe_decrypt(doc.get('self_talk'))
    
    full_text = f"{event} {emotion_desc} {self_talk}".strip()
    
    if not full_text:
        print(" -> Empty text, skipping.")
        continue
        
    print(f" -> Text length: {len(full_text)}")
    
    # 2. Analyze
    result = brain.predict(full_text)
    print(f" -> Result: {result['emotion']}")
    
    # 3. Encrypt & Update
    ai_pred_enc = crypto_manager.encrypt(result['emotion'])
    ai_comment_enc = crypto_manager.encrypt(result['comment'])
    
    db.diaries.update_one(
        {'_id': diary_id},
        {'$set': {
            'ai_prediction': ai_pred_enc,
            'ai_comment': ai_comment_enc,
            'task_id': 'manual_success'
        }}
    )
    print(" -> Updated DB.")

print("--- Done ---")
