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
            return f"Error: Diary {diary_id} not found"
            
        # 2. Prepare text for analysis
        content = f"사건: {diary.get('event', '')}\n감정: {diary.get('emotion_desc', '')}\n생각: {diary.get('emotion_meaning', '')}"
        
        # 3. Analyze (Gemini Priority)
        # self.update_state(state='PROGRESS', meta={'process_percent': 30, 'message': 'AI가 감정을 탐색하고 있습니다...', 'eta_seconds': 5})
        
        # Re-initialize AI per task to ensure clean state or use global singleton if preferred
        # Here we use a lightweight init
        ai = EmotionAnalysis() 
        
        prediction, comment = None, None
        if ai.gemini_model:
            print("🚀 [Worker] Using Fast Gemini Analysis...")
            prediction, comment = ai.analyze_diary_with_gemini(content)
            
            # If Gemini fails/limits return None, we RAISE exception to trigger Retry!
            if not prediction:
                raise Exception("Gemini returned None (Rate Limit or Error)")
                
        # Fallback to Local Model if Gemini fails or is not available
        if not prediction: # This condition will be true if Gemini failed or was not available
            print("📦 [Worker] Fallback to Local Model Analysis...")
            result = ai.predict(content) # Assuming predict returns a dict with 'emotion' and 'comment'
            prediction = result.get('emotion')
            comment = result.get('comment', '분석에 실패했습니다.')

        # 3.5. Finished Analysis, Saving result
        # self.update_state(state='PROGRESS', meta={'process_percent': 90, 'message': '분석 완료! 결과 저장 중...', 'eta_seconds': 1})
        
        # 4. Update DB
        if prediction:
            mongo.db.diaries.update_one(
                {'_id': ObjectId(diary_id)},
                {'$set': {
                    'ai_prediction': prediction,
                    'ai_comment': comment,
                    'task_id': None # Clear task ID
                }}
            )
            print(f"✅ [Worker] Analysis Complete for Diary {diary_id}")
            return {'process_percent': 100, 'message': '완료', 'result': 'Success'}
        else:
            raise Exception("AI Analysis Failed (Both Gemini & Local)")

    except Exception as e:
        print(f"💥 [Worker] Error processing diary {diary_id}: {e}")
        # Retrying is handled by decorator
        raise self.retry(exc=e)
