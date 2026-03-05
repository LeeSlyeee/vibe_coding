
from celery import Celery
from config import Config

def make_celery(app_name=__name__):
    celery = Celery(
        app_name,
        broker=Config.CELERY_BROKER_URL,
        backend=Config.CELERY_RESULT_BACKEND
    )
    celery.conf.update(
        result_expires=3600,
    )
    return celery

celery_app = make_celery()

@celery_app.task(bind=True)
def run_ai_analysis_task(self, diary_id, full_text):
    """
    Celery Task for Async Analysis
    """
    import os
    import sys
    
    # Manually ensure path context
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from ai_brain import EmotionAnalysis
    from crypto_utils import crypto_manager
    from pymongo import MongoClient
    from bson.objectid import ObjectId
    from config import Config

    print(f"🥦 [Celery] Processing Task {self.request.id} for Diary {diary_id}")

    try:
        # Re-init Dependencies inside Worker
        client = MongoClient(Config.MONGO_URI)
        db = client.get_database()
        
        # Load AI (Worker needs its own model instance)
        brain = EmotionAnalysis()
        
        print(f"🥦 [Celery] AI Model Loaded. Starting Prediction...")
        
        # 1. Analyze
        # Use simple text predict for now (Risk level support TBD or fetch fromUser)
        # Fetch user risk level? For now default 1
        result = brain.predict(full_text)
        
        # 2. Encrypt
        enc_emotion = crypto_manager.encrypt(result['emotion'])
        enc_comment = crypto_manager.encrypt(result['comment'])
        
        # 3. Update DB
        db.diaries.update_one(
            {'_id': ObjectId(diary_id)},
            {'$set': {
                'ai_prediction': enc_emotion,
                'ai_comment': enc_comment,
                'task_id': f"celery-{self.request.id}",
                'thread_status': 'completed'
            }}
        )
        print(f"🥦 [Celery] DB Updated for {diary_id}!")
        return {'status': 'success', 'emotion': result['emotion']}

    except Exception as e:
        print(f"🥦 [Celery] Error: {e}")
        # Mark error in DB
        try:
             client = MongoClient(Config.MONGO_URI)
             db = client.get_database()
             db.diaries.update_one(
                {'_id': ObjectId(diary_id)},
                {'$set': {
                    'ai_prediction': crypto_manager.encrypt("분석 실패"),
                    'ai_comment': crypto_manager.encrypt("잠시 후 다시 시도해주세요."),
                    'task_id': f"celery-failed-{self.request.id}"
                }}
            )
        except: pass
        return {'status': 'failed', 'error': str(e)}

@celery_app.task(bind=True)
def generate_weekly_letters_batch(self):
    """
    Celery Task for batch generating weekly letters for all users.
    This can be scheduled to run every Sunday night.
    """
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from kick_analysis.weekly_letter import process_all_users_weekly_letter
    
    print(f"💌 [Celery] Starting Weekly Letter Batch Processing (Task ID: {self.request.id})")
    try:
        results = process_all_users_weekly_letter()
        print(f"💌 [Celery] Weekly Letter Batch Finished. Results: {results}")
        return {'status': 'success', 'results': results}
    except Exception as e:
        print(f"💌 [Celery] Error in Weekly Letter Batch: {e}")
        return {'status': 'failed', 'error': str(e)}
