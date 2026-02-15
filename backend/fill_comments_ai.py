
import psycopg2
import requests
import json
import os
from dotenv import load_dotenv

# Load Env
load_dotenv()

# PG Config
DB_NAME = "vibe_db"
DB_USER = "vibe_user"
DB_PASS = "vibe1234"
DB_HOST = "127.0.0.1"

def generate_ai_comment_for_text(diary_dict):
    try:
        content = f"""
        [일기 데이터]
        사건: {diary_dict.get('event')}
        감정: {diary_dict.get('emotion_desc')}
        의미: {diary_dict.get('emotion_meaning')}
        스스로에게 한 말: {diary_dict.get('self_talk')}
        """
        
        prompt_text = (
            f"너는 다정하고 섬세한 심리 상담 AI '하루온'이야. 아래 회원의 일기를 읽고, 따뜻한 위로와 공감의 코멘트를 남겨줘.\n"
            f"{content}\n\n"
            "### 지시사항:\n"
            "1. 회원의 감정을 깊이 경청하고 있다는 느낌을 줘.\n"
            "2. 사건의 나열보다는 그 속의 **감정의 의미**를 읽어줘.\n"
            "3. 말투는 부드러운 '해요체'를 사용해 (반말 금지).\n"
            "4. 길이는 150자 ~ 200자 정도로 충분히 풍부하게.\n"
            "5. 답변만 바로 출력해.\n\n"
            "상담사 코멘트:"
        )
        
        payload = {
            "model": "haru-on-gemma",
            "prompt": prompt_text,
            "stream": False,
            "options": {
                "temperature": 0.7, 
                "num_predict": 400
            }
        }
        res = requests.post("http://localhost:11434/api/generate", json=payload, timeout=90)
        if res.status_code == 200:
             return res.json().get('response', '').strip()
    except Exception as e:
        print(f"AI Gen Error: {e}")
    return None

def fill_missing_comments():
    print("🪄 Filling Missing AI Comments via Local LLM...")
    
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    conn.autocommit = True
    cur = conn.cursor()
    
    # 1. Select diaries with NULL ai_comment
    cur.execute("SELECT id, date, event, emotion_desc, emotion_meaning, self_talk FROM diaries WHERE ai_comment IS NULL OR ai_comment = '';")
    rows = cur.fetchall()
    total = len(rows)
    print(f"📄 Found {total} diaries missing comments.")
    
    count = 0
    for r in rows:
        d_id, date, event, emo_desc, emo_mean, self_talk = r
        # Decrypt if needed?
        # Assuming DB stores them encrypted if using app.py path, but migrated data might be plain or encrypted.
        # But here we read raw. If raw is encrypted (starts with gAAAA), we can't read it easily without key.
        # However, the migration script `migrate_mongo_to_pg_v3.py` inserted them plainly?
        # Let's check `migrate_mongo_to_pg_v3.py`.
        # Ah, `migrate_mongo_to_pg_v3.py` just inserted value directly from Mongo.
        # And Mongo values might be encrypted (by `migrate_encrypt.py`).
        
        # If encrypted, we must decrypt first to generate comment.
        # But wait, `migrate_encrypt.py` encrypted fields in Mongo.
        # So PG has encrypted data.
        
        # We need `EncryptionManager` to decrypt before sending to AI.
        
        # Let's import crypto
        from crypto_utils import EncryptionManager
        crypto = EncryptionManager(os.environ.get('ENCRYPTION_KEY'))
        
        def decrypt_val(v):
            if not v: return ""
            return crypto.decrypt(v)

        diary_dict = {
            'event': decrypt_val(event),
            'emotion_desc': decrypt_val(emo_desc),
            'emotion_meaning': decrypt_val(emo_mean),
            'self_talk': decrypt_val(self_talk)
        }
        
        print(f"   Generating for Diary {d_id} ({date})...")
        comment = generate_ai_comment_for_text(diary_dict)
        
        if comment:
            # We must ENCRYPT the comment before saving to PG, 
            # because app.py expects encrypted ai_comment.
            encrypted_comment = crypto.encrypt(comment)
            
            cur.execute("UPDATE diaries SET ai_comment = %s WHERE id = %s", (encrypted_comment, d_id))
            print(f"   ✅ Saved comment for {date}")
            count += 1
        else:
            print(f"   ❌ Failed to generate for {date}")

    print(f"🎉 Complete! Generated {count}/{total} comments.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    fill_missing_comments()
