import os
import psycopg2
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# .env 로드 (필요시)
load_dotenv(dotenv_path="/Users/slyeee/Desktop/DATA/DATA2/vibe_coding/temp_insight_deploy/backend/.env")

# DB 접속 정보 (Flask 앱 기준)
# app.py: app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://vibe_user:vibe1234@127.0.0.1/vibe_db'
DB_HOST = "127.0.0.1"
DB_NAME = "vibe_db"
DB_USER = "vibe_user"
DB_PASS = "vibe1234"
DB_PORT = "5432"

ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY') or "no-cI2OmQ0K2Eb7cNlfmndN159GET62e-YqVncAkjKg="
cipher = Fernet(ENCRYPTION_KEY)

def check_postgres():
    print(f"--- POSTGRES DB CHECK ({DB_NAME}) ---")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        cur = conn.cursor()
        
        # 1. User Count
        cur.execute("SELECT count(*) FROM users WHERE username NOT LIKE 'app_%' AND role != 'admin';")
        user_count = cur.fetchone()[0]
        print(f"Valid Patients Count: {user_count}")
        
        # 2. Diary Count
        cur.execute("SELECT count(*) FROM diaries;")
        diary_count = cur.fetchone()[0]
        print(f"Total Diaries Count: {diary_count}")
        
        # 3. Sample Data
        cur.execute("SELECT id, user_id, date, event FROM diaries ORDER BY created_at DESC LIMIT 1;")
        sample = cur.fetchone()
        if sample:
            print(f"Latest Diary: ID={sample[0]}, UserID={sample[1]}, Date={sample[2]}")
            # Try Decrypt
            try:
                decrypted = cipher.decrypt(sample[3].encode()).decode()
                print(f"Decrypted Event Sample: {decrypted[:20]}...")
            except:
                print(f"Decrypted Event Sample: (Failed or Not Encrypted) {sample[3]}")
        else:
            print("No diaries found.")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"DB Connection Error: {e}")
        
    print("--- END ---")

if __name__ == "__main__":
    check_postgres()
