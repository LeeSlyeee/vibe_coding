import json
import datetime

path = "/Users/slyeee/Desktop/DATA/DATA2/vibe_coding/full_backup_20260210.json"
print("Loading Django backup...")
with open(path, 'r') as f:
    data = json.load(f)

print(f"Total objects: {len(data)}")

slyeee_diaries = []
for item in data:
    if item.get('model') == 'haru_on.haruon':
        fields = item.get('fields', {})
        # User field in Django dump might be a list of usernames or IDs?
        # In the dump it shows: "user": ["user_f0bdfd"] or "user": ["Guest"]
        users = fields.get('user', [])
        if "slyeee" in users:
            slyeee_diaries.append(item)

print(f"Slyeee diaries found: {len(slyeee_diaries)}")

if slyeee_diaries:
    dates = []
    for d in slyeee_diaries:
        fields = d.get('fields', {})
        c_at = fields.get('created_at')
        if c_at:
            dates.append(c_at)
    
    dates.sort()
    print(f"Oldest: {dates[0]}")
    print(f"Newest: {dates[-1]}")
