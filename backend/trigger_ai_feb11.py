
import psycopg2
import os
import logging
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

# Configure logging to stdout for this script
logging.basicConfig(level=logging.INFO)

def trigger():
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor()
        # Get latest diary for date '2026-02-11'
        # Note: 'event' column usually stores the 'content' in new schema
        cur.execute("SELECT id, sleep_condition, emotion_desc, emotion_meaning, self_talk, event FROM diaries WHERE date = '2026-02-11' ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        
        if not row:
            print("No diary found for 2026-02-11")
            return

        diary_id = row[0]
        
        def dec(t):
            if not t: return ""
            try: return crypto.decrypt(t)
            except: return t

        sleep = dec(row[1])
        emotion_desc = dec(row[2])
        emotion_meaning = dec(row[3])
        self_talk = dec(row[4])
        event = dec(row[5])
        
        print(f"Triggering analysis for Diary {diary_id}...")
        run_analysis_process(diary_id, "2026-02-11", event, sleep, emotion_desc, emotion_meaning, self_talk)
        print("Done.")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    trigger()
