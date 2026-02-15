
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# PG Config
DB_NAME = "vibe_db"
DB_USER = "vibe_user"
DB_PASS = "vibe1234"
DB_HOST = "127.0.0.1"

def add_ai_emotion_column():
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if column exists
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='diaries' AND column_name='ai_emotion';")
        if cur.fetchone():
            print("✅ 'ai_emotion' column already exists.")
        else:
            print("➕ Adding 'ai_emotion' column...")
            cur.execute("ALTER TABLE diaries ADD COLUMN ai_emotion TEXT;")
            print("✅ 'ai_emotion' column added successfully.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Failed to add column: {e}")

if __name__ == "__main__":
    add_ai_emotion_column()
