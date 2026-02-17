
import os
import psycopg2
from dotenv import load_dotenv
from app import app, db, Diary, safe_decrypt

load_dotenv()

def fix_remote_diary():
    with app.app_context():
        # 1. Find the specific diary (Date: 2026-02-17 + Content "그럭저럭")
        print("🔍 Searching for misdated diary (2026-02-17)...")
        candidates = Diary.query.filter_by(date="2026-02-17").all()
        
        found = False
        for d in candidates:
            try:
                sleep_text = safe_decrypt(d.sleep_condition)
                event_text = safe_decrypt(d.event)
                
                print(f"  Diary ID: {d.id} | Date: {d.date} | Event: {event_text} | Sleep: {sleep_text}")
                
                # Check for "그럭저럭" OR user just wrote today but actually meant 13th
                # Or just move ANY diary from today to 13th if user confirms?
                # The user said "수면 관련 내용이 '그럭저럭 잘 잤어'야"
                
                if (sleep_text and "그럭저럭" in sleep_text) or (event_text and "그럭저럭" in event_text):
                    print(f"  ✅ FOUND IT! Moving ID {d.id} to 2026-02-13")
                    d.date = "2026-02-13"
                    db.session.commit()
                    print("  🚀 Update Successful!")
                    found = True
                    break
            except Exception as e:
                print(f"  ⚠️ Error: {e}")
        
        if not found:
            print("❌ No matching diary found on this server.")

if __name__ == "__main__":
    fix_remote_diary()
