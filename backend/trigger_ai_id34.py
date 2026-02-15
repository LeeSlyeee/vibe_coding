
import psycopg2
import os
import logging
import sys
from dotenv import load_dotenv
from analysis_worker import run_analysis_process
from crypto_utils import EncryptionManager

load_dotenv()

# Config
DB_NAME = "vibe_db"
DB_USER = "vibe_user"
DB_PASS = "vibe1234"
DB_HOST = "127.0.0.1"
crypto = EncryptionManager(os.environ.get('ENCRYPTION_KEY'))

# Configure logging
logging.basicConfig(level=logging.INFO)

def trigger(diary_id):
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor()
        
        # Get diary data
        cur.execute("SELECT id, date, sleep_condition, emotion_desc, emotion_meaning, self_talk, event FROM diaries WHERE id = %s", (diary_id,))
        row = cur.fetchone()
        
        if not row:
            print(f"No diary found for ID {diary_id}")
            return

        date_val = row[1]
        
        def dec(t):
            if not t: return ""
            try: return crypto.decrypt(t)
            except: return t

        sleep = dec(row[2])
        emotion_desc = dec(row[3])
        emotion_meaning = dec(row[4])
        self_talk = dec(row[5])
        event = dec(row[6])
        
        print(f"Triggering analysis for Diary {diary_id} (Date: {date_val})...")
        print(f"Content length: {len(event)}")
        
        run_analysis_process(diary_id, str(date_val), event, sleep, emotion_desc, emotion_meaning, self_talk)
        print("Done.")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    trigger(34)
