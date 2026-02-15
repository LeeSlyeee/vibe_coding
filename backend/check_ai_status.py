
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = "vibe_db"
DB_USER = "vibe_user"
DB_PASS = "vibe1234"
DB_HOST = "127.0.0.1"

def check():
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor()
        cur.execute("SELECT id, date, ai_emotion, ai_comment FROM diaries ORDER BY id DESC LIMIT 5")
        rows = cur.fetchall()
        
        print("--- Recent Diaries ---")
        for r in rows:
            print(f"ID: {r[0]}, Date: {r[1]}")
            print(f"  AI Emotion (Raw): {r[2]}")
            print(f"  AI Comment (Raw): {r[3]}")
        conn.close()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    check()
