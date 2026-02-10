import json
import os
import django
import sys
from cryptography.fernet import Fernet
from datetime import datetime
from django.utils.dateparse import parse_datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from haru_on.models import HaruOn

User = get_user_model()

# Key from vibe_coding project
LEGACY_KEY = b'no-cI2OmQ0K2Eb7cNlfmndN159GET62e-YqVncAkjKg='
cipher_suite = Fernet(LEGACY_KEY)

def decrypt_text(text):
    if not text: return text
    if not isinstance(text, str): return text
    if not text.startswith('gAAAA'): return text
    try:
        return cipher_suite.decrypt(text.encode()).decode()
    except:
        return text

def update_diaries_full(json_path, user_map_path):
    print(f"Reading {json_path}...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            diaries_data = data.get('diaries', [])
        else:
            diaries_data = data
    except Exception as e:
        print(f"Failed to load JSON: {e}")
        return

    # Build User Map
    user_map = {}
    try:
        with open(user_map_path, 'r', encoding='utf-8') as f:
            users_json = json.load(f)
            if isinstance(users_json, dict): users_json = users_json.get('users', [])
            for u in users_json:
                uid = u.get('_id', {}).get('$oid')
                username = u.get('username')
                if uid and username:
                    user_map[uid] = username
    except:
        pass

    count = 0
    updated_count = 0
    
    for d_data in diaries_data:
        # Find User
        oid_user = d_data.get('user_id')
        username = user_map.get(oid_user)
        if not username: continue
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            continue
            
        # Find Diary (by created_at)
        created_at_data = d_data.get('created_at')
        created_at = None
        if created_at_data and '$date' in created_at_data:
            try:
                created_at = parse_datetime(created_at_data['$date'])
            except: pass
            
        if not created_at: continue
        
        try:
            diary = HaruOn.objects.get(user=user, created_at=created_at)
        except HaruOn.DoesNotExist:
            continue

        # Prepare Extra Fields to inject into analysis_result
        # Fields to fetch and potentially decrypt
        fields_to_sync = [
            'weather', 'temperature', 'symptoms', 'medication_taken', 'gratitude_note', 
            'sleep_condition', 'sleep_desc', 'emotion_desc', 'emotion_meaning', 'self_talk'
        ]
        
        current_analysis = diary.analysis_result or {}
        is_modified = False
        
        for field in fields_to_sync:
            if field in d_data:
                val = d_data[field]
                # Decrypt if string and encrypted
                if isinstance(val, str) and val.startswith('gAAAA'):
                     val = decrypt_text(val)
                
                # Update if missing or different
                # Note: valid could be empty string/list/false which is falsy but valid data.
                # So we check simple existence or update.
                current_analysis[field] = val
                is_modified = True
        
        if is_modified:
            diary.analysis_result = current_analysis
            diary.save()
            updated_count += 1
        
        count += 1
        if count % 50 == 0:
            print(f"Checked {count} diaries...")

    print(f"Finished. Checked {count}, Updated {updated_count}.")

if __name__ == '__main__':
    update_diaries_full('remote_diaries_export.json', 'remote_users_export.json')
