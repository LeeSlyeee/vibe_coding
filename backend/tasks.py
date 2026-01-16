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
    """
    print(f"🤖 [Worker] Processing Diary ID: {diary_id_str}")
    
    # 1. Fetch the diary from DB (Progress: 10%)
    self.update_state(state='PROGRESS', meta={'process_percent': 10, 'message': '일기장을 펼치는 중...', 'eta_seconds': 15})
    
    db = get_db()
    
    try:
        diary_id = ObjectId(diary_id_str)
        diary = db.diaries.find_one({'_id': diary_id})
        
        if not diary:
            print(f"❌ [Worker] Diary {diary_id_str} not found!")
            return "Diary Not Found"
            
        # 2. Prepare text for analysis (Progress: 20%)
        # Note: In Mongo, keys are accessed like dict
        combined_text = f"사건: {diary.get('event', '')}\n감정: {diary.get('emotion_desc', '')}\n생각: {diary.get('emotion_meaning', '')}"
        
        # 3. Perform AI Analysis (Heavy Task)
        self.update_state(state='PROGRESS', meta={'process_percent': 30, 'message': '감정을 깊이 분석하고 있습니다...', 'eta_seconds': 12})
        
        global ai_analyzer
        if ai_analyzer is None:
             # Just in case worker restarted or lazy loading isn't working
             ai_analyzer = EmotionAnalysis()

        result = ai_analyzer.predict(combined_text)
        
        # 3.5. Finished Analysis, Saving result (Progress: 90%)
        self.update_state(state='PROGRESS', meta={'process_percent': 90, 'message': '분석 완료! 결과 저장 중...', 'eta_seconds': 1})
        
        # 4. Update DB
        db.diaries.update_one(
            {'_id': diary_id},
            {'$set': {
                'ai_prediction': result.get('emotion', '분석 실패'),
                'ai_comment': result.get('comment', '분석에 실패했습니다.')
            }}
        )
        
        print(f"✅ [Worker] Analysis Complete for Diary {diary_id_str}")
        return {'process_percent': 100, 'message': '완료', 'result': 'Success'}
        
    except Exception as e:
        print(f"💥 [Worker] Error processing diary {diary_id_str}: {e}")
        return f"Error: {str(e)}"
