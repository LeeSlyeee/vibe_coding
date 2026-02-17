
import pymongo
from app import app, db, safe_encrypt
from models import User, Diary
import datetime

def migrate_slyeee():
    print("🚀 Starting Migration for 'slyeee' from MongoDB to PostgreSQL...")

    # 1. Connect to Mongo
    try:
        client = pymongo.MongoClient('mongodb://localhost:27017/')
        mongo_db = client['mood_diary_db']
        mongo_users = mongo_db['users']
        mongo_diaries = mongo_db['diaries']
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ MongoDB Connection Failed: {e}")
        return

    with app.app_context():
        # 2. Get PG User
        pg_user = User.query.filter_by(username='slyeee').first()
        if not pg_user:
            print("❌ PostgreSQL User 'slyeee' not found! Cannot migrate.")
            return
        
        print(f"👤 Found PG User: {pg_user.username} (ID: {pg_user.id})")

        # 3. Get Mongo User
        mongo_user = mongo_users.find_one({'username': 'slyeee'})
        if not mongo_user:
            print("❌ MongoDB User 'slyeee' not found!")
            return

        mongo_uid = str(mongo_user['_id'])
        print(f"👤 Found Mongo User ID: {mongo_uid}")

        # 4. Get Diaries from Mongo
        cursor = mongo_diaries.find({'user_id': mongo_uid})
        diaries = list(cursor)
        print(f"📚 Found {len(diaries)} diaries in MongoDB.")

        migrated_count = 0
        skipped_count = 0

        for d in diaries:
            date_str = d.get('date')
            
            # Check duplication in PG
            exists = Diary.query.filter_by(user_id=pg_user.id, date=date_str).first()
            if exists:
                print(f"   ⏭️ Skipping {date_str} (Already exists in PG)")
                skipped_count += 1
                continue

            # Prepare Data
            try:
                # Assuming data structure matches what's expected for new_diary creation
                # Including removal of 'content' which caused issues earlier
                new_diary = Diary(
                    user_id=pg_user.id,
                    date=date_str,
                    mood_level=d.get('mood_level', 3),
                    event=d.get('event'),
                    emotion_desc=d.get('emotion_desc'),
                    emotion_meaning=d.get('emotion_meaning'),
                    self_talk=d.get('self_talk'),
                    sleep_condition=d.get('sleep_condition'),
                    gratitude_note=d.get('gratitude_note'),
                    ai_comment=d.get('ai_comment'),
                    ai_emotion=d.get('ai_emotion'),
                    weather=d.get('weather'),
                    temperature=d.get('temperature'),
                    mode=d.get('mode', 'green'),
                    mood_intensity=d.get('mood_intensity', 0),
                    safety_flag=d.get('safety_flag', False),
                    created_at=datetime.datetime.now(),
                    updated_at=datetime.datetime.now()
                )
                
                db.session.add(new_diary)
                migrated_count += 1
                print(f"   ✅ Migrated {date_str}")
                
            except Exception as ex:
                print(f"   ❌ Failed to migrate {date_str}: {ex}")

        # Commit
        if migrated_count > 0:
            db.session.commit()
            print(f"\n🎉 Migration Complete! {migrated_count} inserted, {skipped_count} skipped.")
        else:
            print("\n⚠️ No new diaries migrated.")

if __name__ == "__main__":
    migrate_slyeee()
