
import os
import psycopg2
from dotenv import load_dotenv
from app import app, db, Diary, safe_decrypt

load_dotenv()

def find_today_diaries():
    with app.app_context():
        # Find diaries with date '2026-02-17'
        today_diaries = Diary.query.filter_by(date="2026-02-17").all()
        
        print(f"🔍 Found {len(today_diaries)} diaries for 2026-02-17:")
        
        for d in today_diaries:
            try:
                print(f"  Diary ID: {d.id}")
                print(f"  Event: {safe_decrypt(d.event)}")
                print(f"  Sleep Condition: {safe_decrypt(d.sleep_condition)}")
                print("-" * 30)
                
                # Auto-fix: If sleep contains "그럭저럭" then update to 13
                sleep_text = safe_decrypt(d.sleep_condition)
                if sleep_text and "그럭저럭" in sleep_text:
                    print(f"  ✅ Matched '그럭저럭' -> Moving to 2026-02-13")
                    d.date = "2026-02-13"
                    db.session.commit()
                    print("  🚀 Moved Successfully!")
                    
            except Exception as e:
                print(f"  ⚠️ Error decrypting diary {d.id}: {e}")

if __name__ == "__main__":
    find_today_diaries()
