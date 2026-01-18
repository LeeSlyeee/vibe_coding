
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
        
        # Retry Loop for 429 Errors
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Use the new ultra-fast method
                prediction, comment = ai.analyze_diary_with_gemini(content)
                
                if prediction and comment:
                    db.diaries.update_one(
                        {'_id': diary_id},
                        {'$set': {
                            'ai_prediction': prediction,
                            'ai_comment': comment,
                            'task_id': 'batch_update_v2' # Reset task
                        }}
                    )
                    print("✅ Done!")
                    success_count += 1
                    # Success Sleep (avoid hitting limit again)
                    time.sleep(10) 
                    break # Success, move to next diary
                else:
                    print(f"⚠️ AI returned None (Attempt {retry_count+1})...", end=" ")
                    retry_count += 1
                    time.sleep(2)

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "Quota exceeded" in error_str:
                    print(f"\n⏳ Rate Limit Hit! Sleeping for 35s... (Attempt {retry_count+1})")
                    time.sleep(35)
                    retry_count += 1
                else:
                    print(f"❌ Error: {e}")
                    break # Fatal error, skip
            
    print(f"\n🎉 Batch Update Complete! ({success_count}/{total} updated)")

if __name__ == "__main__":
    target_user = sys.argv[1] if len(sys.argv) > 1 else "test"
    batch_process_user(target_user)
