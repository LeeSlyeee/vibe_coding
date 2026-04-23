import sys
import os
from celery_app import celery_app
from ai_brain import EmotionAnalysis
from config import Config, get_korea_time
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

        # [NEW] Fetch User Risk Level
        user_risk_level = 1
        try:
            user = db.users.find_one({'_id': diary.get('user_id')})
            if user:
                user_risk_level = user.get('risk_level', 1)
            print(f"📊 [Analysis] User Context: Risk Level {user_risk_level}")
        except Exception as e:
            print(f"⚠️ Failed to fetch user risk level: {e}")
            
        # 2. Prepare text for analysis (Decrypt first)
        event = crypto_manager.decrypt(diary.get('event', ''))
        sleep_condition = crypto_manager.decrypt(diary.get('sleep_condition', ''))
        emotion_desc = crypto_manager.decrypt(diary.get('emotion_desc', ''))
        emotion_meaning = crypto_manager.decrypt(diary.get('emotion_meaning', ''))
        
        content = f"수면 상태: {sleep_condition}\n사건: {event}\n감정: {emotion_desc}\n생각: {emotion_meaning}"
        
        # 2.5 Fetch 7-Day History Context
        history_context = ""
        try:
            current_date = diary.get('created_at', get_korea_time())
            start_date = current_date - timedelta(days=7)
            
            # Fetch previous diaries (exclude current)
            history_cursor = db.diaries.find({
                'user_id': diary.get('user_id'),
                'created_at': {'$gte': start_date, '$lt': current_date}
            }).sort('created_at', 1)

            # [Analysis Logic] Calculate Persistence of Negative Mood
            negative_count = 0
            total_history = 0
            
            history_lines = []
            for doc in history_cursor:
                # Simple summary: Date + Mood + Event
                d_date = doc.get('created_at').strftime('%Y-%m-%d')
                d_mood = doc.get('mood_level', 3)
                d_event = crypto_manager.decrypt(doc.get('event', ''))[:30] # Truncate event
                
                # Check negative mood (1=Angry, 2=Sad)
                if d_mood <= 2:
                    negative_count += 1
                total_history += 1
                    
                history_lines.append(f"- {d_date} (기분:{d_mood}/5): {d_event}")
            
            # Generate Insight Metadata
            persistence_note = ""
            if total_history >= 3 and (negative_count / total_history) >= 0.6:
                persistence_note = f"\n[경고: 최근 {total_history}일 중 {negative_count}일간 부정적 감정이 지속되고 있음. 주의 깊은 관찰 필요.]"
            
            if history_lines:
                history_context = "[지난 7일간의 기록]" + persistence_note + "\n" + "\n".join(history_lines)
                print(f"📜 [Analysis] Found {len(history_lines)} past entries. Negative Ratio: {negative_count}/{total_history}")

                
        except Exception as e:
            print(f"⚠️ [Analysis] Failed to fetch history context: {e}")

        # 3. Analyze (Gemma 4 Local Priority)
        print(f"🦙 [Analysis] Diary {diary_id}: Requesting Gemma 4 Analysis (Level {user_risk_level})...")
        
        # Use local instance to ensure freshness or global if preferred. 
        ai = EmotionAnalysis() 
        
        prediction, comment, need_followup, question = ai.analyze_diary_with_local_llm(content, history_context=history_context, user_risk_level=user_risk_level)
        
        if not prediction:
            print(f"❌ [Analysis] AI Analysis Failed for {diary_id}")
            # Instead of raising Exception immediately, maybe fallback?
             # Fallback to Label/Keyword
            print("⚠️ Switching to Fallback Analysis...")
            res = ai.predict(content) # This includes fallbacks
            prediction = res['emotion']
            comment = res['comment']
            need_followup = False
            question = ""

        # 4. Update DB (Encrypt results)
        enc_prediction = crypto_manager.encrypt(prediction)
        enc_comment = crypto_manager.encrypt(comment)
        enc_question = crypto_manager.encrypt(question)
        
        db.diaries.update_one(
            {'_id': diary_id},
            {'$set': {
                'ai_prediction': enc_prediction,
                'ai_comment': enc_comment,
                'followup_required': need_followup,
                'followup_question': enc_question,
                'task_id': None 
            }}
        )
        print(f"✅ [Analysis] Complete for Diary {diary_id}")
        return {'process_percent': 100, 'message': '완료', 'result': 'Success'}
            
    except Exception as e:
        print(f"💥 [Analysis] Error processing diary {diary_id_str}: {e}")
        # Retrying handled by caller if needed
        raise e
