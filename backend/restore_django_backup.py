import json
from datetime import datetime
from app import app, mongo, encrypt_data
from bson.objectid import ObjectId

BACKUP_FILE = "/Users/slyeee/Desktop/DATA/DATA2/vibe_coding/full_backup_20260210.json"

def restore():
    print("🚀 Starting Restore from Django Backup...")
    
    with open(BACKUP_FILE, 'r') as f:
        data = json.load(f)
        
    with app.app_context():
        # Get Slyeee User
        slyeee = mongo.db.users.find_one({'username': 'slyeee'})
        if not slyeee:
            print("❌ User slyeee not found in Mongo!")
            return
            
        user_id = str(slyeee['_id'])
        print(f"✅ User Found: slyeee ({user_id})")
        
        count = 0
        skipped = 0
        
        for item in data:
            if item.get('model') != 'haru_on.haruon':
                continue
                
            fields = item.get('fields', {})
            users = fields.get('user', [])
            
            # Check if this diary belongs to slyeee
            if "slyeee" not in users:
                continue
                
            # Prepare Data
            content = fields.get('content', '')
            mood_score = fields.get('mood_score', 3)
            created_at_str = fields.get('created_at')
            analysis = fields.get('analysis_result', {})
            
            # Date Parsing
            created_at = datetime.now()
            if created_at_str:
                try:
                    # Handle Django ISO format
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                except:
                    print(f"⚠️ Date Parse Error: {created_at_str}")
            
            # Map to Mongo Schema
            raw_diary = {
                'user_id': user_id,
                'event': content,
                'mood_level': mood_score,
                'created_at': created_at,
                'date': created_at.strftime("%Y-%m-%d"),
                
                # Analysis Fields
                'emotion_desc': analysis.get('emotion_desc', ''),
                'emotion_meaning': analysis.get('emotion_meaning', ''),
                'self_talk': analysis.get('self_talk', ''),
                'weather': analysis.get('weather', ''),
                'sleep_condition': analysis.get('sleep_condition', ''),
                'sleep_desc': analysis.get('sleep_condition', ''), # Legacy sync
                
                'ai_prediction': analysis.get('ai_prediction', ''),
                'ai_comment': analysis.get('ai_comment', ''),
                'ai_advice': analysis.get('ai_advice', ''),
                'ai_analysis': analysis.get('ai_analysis', ''),
                
                'medication_taken': analysis.get('medication_taken', False),
                
                'is_restored': True,
                'source': 'django_backup_20260210'
            }
            
            # Check for Duplicate (Date + User)
            # Avoid overwriting existing entries if they are identical?
            # Or just update if exists?
            # Let's check if an entry exists for this date (YYYY-MM-DD range)
            start = created_at.replace(hour=0, minute=0, second=0, microsecond=0)
            end = created_at.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            exists = mongo.db.diaries.find_one({
                'user_id': user_id,
                'created_at': {'$gte': start, '$lte': end}
            })
            
            if exists:
                print(f"⏩ Skipping existing entry for {raw_diary['date']}")
                skipped += 1
                continue
                
            # Encrypt & Insert
            encrypted_diary = encrypt_data(raw_diary)
            
            try:
                mongo.db.diaries.insert_one(encrypted_diary)
                count += 1
                print(f"✅ Restored entry for {raw_diary['date']}")
            except Exception as e:
                print(f"❌ Failed to insert: {e}")

        print(f"\n🎉 Restoration Complete! Inserted: {count}, Skipped: {skipped}")

if __name__ == "__main__":
    restore()
