
import os
import sys
import time
from pymongo import MongoClient
from config import Config
from ai_brain import EmotionAnalysis

# Force Gemini Mode
os.environ['GEMINI_API_KEY'] = Config.GEMINI_API_KEY

def batch_process_user(username="test"):
    print(f"🚀 Starting Gemini Batch Update for user: {username}")
    
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
        ai = EmotionAnalysis()
        if not ai.gemini_model:
            print("❌ Gemini AI failed to load. Check API Key.")
            return
    except Exception as e:
        print(f"❌ AI Init Error: {e}")
        return

    # 5. Process
    success_count = 0
    
    for i, d in enumerate(diaries):
        diary_id = d['_id']
        content = f"사건: {d.get('event', '')}\n감정: {d.get('emotion_desc', '')}\n생각: {d.get('emotion_meaning', '')}"
        
        print(f"[{i+1}/{total}] Analyzing Diary {diary_id}...", end=" ", flush=True)
        
        # [Resumable Logic] Skip ONLY if processed by THIS batch script (v4)
        if d.get('task_id') == 'batch_update_v4':
             print("⏭️  Skipping (Already Processed by Gemma2).")
             continue
        
        # Strict Rate Limit Enforcement (Gemini Free Tier: 15 RPM)
        # We aim for ~10 RPM to be safe -> 1 request every 6 seconds.
        SAFE_INTERVAL = 0.1 # No rate limits for local AI! 
        
        while True:
            start_time = time.time()
            try:
                # Use the new ultra-fast method
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
                    print(f"✅ Diary {i+1} Done!")
                    success_count += 1
                    
                    # Smart Sleep: Ensure we wait at least SAFE_INTERVAL seconds
                    elapsed = time.time() - start_time
                    if elapsed < SAFE_INTERVAL:
                        time.sleep(SAFE_INTERVAL - elapsed)
                    break 
                    
                else:
                    print(f"⚠️ AI returned None (Quota Limit/Error). Cooling down for 60s...", end=" ")
                    time.sleep(60) 
                    # Retry continues after 1 minute...

            except Exception as e:
                # Even with safe pacing, if we hit a limit, cool down significantly
                error_str = str(e)
                if "429" in error_str or "Quota exceeded" in error_str:
                    print(f"\n⏳ Quota Pulse Hit. Cooling down for 30s...")
                    time.sleep(30)
                else:
                    print(f"❌ Error: {e}")
                    time.sleep(5)
                    # Retry continues...
            
    print(f"\n🎉 Batch Update Complete! ({success_count}/{total} updated)")

if __name__ == "__main__":
    target_user = sys.argv[1] if len(sys.argv) > 1 else "test"
    
    # Priority: Config from .env (Best Practice)
    if Config.GEMINI_API_KEY:
        print(f"🔑 Using API Key from .env: {Config.GEMINI_API_KEY[:5]}...*****")
    else:
        print("❌ No API Key found in .env!")
        sys.exit(1)
        
    batch_process_user(target_user)
