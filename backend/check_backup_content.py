import json
from bson.json_util import loads
from datetime import datetime

# Path to backup file
backup_path = "/Users/slyeee/Desktop/DATA/DATA2/vibe_coding/mood_diary_backup.json"

print("Loading backup file (this may take a moment)...")
with open(backup_path, 'r') as f:
    data = loads(f.read())

print("Backup loaded.")
print(f"Top-level keys: {list(data.keys())}")

# Identify slyeee
slyeee_user = None
for user in data.get('users', []):
    if user.get('username') == 'slyeee':
        slyeee_user = user
        break

if not slyeee_user:
    print("User 'slyeee' not found in backup.")
    exit()

print(f"Slyeee ID: {slyeee_user['_id']}")
user_id_str = str(slyeee_user['_id'])

# Check Diaries
diaries = data.get('diaries', [])
print(f"Total diaries in backup: {len(diaries)}")

slyeee_diaries = []
for d in diaries:
    # Check both string and ObjectId user_id
    d_uid = d.get('user_id')
    if str(d_uid) == user_id_str:
        slyeee_diaries.append(d)

print(f"Diaries for slyeee found: {len(slyeee_diaries)}")

# Check Date Range
if slyeee_diaries:
    dates = []
    for d in slyeee_diaries:
        created_at = d.get('created_at')
        if isinstance(created_at, datetime):
            dates.append(created_at)
        elif isinstance(created_at, str):
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                dates.append(dt)
            except:
                pass
    
    if dates:
        dates.sort()
        print(f"Oldest Entry: {dates[0]}")
        print(f"Newest Entry: {dates[-1]}")
        
        # Check Feb 2026
        feb_2026 = [d for d in dates if d.year == 2026 and d.month == 2]
        print(f"Entries in Feb 2026: {len(feb_2026)}")
    else:
        print("No valid created_at dates found.")
else:
    print("No diaries for slyeee.")
