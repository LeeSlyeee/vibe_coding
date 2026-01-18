
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
        
        # Infinite Retry Loop (Until Success)
        retry_count = 0
        
        while True:
            try:
                # Use the new ultra-fast method
                prediction, comment = ai.analyze_diary_with_gemini(content)
                
                if prediction and comment:
                    db.diaries.update_one(
                        {'_id': diary_id},
                        {'$set': {
                            'ai_prediction': prediction,
                            'ai_comment': comment,
                            'task_id': 'batch_update_v3' 
                        }}
                    )
                    print(f"✅ Done! (Retries: {retry_count})")
                    success_count += 1
                    # Super Safe Sleep (Gemini Free is tricky)
                    time.sleep(15) 
                    break 
                else:
                    print(f"⚠️ AI returned None (Attempt {retry_count+1})...", end=" ")
                    retry_count += 1
                    time.sleep(5)

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "Quota exceeded" in error_str:
                    wait_time = 65 + (retry_count * 5) # Progressive wait
                    print(f"\n⏳ Rate Limit Hit! Sleeping for {wait_time}s... (Attempt {retry_count+1})")
                    time.sleep(wait_time)
                    retry_count += 1
                else:
                    print(f"❌ Fatal Error: {e}")
                    break # Fatal error (not rate limit), skip
            
    print(f"\n🎉 Batch Update Complete! ({success_count}/{total} updated)")

if __name__ == "__main__":
    target_user = sys.argv[1] if len(sys.argv) > 1 else "test"
    
    # Optional: Allow passing API Key as 2nd argument
    if len(sys.argv) > 2:
        new_key = sys.argv[2]
        print(f"🔑 Using New API Key provided from command line: {new_key[:5]}...*****")
        Config.GEMINI_API_KEY = AIzaSyAyHJM4BsRT46f2T-NQV5cktZF9f3_QfNw
        os.environ['GEMINI_API_KEY'] = AIzaSyAyHJM4BsRT46f2T-NQV5cktZF9f3_QfNw
        
    batch_process_user(target_user)
