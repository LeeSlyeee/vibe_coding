
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

from app import app, db, User, Diary

def inspect_columns():
    with app.app_context():
        # Using Flask Model which clearly has 'date'
        # Let's see what 'created_at' says.
        
        user = User.query.filter_by(username='slyeee').first()
        target = Diary.query.filter_by(user_id=user.id, date='2026-02-16').first()
        
        if target:
            print(f"📅 Diary ID: {target.id}")
            print(f"   - date column: '{target.date}'")
            print(f"   - created_at column: '{target.created_at}'")
            
            if str(target.date) not in str(target.created_at):
                print("⚠️  MISMATCH DETECTED! Django (using created_at) will see the Wrong Date.")
            else:
                print("✅ Match.")
        else:
            print("❌ Diary for Feb 16 not found via 'date' query.")

if __name__ == "__main__":
    inspect_columns()
