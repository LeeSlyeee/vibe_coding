import sys
import os
from celery_app import celery_app
from ai_brain import EmotionAnalysis
from models import db, Diary
from flask import Flask
from config import Config

# Need minimal Flask app context for DB operations
def create_minimal_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

# Initialize AI Brain ONLY in the worker process
# This prevents Flask/Gunicorn from loading the heavy model when importing tasks.py
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

@celery_app.task(bind=True)
def process_diary_ai(self, diary_id):
    """
    Background task to perform AI analysis on a diary entry.
    """
    print(f"🤖 [Worker] Processing Diary ID: {diary_id}")
    
    app = create_minimal_app()
    
    with app.app_context():
        # 1. Fetch the diary from DB (Progress: 10%)
        self.update_state(state='PROGRESS', meta={'process_percent': 10, 'message': '일기장을 펼치는 중...', 'eta_seconds': 15})
        diary = Diary.query.get(diary_id)
        if not diary:
            print(f"❌ [Worker] Diary {diary_id} not found!")
            return "Diary Not Found"
            
        # 2. Prepare text for analysis (Progress: 20%)
        combined_text = f"사건: {diary.event}\n감정: {diary.emotion_desc}\n생각: {diary.emotion_meaning}"
        
        try:
            # 3. Perform AI Analysis (Heavy Task)
            # update_state can be tricky inside synchronous predict call, so we update BEFORE call.
            self.update_state(state='PROGRESS', meta={'process_percent': 30, 'message': '감정을 깊이 분석하고 있습니다...', 'eta_seconds': 12})
            
            # Since ai_analyzer might take time, we ideally want callbacks inside it, but for now, step-based updates are enough.
            # Emotion Analysis (LSTM) is fast. Comment Gen (Polyglot) is slow.
            
            result = ai_analyzer.predict(combined_text)
            
            # 3.5. Finished Analysis, Saving result (Progress: 90%)
            self.update_state(state='PROGRESS', meta={'process_percent': 90, 'message': '분석 완료! 결과 저장 중...', 'eta_seconds': 1})
            
            # 4. Update DB
            diary.ai_prediction = result.get('emotion', '분석 실패')
            diary.ai_comment = result.get('comment', '분석에 실패했습니다.')
            
            db.session.commit()
            print(f"✅ [Worker] Analysis Complete for Diary {diary_id}")
            return {'process_percent': 100, 'message': '완료', 'result': 'Success'}
            
        except Exception as e:
            print(f"💥 [Worker] Error processing diary {diary_id}: {e}")
            db.session.rollback()
            return f"Error: {str(e)}"
