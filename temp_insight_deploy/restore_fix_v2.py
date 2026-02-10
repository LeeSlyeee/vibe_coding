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
    print('Starting SMART Restoration for Jan 16-27... (Best Quality Wins)')
    
    if not os.path.exists(log_path):
        print("Log file not found!")
        return

    lines = open(log_path).readlines()
    
    # Store all candidates per date
    candidates_by_date = {}

    # 1. Collect Valid Data from Logs
    for line in lines: # Order doesn't matter for collection, we verify later
        if 'mood_metrics' in line:
            try:
                start = line.find('{')
                payload = ast.literal_eval(line[start:].strip())
                metrics = payload.get('mood_metrics', [])
                if len(metrics) > 0:
                    for item in metrics:
                        d_str = item.get('created_at') or item.get('date')
                        if not d_str: continue
                        key = d_str[:10] # YYYY-MM-DD
                        if '2026-01-16' <= key <= '2026-01-28':
                            if key not in candidates_by_date:
                                candidates_by_date[key] = []
                            candidates_by_date[key].append(item)
            except:
                continue

    # 2. Pick the BEST entry for each date
    valid_data = {}
    for key, items in candidates_by_date.items():
        # Score strategy:
        # Length of content + Length of AI analysis keys/values
        # This prioritizes "Rich" entries over "Empty" entries (corruption)
        best_item = max(items, key=lambda x: len(x.get('event', '') or x.get('content', '')) + len(str(x.get('ai_analysis', ''))) + len(str(x.get('ai_comment', ''))) + len(str(x)) )
        valid_data[key] = best_item
        print(f"Date {key}: Found {len(items)} versions. Picked size {len(str(best_item))}")

    print(f'Found {len(valid_data)} best-quality log entries.')

    # 3. Update DB
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
            
            # FORCE OVERWRITE with BEST data
            record.content = item.get('event', '') or item.get('content', '') or record.content
            record.mood_score = item.get('score', 0)
            record.analysis_result = rich_data
            
            record.save()
            updated_count += 1
            print(f'Restored {date_key}')
        except Exception as e:
            print(f"Error restoring {date_key}: {e}")

    print(f'Smart Restoration Complete. Updated {updated_count} records.')

run()
