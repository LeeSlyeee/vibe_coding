import sys
import os
from celery_app import celery_app
from ai_brain import EmotionAnalysis
from config import Config
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from crypto_utils import crypto_manager 

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
    Celery Wrapper for AI Analysis
    """
    def update_progress(state, meta):
        self.update_state(state=state, meta=meta)
        
    return analyze_diary_logic(diary_id_str, update_progress_callback=update_progress)

def analyze_diary_logic(diary_id_str, update_progress_callback=None):
    """
    Core AI Analysis Logic (Framework Agnostic)
    """
    print(f"🤖 [Analysis] Processing Diary ID: {diary_id_str}")
    
    if update_progress_callback:
        update_progress_callback('PROGRESS', {'process_percent': 10, 'message': '일기장을 펼치는 중...', 'eta_seconds': 15})
    
    db = get_db()
    
    try:
        diary_id = ObjectId(diary_id_str)
        diary = db.diaries.find_one({'_id': diary_id})
        
        if not diary:
            print(f"❌ [Analysis] Diary {diary_id_str} not found!")
            return "Diary Not Found"
            
        # 2. Prepare text for analysis (Decrypt first)
        event = crypto_manager.decrypt(diary.get('event', ''))
        emotion_desc = crypto_manager.decrypt(diary.get('emotion_desc', ''))
        emotion_meaning = crypto_manager.decrypt(diary.get('emotion_meaning', ''))
        
        content = f"사건: {event}\n감정: {emotion_desc}\n생각: {emotion_meaning}"
        
        # 2.5 Fetch 7-Day History Context
        history_context = ""
        try:
            current_date = diary.get('created_at', datetime.utcnow())
            start_date = current_date - timedelta(days=7)
            
            # Fetch previous diaries (exclude current)
            history_cursor = db.diaries.find({
                'user_id': diary.get('user_id'),
                'created_at': {'$gte': start_date, '$lt': current_date}
            }).sort('created_at', 1)
            
            history_lines = []
            for doc in history_cursor:
                # Simple summary: Date + Mood + Event
                d_date = doc.get('created_at').strftime('%Y-%m-%d')
                d_mood = doc.get('mood_level', 3)
                d_event = crypto_manager.decrypt(doc.get('event', ''))[:30] # Truncate event
                history_lines.append(f"- {d_date} (기분:{d_mood}): {d_event}")
            
            if history_lines:
                history_context = "[지난 7일간의 기록]\n" + "\n".join(history_lines)
                print(f"📜 [Analysis] Found {len(history_lines)} past entries for context.")
                
        except Exception as e:
            print(f"⚠️ [Analysis] Failed to fetch history context: {e}")

        # 3. Analyze (Gemma 2 Local Priority)
        print(f"🦙 [Analysis] Diary {diary_id}: Requesting Gemma 2 Analysis (with Context)...")
        
        # Use local instance to ensure freshness or global if preferred. 
        ai = EmotionAnalysis() 
        
        prediction, comment = ai.analyze_diary_with_local_llm(content, history_context=history_context)
        
        if not prediction:
            print(f"❌ [Analysis] AI Analysis Failed for {diary_id}")
            # Instead of raising Exception immediately, maybe fallback?
             # Fallback to Label/Keyword
            print("⚠️ Switching to Fallback Analysis...")
            res = ai.predict(content) # This includes fallbacks
            prediction = res['emotion']
            comment = res['comment']

        # 4. Update DB (Encrypt results)
        enc_prediction = crypto_manager.encrypt(prediction)
        enc_comment = crypto_manager.encrypt(comment)
        
        db.diaries.update_one(
            {'_id': diary_id},
            {'$set': {
                'ai_prediction': enc_prediction,
                'ai_comment': enc_comment,
                'task_id': None 
            }}
        )
        print(f"✅ [Analysis] Complete for Diary {diary_id}")
        return {'process_percent': 100, 'message': '완료', 'result': 'Success'}
            
    except Exception as e:
        print(f"💥 [Analysis] Error processing diary {diary_id_str}: {e}")
        # Retrying handled by caller if needed
        raise e
