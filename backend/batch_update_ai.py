
import os
import sys
import time
import multiprocessing
from pymongo import MongoClient
from bson.objectid import ObjectId

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_brain import EmotionAnalysis
from config import Config

# Global variables for worker processes
worker_ai = None
worker_db = None

def init_worker():
    """Initialize AI and DB connection in each worker process"""
    global worker_ai, worker_db
    
    # Identify as worker
    os.environ['MOOD_ROLE'] = 'celery' 
    
    print(f"🔧 Worker {os.getpid()} initializing...")
    try:
        # Initialize AI (each worker gets its own instance)
        worker_ai = EmotionAnalysis()
        
        # Initialize DB connection
        client = MongoClient(Config.MONGO_URI)
        worker_db = client.get_database()
        print(f"✅ Worker {os.getpid()} ready.")
    except Exception as e:
        print(f"❌ Worker {os.getpid()} failed to init: {e}")

def process_entry(doc):
    """Process a single diary entry"""
    global worker_ai, worker_db
    
    if worker_ai is None or worker_db is None:
        return {'id': str(doc['_id']), 'status': 'error', 'msg': 'Worker not initialized'}

    combined_text = f"사건: {doc.get('event', '')}\n감정: {doc.get('emotion_desc', '')}\n생각: {doc.get('emotion_meaning', '')}"
    
    try:
        # Predict
        result = worker_ai.predict(combined_text)
        
        # Update DB
        worker_db.diaries.update_one(
            {'_id': doc['_id']},
            {'$set': {
                'ai_prediction': result.get('emotion', '분석 실패'),
                'ai_comment': result.get('comment', '분석 중 오류 발생')
            }}
        )
        return {'id': str(doc['_id']), 'status': 'success'}
        
    except Exception as e:
        return {'id': str(doc['_id']), 'status': 'error', 'msg': str(e)}

def batch_update(username="test"):
    print(f"🚀 [Batch Parallel] Starting AI analysis for user: {username}")
    
    start_main = time.time()
    
    # 1. Main Process DB Connection to fetch IDs
    try:
        client = MongoClient(Config.MONGO_URI)
        db = client.get_database()
    except Exception as e:
        print(f"❌ DB Connection Failed: {e}")
        return

    # 2. Find User
    user = db.users.find_one({"username": username})
    if not user:
        print(f"❌ User '{username}' not found.")
        return
        
    target_user_id = str(user['_id'])
    
    # 3. Fetch Diaries
    query = {"user_id": target_user_id}
    diaries = list(db.diaries.find(query).sort('created_at', -1))
    total = len(diaries)
    
    if total == 0:
        print("✨ No diaries found.")
        return

    print(f"📦 Found {total} diaries. Spawning workers...")

    # 4. multiprocessing Pool
    # Use 2-3 processes to avoid OOM (1.3B model is ~3GB RAM per process)
    # Mac M-series usually has unified memory, but still safer to be conservative.
    num_processes = 2 
    
    with multiprocessing.Pool(processes=num_processes, initializer=init_worker) as pool:
        print(f"🔥 Processing with {num_processes} parallel workers...")
        
        results = []
        for i, res in enumerate(pool.imap_unordered(process_entry, diaries)):
            results.append(res)
            
            if (i + 1) % 5 == 0:
                elapsed = time.time() - start_main
                avg = elapsed / (i + 1)
                eta = (total - (i + 1)) * avg
                print(f"⏳ [{i + 1}/{total}] Processed | Avg: {avg:.2f}s/item (Parallel) | ETA: {int(eta)}s")

    total_time = time.time() - start_main
    print(f"\n✅ Batch Update Complete! Processed {total} entries in {total_time:.1f} seconds.")

if __name__ == "__main__":
    # Required for macOS/Windows
    multiprocessing.set_start_method('spawn', force=True)
    batch_update("test")
