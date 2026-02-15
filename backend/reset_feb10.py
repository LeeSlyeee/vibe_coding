
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# PG Config
DB_NAME = "vibe_db"
DB_USER = "vibe_user"
DB_PASS = "vibe1234"
DB_HOST = "127.0.0.1"

def reset_feb10_diary():
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Get user id for slyeee
        cur.execute("SELECT id FROM users WHERE username = 'slyeee'")
        user_row = cur.fetchone()
        if not user_row:
            print("User not found")
            return
        user_id = user_row[0]
        
        # Reset Diary Content (Delete "Automated Test Update")
        # Keep metadata like mood_level, weather if possible, or reset them too?
        # User said "modify", so let's keep metadata but clear content.
        cur.execute("""
            UPDATE diaries 
            SET event = '', 
                emotion_desc = '', 
                emotion_meaning = '', 
                self_talk = '', 
                gratitude_note = '', 
                sleep_condition = '', 
                ai_comment = NULL, 
                ai_emotion = NULL
            WHERE user_id = %s AND date = '2026-02-10'
        """, (user_id,))
        
        print("✅ Diary for 2026-02-10 content has been reset (emptied).")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    reset_feb10_diary()
