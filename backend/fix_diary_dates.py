
from app import app, db
from models import Diary, User
from datetime import datetime

def fix_diary_dates():
    print("🔧 Fixing Diary created_at timestamps...")
    with app.app_context():
        # Get slyeee
        user = User.query.filter_by(username='slyeee').first()
        if not user:
            print("❌ User slyeee not found")
            return

        diaries = Diary.query.filter_by(user_id=user.id).all()
        count = 0
        
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        for d in diaries:
            # d.date is string 'YYYY-MM-DD'
            try:
                real_date = datetime.strptime(d.date, '%Y-%m-%d')
                
                # Set time to 23:59:59 of that day (end of day) or 12:00:00
                # Let's use 09:00:00 (morning) just to be safe from Timezone checks being -9h
                # If we set 00:00:00, and frontend does UTC conversion, it might show previous day.
                # Safest is 12:00:00 Local.
                new_timestamp = real_date.replace(hour=12, minute=0, second=0)
                
                # Update if created_at is "Today" but diary date is NOT "Today"
                # (Or just force update all migrated ones)
                
                # We simply update ALL diaries for consistency, so created_at matches the entry date.
                d.created_at = new_timestamp
                d.updated_at = new_timestamp
                
                # Mark dirty
                db.session.add(d)
                count += 1
                
                print(f"   📝 Fixed Diary {d.id}: Date={d.date} -> CreatedAt={new_timestamp}")
                
            except Exception as e:
                print(f"   ⚠️ Error fixing Diary {d.id}: {e}")

        if count > 0:
            db.session.commit()
            print(f"✅ Successfully updated {count} diaries for user 'slyeee'.")
        else:
            print("⚠️ No diaries updated.")

if __name__ == "__main__":
    fix_diary_dates()
