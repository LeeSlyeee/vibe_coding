
import psycopg2
import os
from dotenv import load_dotenv
from crypto_utils import EncryptionManager

load_dotenv()

# PG Config
DB_NAME = "vibe_db"
DB_USER = "vibe_user"
DB_PASS = "vibe1234"
DB_HOST = "127.0.0.1"

crypto = EncryptionManager(os.environ.get('ENCRYPTION_KEY'))

def inspect_feb10_diary():
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor()
        
        # Get user id for slyeee
        cur.execute("SELECT id FROM users WHERE username = 'slyeee'")
        user_id = cur.fetchone()[0]
        
        # Get diary for 2026-02-10
        cur.execute("SELECT id, event, emotion_desc, emotion_meaning, self_talk, ai_comment FROM diaries WHERE user_id = %s AND date = '2026-02-10'", (user_id,))
        row = cur.fetchone()
        
        if row:
            print(f"Diary ID: {row[0]}")
            print(f"Event (Raw): {row[1][:20]}...")
            print(f"Event (Decrypted): {crypto.decrypt(row[1])}")
            print(f"Emotion (Decrypted): {crypto.decrypt(row[2])}")
            print(f"AI Comment (Decrypted): {crypto.decrypt(row[5])}")
        else:
            print("No diary found for 2026-02-10")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_feb10_diary()
