import sys
import os
from app import app, db, Diary, start_analysis_thread
from analysis_worker import generate_ai_analysis, crypto
from dotenv import load_dotenv

def fix_scores_orm():
    print("🚀 Starting Score Fix Process (ORM Mode)...")
    
    with app.app_context():
        # 1. Fetch Diaries with mood_level 0 or NULL (or default 3/5 if deemed unanalyzed)
        # Note: In app.py, mood_level defaults to 3. 
        # But user said "0 points". Let's check for 0.
        # Also check for empty AI comment.
        diaries = Diary.query.filter(
            (Diary.mood_level == 0) | 
            (Diary.ai_comment == None) | 
            (Diary.ai_comment == "")
        ).all()
        
        print(f"🔍 Found {len(diaries)} diaries to analyze.")
        
        for diary in diaries:
            print(f"🧵 Analyzing Diary {diary.id} ({diary.date})...")
            
            # Decrypt Content
            # app.py's safe_decrypt uses crypto_utils, let's reuse it or manual
            # Diary model fields are stored encrypted in app.py logic.
            
            def decrypt(val):
                if not val: return ""
                try: return crypto.decrypt(val)
                except: return val
                
            content = decrypt(diary.event)
            sleep = decrypt(diary.sleep_condition)
            emotion_desc = decrypt(diary.emotion_desc)
            emotion_meaning = decrypt(diary.emotion_meaning)
            self_talk = decrypt(diary.self_talk)
            
            full_text = f"날짜: {diary.date}\n수면: {sleep}\n사건: {content}\n감정: {emotion_desc}\n의미: {emotion_meaning}\n스스로에게: {self_talk}"
            
            # AI Call
            comment, emotion, score = generate_ai_analysis(full_text)
            
            print(f"   => AI Result: Score={score}, Emotion={emotion}")
            
            # Update Diary Object
            # Encrypt AI results
            diary.ai_comment = crypto.encrypt(comment)
            diary.ai_emotion = crypto.encrypt(emotion)
            
            # Update Score (mood_level? mood_score?)
            # In app.py model 'Diary', the field is 'mood_level' (1-10?) or 'mood_intensity'?
            # Let's check app.py Create Diary:
            #   mood_level=data.get('mood_level', 3)
            #   mood_intensity=0
            # user said "0 points".
            
            try:
                s_int = int(score)
                s_int = max(1, min(10, s_int))
            except:
                s_int = 5
            
            diary.mood_level = s_int
            # Also update mood_score if it exists? app.py Diary model seems to use mood_level.
            
            db.session.add(diary)
            print(f"   ✅ Updated Diary {diary.id}")
            
        db.session.commit()
        print("🎉 All Done.")

if __name__ == "__main__":
    fix_scores_orm()
