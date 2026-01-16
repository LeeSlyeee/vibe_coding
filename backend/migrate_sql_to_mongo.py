import os
import sys
from sqlalchemy import create_engine, MetaData, Table, inspect
from pymongo import MongoClient
from datetime import datetime
from config import Config

def migrate():
    print("🚀 Starting Migration: SQL -> MongoDB")
    
    # 1. SQL Connection
    # Use the legacy connection string from Config or ENV
    # Note: We commented out SQLALCHEMY_DATABASE_URI in config.py, so we need to fetch it manually or uncomment temporarily.
    # For now, let's try to get it from ENV or use the fallback string.
    sql_uri = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:1q2w3e4r@127.0.0.1:3306/mood_diary'
    
    try:
        sql_engine = create_engine(sql_uri)
        connection = sql_engine.connect()
        print("✅ SQL Connected")
    except Exception as e:
        print(f"❌ SQL Connection Failed: {e}")
        return

    # 2. Mongo Connection
    try:
        mongo_client = MongoClient(Config.MONGO_URI)
        mongo_db = mongo_client.get_database()
        print("✅ MongoDB Connected")
    except Exception as e:
        print(f"❌ MongoDB Connection Failed: {e}")
        return

    metadata = MetaData()
    metadata.reflect(bind=sql_engine)
    
    inspector = inspect(sql_engine)
    tables = inspector.get_table_names()
    print(f"Found SQL Tables: {tables}")

    # --- Migrate Users ---
    if 'user' in tables:
        print("\nmigrating users...")
        user_table = Table('user', metadata, autoload_with=sql_engine)
        users = connection.execute(user_table.select()).fetchall()
        
        count = 0
        for u in users:
            # u is a Row object. Access by column name.
            # Columns: id, username, password_hash, (created_at might not exist in old User model, check)
            
            user_doc = {
                'username': u.username,
                'password_hash': u.password_hash,
                # 'created_at': datetime.utcnow() # Add if missing
            }
            
            # Upsert by username to prevent duplicates
            mongo_db.users.update_one(
                {'username': u.username},
                {'$set': user_doc},
                upsert=True
            )
            count += 1
        print(f"✨ Migrated {count} users.")

    # --- Migrate Diaries ---
    if 'diary' in tables:
        print("\nmigrating diaries...")
        diary_table = Table('diary', metadata, autoload_with=sql_engine)
        diaries = connection.execute(diary_table.select()).fetchall()
        
        count = 0
        for d in diaries:
            # Columns: id, user_id, event, emotion_desc, emotion_meaning, self_talk, ...
            
            # Need to map SQL integer user_id to Mongo ObjectId user_id?
            # Issue: New Mongo users have new ObjectIds. Old SQL users have integer IDs.
            # Strategy: Find Mongo user by 'username' using the old SQL user ID relation.
            # This is complex because we just have 'user_id' (int) here.
            
            # Step 1: Find the username of the old SQL user
            # This requires joining or a separate lookup.
            # Simple approach: Since we just migrated users, we can try to look up username by ID from SQL side first?
            # Or assume we migrated users already.
            
            # Let's get the username for this diary's user_id from SQL
            # (Assuming strict consistency)
            
            # This is hard without ORM. Let's assume single user for now or simple mapping.
            # Better way: Look up the user in SQL user table by d.user_id -> get username -> find Mongo user by username -> get Mongo ID.
            
            if 'user' in tables:
                 user_query = user_table.select().where(user_table.c.id == d.user_id)
                 sql_user = connection.execute(user_query).first()
                 if sql_user:
                     mongo_user = mongo_db.users.find_one({'username': sql_user.username})
                     if mongo_user:
                         new_user_id = str(mongo_user['_id']) # Store as string for JWT identity compatibility
                     else:
                         new_user_id = str(d.user_id) # Fallback (will break auth but preserve data)
                 else:
                     new_user_id = str(d.user_id)
            else:
                new_user_id = str(d.user_id)

            diary_doc = {
                'user_id': new_user_id,
                'event': d.event,
                'emotion_desc': d.emotion_desc,
                'emotion_meaning': d.emotion_meaning,
                'self_talk': d.self_talk,
                'mood_level': d.mood_level,
                'ai_prediction': d.ai_prediction,
                'ai_comment': d.ai_comment,
                'created_at': d.created_at
            }
            
            # Insert
            # We don't have a unique key for diaries easily (maybe created_at + user_id?)
            # Let's just insert for now. To avoid duplicates, check created_at?
            existing = mongo_db.diaries.find_one({
                'user_id': new_user_id,
                'created_at': d.created_at
            })
            
            if not existing:
                mongo_db.diaries.insert_one(diary_doc)
                count += 1
                
        print(f"✨ Migrated {count} diaries.")

    connection.close()
    print("\n✅ Migration Completed!")

if __name__ == '__main__':
    migrate()
