import ast
import datetime
import os
from django.utils.dateparse import parse_datetime
from haru_on.models import HaruOn
from django.contrib.auth import get_user_model
User = get_user_model()

def run():
    try:
        u = User.objects.get(username='slyeee')
    except:
        print("User slyeee not found")
        return

    log_path = '/home/ubuntu/InsightMind/request_log.txt'
    print('Starting Deep Restoration for Jan 16-27... (Shell Mode)')
    
    if not os.path.exists(log_path):
        print("Log file not found!")
        return

    lines = open(log_path).readlines()
    candidates = []

    for line in reversed(lines):
        if 'mood_metrics' in line:
            try:
                start = line.find('{')
                payload = ast.literal_eval(line[start:].strip())
                metrics = payload.get('mood_metrics', [])
                if len(metrics) > 5:
                    candidates.extend(metrics)
            except:
                continue

    valid_data = {}
    for item in candidates:
        d_str = item.get('created_at') or item.get('date')
        if not d_str: continue
        key = d_str[:10]
        if '2026-01-16' <= key <= '2026-01-28':
            valid_data[key] = item

    print(f'Found {len(valid_data)} validated log entries.')

    updated_count = 0
    for date_key, item in valid_data.items():
        try:
            target_date = datetime.datetime.strptime(date_key, '%Y-%m-%d').date()
            start = datetime.datetime.combine(target_date, datetime.time.min).replace(tzinfo=datetime.timezone.utc)
            end = datetime.datetime.combine(target_date, datetime.time.max).replace(tzinfo=datetime.timezone.utc)
            
            record = HaruOn.objects.filter(user=u, created_at__range=(start - datetime.timedelta(days=1), end + datetime.timedelta(days=1))).first()
            
            if not record:
                record = HaruOn(user=u, created_at=start + datetime.timedelta(hours=9))
            
            rich_data = {k: v for k, v in item.items() if k not in ['id', 'user_id']}
            
            # FORCE OVERWRITE Bad Data
            record.content = item.get('event', '') or item.get('content', '') or record.content
            record.mood_score = item.get('score', 0)
            record.analysis_result = rich_data
            
            record.save()
            updated_count += 1
            print(f'Restored {date_key}')
        except Exception as e:
            print(f"Error restoring {date_key}: {e}")

    print(f'Deep Restoration Complete. Updated {updated_count} records.')

run()
