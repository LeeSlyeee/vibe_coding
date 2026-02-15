
import psycopg2
from config import Config
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = "vibe_db"
DB_USER = "vibe_user"
DB_PASS = "vibe1234"
DB_HOST = "127.0.0.1"
DB_PORT = "5432"

def add_ai_comment_column():
    print("🛠 Adding 'ai_comment' column to PostgreSQL records...")
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if column exists
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='diaries' AND column_name='ai_comment';")
        if cur.fetchone():
            print("✅ 'ai_comment' column already exists.")
        else:
            cur.execute("ALTER TABLE diaries ADD COLUMN ai_comment TEXT;")
            print("✅ 'ai_comment' column added successfully.")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Database Error: {e}")

if __name__ == "__main__":
    add_ai_comment_column()
