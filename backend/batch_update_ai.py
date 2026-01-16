
import os
import sys
import time
from pymongo import MongoClient
from bson.objectid import ObjectId

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_brain import EmotionAnalysis
from config import Config

def batch_update(limit=None, target_user_id="6969bc2a7bc218506b52ab05"):
    print(f"🚀 [Batch Update] Starting AI analysis for user: {target_user_id}")
    
    # 1. Mongo Connection
    try:
        client = MongoClient(Config.MONGO_URI)
        db = client.get_database()
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ MongoDB Connection Failed: {e}")
        return

    # 2. Initialize AI
    print("🧠 Initializing AI Brain (Loading Polyglot-Ko-1.3B)...")
    os.environ['MOOD_ROLE'] = 'celery'
    ai = EmotionAnalysis()
    
    if hasattr(ai, 'gpt_model') and ai.gpt_model:
        print("✨ PRECISE MODE ACTIVATED (GPU/LLM)")
    else:
        print("⚠️ FALLBACK MODE (Keyword based)")

    # 3. Fetch diaries (focus on pending ones)
    query = {
        "user_id": target_user_id,
        "ai_comment": {"$regex": "^분석 (대기|중|오류).*"}
    }
    
    diaries = list(db.diaries.find(query).sort('created_at', -1))
    if limit:
        diaries = diaries[:limit]
        
    total = len(diaries)
    if total == 0:
        print("✨ No pending diaries found. Everything is already analyzed!")
        return

    print(f"📦 Found {total} pending diaries to process.")

    start_time = time.time()
    count = 0
    
    for doc in diaries:
        combined_text = f"사건: {doc.get('event', '')}\n감정: {doc.get('emotion_desc', '')}\n생각: {doc.get('emotion_meaning', '')}"
        
        try:
            # Predict
            result = ai.predict(combined_text)
            
            # Update DB
            db.diaries.update_one(
                {'_id': doc['_id']},
                {'$set': {
                    'ai_prediction': result.get('emotion', '분석 실패'),
                    'ai_comment': result.get('comment', '분석 중 오류 발생')
                }}
            )
            
            count += 1
            if count % 5 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / count
                eta = (total - count) * avg_time
                print(f"⏳ [{count}/{total}] | Avg: {avg_time:.2f}s | ETA: {int(eta//60)}m {int(eta%60)}s")
                
        except Exception as e:
            print(f"❌ Error at {doc['_id']}: {e}")

    print(f"\n✅ Batch Update Complete! Processed {count} entries.")

if __name__ == "__main__":
    # Process all pending entries
    batch_update()
