
import os
import sys
import time
from pymongo import MongoClient
from config import Config
from ai_brain import EmotionAnalysis

# Force Local Mode logic if needed
if 'GEMINI_API_KEY' in os.environ:
    del os.environ['GEMINI_API_KEY']

def batch_process_user(username="test"):
    print(f"🚀 Starting Local AI (Gemma 4) Batch Update for user: {username}")
    
    # 1. Connect DB
    client = MongoClient(Config.MONGO_URI)
    db = client.get_database()
    
    # 2. Find User
    user = db.users.find_one({'username': username})
    if not user:
        print("❌ User not found!")
        return
    
    # 3. Find Diaries
    diaries = list(db.diaries.find({'user_id': str(user['_id'])}))
    total = len(diaries)
    print(f"📦 Found {total} diaries.")
    
    # 4. Initialize AI
    try:
        # Initialize AI (Local Mode)
        ai = EmotionAnalysis()
        print("✅ AI Brain Initialized (Local Mode).")
    except Exception as e:
        print(f"❌ AI Init Error: {e}")
        return

    # 5. Process
    success_count = 0
    
    for i, d in enumerate(diaries):
        diary_id = d['_id']
        content = f"사건: {d.get('event', '')}\n감정: {d.get('emotion_desc', '')}\n생각: {d.get('emotion_meaning', '')}"
        
        print(f"[{i+1}/{total}] Analyzing Diary {diary_id}...", end=" ", flush=True)
        
        # [Resumable Logic] 
        # Skip if already processed by 'batch_update_v5' (or new tag)
        if d.get('task_id') == 'batch_update_v5':
             print("⏭️  Skipping (Already Processed).")
             continue
        
        # No Strict Rate Limit for Local AI, but good to be gentle on CPU
        SAFE_INTERVAL = 0.5 
        
        start_time = time.time()
        try:
            # key point: uses 'analyze_diary_with_local_llm'
            prediction, comment = ai.analyze_diary_with_local_llm(content)
            
            if prediction and comment:
                # Success!
                db.diaries.update_one(
                    {'_id': diary_id},
                    {'$set': {
                        'ai_prediction': prediction,
                        'ai_comment': comment,
                        'task_id': 'batch_update_v5' 
                    }}
                )
                print(f"✅ Done! ({time.time() - start_time:.1f}s)")
                success_count += 1
                time.sleep(SAFE_INTERVAL)
                
            else:
                print(f"⚠️ AI returned None. (Local AI Error or Timeout)")
                time.sleep(1) 

        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(1)
            
    print(f"\n🎉 Batch Update Complete! ({success_count}/{total} updated)")

if __name__ == "__main__":
    target_user = sys.argv[1] if len(sys.argv) > 1 else "test"
    
    # Check Ollama availability before start
    import requests
    try:
        requests.get("http://localhost:11434")
        print("✅ Ollama Server is running.")
    except:
        print("❌ Ollama server is NOT running. Please run 'ollama serve' first.")
        sys.exit(1)

    batch_process_user(target_user)
