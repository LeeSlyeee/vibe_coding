
import os
from dotenv import load_dotenv

# Explicitly load .env from current directory
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

from app import app, db, User, Diary
import sys

def verify_recovery():
    with app.app_context():
        # 1. Find User
        user = User.query.filter_by(username='slyeee').first()
        if not user:
            print("❌ User 'slyeee' not found")
            return

        print(f"👤 Checking Data for User: {user.username} (ID: {user.id})")
        
        # 2. Query Feb 9-16
        diaries = Diary.query.filter_by(user_id=user.id).all()
        target_diaries = []
        
        print(f"📊 Scanning {len(diaries)} total diaries...")
        
        for d in diaries:
            if d.date and d.date.startswith('2026-02'):
                day = int(d.date.split('-')[2])
                if 9 <= day <= 16:
                    target_diaries.append(d)
        
        # 3. Report
        if not target_diaries:
            print("⚠️ No diaries found for Feb 9-16.")
        else:
            print(f"\n✅ [EVIDENCE] Found {len(target_diaries)} Active Diaries (Feb 9-16):")
            print("-" * 60)
            print(f"{'Date':<12} | {'ID':<5} | {'Mood':<5} | {'Status'}")
            print("-" * 60)
            
            target_diaries.sort(key=lambda x: x.date)
            
            for d in target_diaries:
                print(f"{d.date:<12} | {d.id:<5} | {d.mood_level:<5} | 🟢 ACTIVE (Saved in DB)")
            print("-" * 60)
            print("Conclusion: Data is SAFELY stored on the server.")

if __name__ == "__main__":
    verify_recovery()
