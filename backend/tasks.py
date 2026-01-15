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
        # 1. Fetch the diary from DB
        diary = Diary.query.get(diary_id)
        if not diary:
            print(f"❌ [Worker] Diary {diary_id} not found!")
            return "Diary Not Found"
            
        # 2. Prepare text for analysis
        combined_text = f"사건: {diary.event}\n감정: {diary.emotion_desc}\n생각: {diary.emotion_meaning}"
        
        try:
            # 3. Perform AI Analysis (Heavy Task)
            # Since ai_analyzer is loaded globally in this worker, it's fast.
            result = ai_analyzer.predict(combined_text)
            
            # 4. Update DB
            diary.ai_prediction = result.get('emotion', '분석 실패')
            diary.ai_comment = result.get('comment', '분석에 실패했습니다.')
            
            db.session.commit()
            print(f"✅ [Worker] Analysis Complete for Diary {diary_id}")
            return "Success"
            
        except Exception as e:
            print(f"💥 [Worker] Error processing diary {diary_id}: {e}")
            db.session.rollback()
            return f"Error: {str(e)}"
