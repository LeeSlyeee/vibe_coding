
import os
import psycopg2
from dotenv import load_dotenv
from app import app, db, Diary, safe_decrypt

load_dotenv()

def fix_diary_date():
    with app.app_context():
        print("🔍 Searching for diary with '그럭저럭 잘 잤어'...")
        diaries = Diary.query.all()
        found = False
        
        for d in diaries:
            try:
                sleep_text = safe_decrypt(d.sleep_condition)
                if sleep_text and "그럭저럭 잘 잤어" in sleep_text:
                    print(f"✅ Found Diary ID: {d.id}")
                    print(f"   Current Date: {d.date}")
                    print(f"   Created At: {d.created_at}")
                    print(f"   Decrypted Sleep: {sleep_text}")
                    
                    # Update Date to 2026-02-13
                    d.date = "2026-02-13"
                    db.session.commit()
                    print("🚀 Updated Date to 2026-02-13 successfully!")
                    found = True
                    break
            except Exception as e:
                print(f"⚠️ Error processing diary {d.id}: {e}")
                continue
        
        if not found:
            print("❌ Diary not found with that content.")

if __name__ == "__main__":
    fix_diary_date()
