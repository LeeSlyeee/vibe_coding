import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add current dir to path to find app & crypto_utils
sys.path.append(os.getcwd())

load_dotenv()

# Import App Components
try:
    from app import app, db, Diary
    from crypto_utils import crypto_manager
    print("✅ Successfully imported app components")
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

def restore_diary():
    with app.app_context():
        # Check if already exists to avoid duplicate
        existing = Diary.query.filter_by(user_id=10, date='2026-02-15').first()
        if existing:
            print("⚠️ Diary for 2026-02-15 already exists for User ID 10.")
            return

        print("🔄 Encrypting content...")
        # Data from reboot_db dump
        content = crypto_manager.encrypt("마음온을 하루종일 작업햇어.")
        emo_desc = crypto_manager.encrypt("마음이 조급해. 불안해.")
        emo_mean = crypto_manager.encrypt("어서 마음온을 완벽하게 잘 마무리해서, 조급함과 불안함을 좀 날려버리고 싶어.")
        self_talk = crypto_manager.encrypt("성희야!!! 넌 잘하고 있어!!!")
        sleep = crypto_manager.encrypt("늦게 잠들었지만 잠은 잘 잤어.")
        gratitude = crypto_manager.encrypt("") # Empty string if null

        new_diary = Diary(
            user_id=10, 
            date='2026-02-15', 
            event=content, 
            content=content, # Just in case model changed
            emotion_desc=emo_desc, 
            emotion_meaning=emo_mean, 
            self_talk=self_talk, 
            gratitude_note=gratitude, 
            sleep_condition=sleep, 
            mood_level=3, 
            weather='흐림 ☁️', 
            temperature='9', 
            safety_flag=True,
            created_at=datetime.now() # Current timestamp for restoration
        )
        
        db.session.add(new_diary)
        db.session.commit()
        print("✅ Diary 2026-02-15 Restored Successfully!")

if __name__ == "__main__":
    restore_diary()
