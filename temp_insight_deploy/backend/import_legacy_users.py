import json
import os
import django
from datetime import datetime
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime

User = get_user_model()

def convert_password_hash(flask_hash):
    # Flask: pbkdf2:sha256:1000000$salt$hash
    # Django: pbkdf2_sha256$1000000$salt$hash
    if not flask_hash:
        return None
    if not flask_hash.startswith('pbkdf2:sha256:1000000$'):
        return None # Unknown format to us
    
    parts = flask_hash.split('$')
    if len(parts) != 3:
        return None
        
    # parts[0] is 'pbkdf2:sha256:1000000'
    # parts[1] is salt
    # parts[2] is hash
    
    return f"pbkdf2_sha256$1000000${parts[1]}${parts[2]}"

def import_users(json_path):
    print(f"Reading {json_path}...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to load JSON: {e}")
        return

    if isinstance(data, list):
        users_data = data
    else:
        users_data = data.get('users', [])
        
    print(f"Found {len(users_data)} users in backup.")
    
    count = 0
    skipped = 0
    errors = 0
    
    for u_data in users_data:
        username = u_data.get('username')
        if not username:
            continue
            
        if User.objects.filter(username=username).exists():
            # print(f"User {username} already exists. Skipping.")
            skipped += 1
            continue
            
        password_hash = u_data.get('password_hash', '')
        django_hash = convert_password_hash(password_hash)
        
        email = u_data.get('email')
        if not email:
            email = ''
            
        created_at_data = u_data.get('created_at')
        date_joined = None
        if created_at_data and '$date' in created_at_data:
            try:
                # ISO format '2026-01-16T04:18:50.638000'
                date_joined = parse_datetime(created_at_data['$date'])
            except:
                pass
        
        # If password format is unknown, we set a dummy usable password? 
        # No, better to leave it unusable or keep original string if it's just a different iteration count.
        # But for now, if it's not our expected format, we just save it as is, user might need to reset password.
        final_password = django_hash if django_hash else password_hash
        
        user = User(
            username=username,
            email=email,
            password=final_password,
            is_active=True,
            risk_level='LOW',
            is_staff=False,
            is_superuser=False
        )
        
        if date_joined:
            user.date_joined = date_joined
            
        try:
            user.save()
            count += 1
            if count % 100 == 0:
                print(f"Imported {count} users...")
        except Exception as e:
            print(f"Error importing {username}: {e}")
            errors += 1
            
    print(f"Import finished. {count} imported, {skipped} skipped, {errors} errors.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python import_legacy_users.py <path_to_json>")
    else:
        import_users(sys.argv[1])
