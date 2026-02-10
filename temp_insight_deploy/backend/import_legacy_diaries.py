import json
import os
import django
from datetime import datetime
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime, parse_date
from haru_on.models import HaruOn

User = get_user_model()

def import_diaries(json_path):
    print(f"Reading {json_path}...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to load JSON: {e}")
        return

    # If it's a list, use it. If dict, check key 'diaries'
    if isinstance(data, list):
        diaries_data = data
    else:
        diaries_data = data.get('diaries', [])
        
    print(f"Found {len(diaries_data)} diaries in backup.")
    
    count = 0
    skipped = 0
    errors = 0
    
    # We need a mapping from MongoDB ObjectId (user_id) to Django User object.
    # Since we imported users with their usernames, and we don't have the map of Old_ID -> New_ID handy here (unless we querying by username),
    # we need to find the user.
    # But wait, the exported diary has "user_id" which is an OID string like "697b5a56...".
    # We DO NOT know which username this OID belongs to unless we have the User export file too or we query the old DB.
    # Fortunately, we just imported users from 'remote_users_export.json' which contains "_id" and "username".
    # So we can build a map: OID -> Username -> Django User.
    
    # Let's load users export again to build this map.
    user_map = {} # OID_str -> User Object
    
    try:
        with open('remote_users_export.json', 'r', encoding='utf-8') as f:
            users_json = json.load(f)
            # users_json is list or dict?
            if isinstance(users_json, dict): users_json = users_json.get('users', [])
            
            for u in users_json:
                uid = u.get('_id', {}).get('$oid')
                username = u.get('username')
                if uid and username:
                    try:
                        django_user = User.objects.get(username=username)
                        user_map[uid] = django_user
                    except User.DoesNotExist:
                        pass
    except Exception as e:
        print(f"Warning: Could not load user map from remote_users_export.json: {e}")
        # If we can't map by OID, we might be stuck unless the diary has username embedded (it usually doesn't).
    
    print(f"Built user map for {len(user_map)} users.")

    for d_data in diaries_data:
        # Get User
        oid_user = d_data.get('user_id')
        user = user_map.get(oid_user)
        
        if not user:
            # print(f"Skipping diary for unknown user OID: {oid_user}")
            skipped += 1
            continue
            
        # Check duplicate?
        # Maybe check by created_at and user?
        created_at_data = d_data.get('created_at')
        created_at = None
        if created_at_data and '$date' in created_at_data:
            try:
                created_at = parse_datetime(created_at_data['$date'])
            except:
                pass
        
        if not created_at:
             created_at = timezone.now()

        # Check if exists
        if HaruOn.objects.filter(user=user, created_at=created_at).exists():
            skipped += 1
            continue
            
        # Fields mapping
        content = d_data.get('content', '') or d_data.get('event', '') # usage of event as content if content missing?
        # Actually in MongoDB schema 'event' might be encrypted content or original text.
        # User prompt showed "event": "gAAAA..." which is encrypted.
        # BUT 'sleep_condition' etc are also encrypted.
        # Wait, if the data is encrypted with Fernet key from `vibe_coding`,
        # and we are on `InsightMind`. Does `InsightMind` use the SAME key?
        # CHECK .env!
        
        mood_score = d_data.get('mood_score') or d_data.get('mood_level') or 5
        
        # Analysis Result construction
        analysis = {}
        # Mapping MongoDB flat fields to analysis_result JSON
        for k in ['ai_comment', 'ai_advice', 'ai_analysis', 'ai_prediction', 'emotion_desc', 'emotion_meaning', 'self_talk', 'sleep_desc', 'sleep_condition']:
             if k in d_data:
                 analysis[k] = d_data[k]
        
        diary = HaruOn(
            user=user,
            content=content, # This might be encrypted string.
            mood_score=mood_score,
            analysis_result=analysis,
            is_high_risk= (mood_score <= 2),
            created_at=created_at
        )
        
        try:
            diary.save()
            count += 1
            if count % 100 == 0:
                print(f"Imported {count} diaries...")
        except Exception as e:
            print(f"Error saving diary: {e}")
            errors += 1
            
    print(f"Diary Import finished. {count} imported, {skipped} skipped, {errors} errors.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python import_legacy_diaries.py <path_to_json>")
    else:
        import_diaries(sys.argv[1])
