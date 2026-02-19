
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

from app import app, db, User, Diary

def deduplicate():
    with app.app_context():
        user = User.query.filter_by(username='slyeee').first()
        if not user: return

        print(f"🧹 Deduplicating Diaries for User: {user.username}")
        
        # Target timestamps
        target_dates = ['2026-02-09', '2026-02-16']
        
        for date_str in target_dates:
            diaries = Diary.query.filter_by(user_id=user.id, date=date_str).order_by(Diary.id.desc()).all()
            
            if len(diaries) > 1:
                print(f"⚠️ Found {len(diaries)} duplicates for {date_str}!")
                
                # Keep the latest one (highest ID)
                latest = diaries[0]
                duplicates = diaries[1:]
                
                print(f"   ✅ Keeping ID: {latest.id} (Mood: {latest.mood_level})")
                
                for d in duplicates:
                    print(f"   🗑️ Deleting ID: {d.id}...")
                    db.session.delete(d)
                
                db.session.commit()
                print(f"   ✨ Cleared {len(duplicates)} duplicates for {date_str}.")
            else:
                print(f"✅ {date_str}: Clean (Count: {len(diaries)})")

if __name__ == "__main__":
    deduplicate()
