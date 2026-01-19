import sys
import os
from celery_app import celery_app
from ai_brain import EmotionAnalysis
from config import Config
from pymongo import MongoClient
from bson.objectid import ObjectId

# Initialize AI Brain ONLY in the worker process
ai_analyzer = None

if os.environ.get('MOOD_ROLE') == 'celery':
    print("🔧 Initializing AI Brain in Worker Process...")
    try:
        ai_analyzer = EmotionAnalysis()
        print("✅ AI Brain Ready in Worker!")
    except Exception as e:
        print(f"❌ Failed to load AI Brain: {e}")
else:
    print("🚀 Flask Process imported tasks.py (Skipping Heavy AI Loading)")

def get_db():
    client = MongoClient(Config.MONGO_URI)
    return client.get_database()

@celery_app.task(bind=True)
def process_diary_ai(self, diary_id_str):
    """
    Background task to perform AI analysis on a diary entry.
    Updated to use Local Gemma 2 (Ollama).
    """
    print(f"🤖 [Worker] Processing Diary ID: {diary_id_str}")
    
    # 1. Fetch the diary from DB
    self.update_state(state='PROGRESS', meta={'process_percent': 10, 'message': '일기장을 펼치는 중...', 'eta_seconds': 15})
    
    db = get_db()
    
    try:
        diary_id = ObjectId(diary_id_str)
        diary = db.diaries.find_one({'_id': diary_id})
        
        if not diary:
            print(f"❌ [Worker] Diary {diary_id_str} not found!")
            return "Diary Not Found"
            
        # 2. Prepare text for analysis
        content = f"사건: {diary.get('event', '')}\n감정: {diary.get('emotion_desc', '')}\n생각: {diary.get('emotion_meaning', '')}"
        
        # 3. Analyze (Gemma 2 Local Priority)
        print(f"🦙 [Worker] Diary {diary_id}: Requesting Gemma 2 Analysis...")
        
        # Use local instance to ensure freshness or global if preferred. 
        ai = EmotionAnalysis() 
        
        prediction, comment = ai.analyze_diary_with_local_llm(content)
        
        if not prediction:
            print(f"❌ [Worker] AI Analysis Failed for {diary_id}")
            raise Exception("Gemma 2 Analysis Failed")

        # 4. Update DB
        db.diaries.update_one(
            {'_id': diary_id},
            {'$set': {
                'ai_prediction': prediction,
                'ai_comment': comment,
                'task_id': None 
            }}
        )
        print(f"✅ [Worker] Analysis Complete for Diary {diary_id}")
        return {'process_percent': 100, 'message': '완료', 'result': 'Success'}
            
    except Exception as e:
        print(f"💥 [Worker] Error processing diary {diary_id_str}: {e}")
        # Retrying is handled by decorator
        raise self.retry(exc=e)
