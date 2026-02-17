import os
import psycopg2
from analysis_worker import generate_ai_analysis, crypto
from dotenv import load_dotenv

load_dotenv()

# PG Config
DB_NAME = "vibe_db"
DB_USER = "vibe_user"
DB_PASS = "vibe1234"
DB_HOST = "127.0.0.1"

def fix_scores():
    print("🚀 Starting Score Fix Process...")
    
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    conn.autocommit = True
    cur = conn.cursor()
    
    # 1. Fetch Diaries with mood_score 0 or NULL
    cur.execute("""
        SELECT id, created_at, content, emotion_desc, emotion_meaning, self_talk, sleep_condition 
        FROM diaries 
        WHERE mood_score IS NULL OR mood_score = 0 OR mood_score = 5
    """)
    # Note: mood_score=5 might be default fallback, but let's re-analyze if we want real AI score.
    # For now, focus on 0/NULL which are definitely wrong.
    
    rows = cur.fetchall()
    print(f"🔍 Found {len(rows)} diaries to analyze.")
    
    for row in rows:
        diary_id, date, content, emotion_desc, emotion_meaning, self_talk, sleep = row
        print(f"🧵 Analyzing Diary {diary_id} ({date})...")
        
        # Build Text
        # Decrypt if needed? Assuming local DB stores encrypted text in these fields?
        # NO, 'content' etc are usually encrypted strings.
        # We need to decrypt them before sending to AI.
        
        try:
            dec_content = crypto.decrypt(content)
            dec_emotion = crypto.decrypt(emotion_desc)
            dec_meaning = crypto.decrypt(emotion_meaning)
            dec_talk = crypto.decrypt(self_talk)
            dec_sleep = crypto.decrypt(sleep)
        except:
            # Fallback: maybe not encrypted or partial
            dec_content = content
            dec_emotion = emotion_desc
            dec_meaning = emotion_meaning
            dec_talk = self_talk
            dec_sleep = sleep
            
        full_text = f"날짜: {date}\n수면: {dec_sleep}\n사건: {dec_content}\n감정: {dec_emotion}\n의미: {dec_meaning}\n스스로에게: {dec_talk}"
        
        # AI Call
        comment, emotion, score = generate_ai_analysis(full_text)
        
        print(f"   => AI Result: Score={score}, Emotion={emotion}")
        
        # Encrypt AI Result
        enc_comment = crypto.encrypt(comment)
        enc_ai_emotion = crypto.encrypt(emotion)
        
        # Update DB
        try:
            score_int = int(score)
            score_int = max(1, min(10, score_int))
        except:
            score_int = 5
            
        cur.execute("""
            UPDATE diaries 
            SET mood_score = %s, ai_comment = %s, ai_emotion = %s
            WHERE id = %s
        """, (score_int, enc_comment, enc_ai_emotion, diary_id))
        
        print(f"   ✅ Updated Diary {diary_id}")
        
    print("🎉 All Done.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    fix_scores()
