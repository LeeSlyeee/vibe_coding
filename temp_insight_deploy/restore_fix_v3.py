import ast
import datetime
import os
from django.utils.dateparse import parse_datetime
from haru_on.models import HaruOn
from django.contrib.auth import get_user_model
User = get_user_model()

def run():
    u = User.objects.get(username='slyeee')
    log_path = '/home/ubuntu/InsightMind/request_log.txt'
    print('Starting NORMALIZED Restoration for Jan 16-27...')
    
    if not os.path.exists(log_path):
        print("Log file not found!")
        return

    lines = open(log_path).readlines()
    
    candidates_by_date = {}

    for line in lines:
        if 'mood_metrics' in line:
            try:
                start = line.find('{')
                payload = ast.literal_eval(line[start:].strip())
                metrics = payload.get('mood_metrics', [])
                if metrics:
                    for item in metrics:
                        d_str = item.get('created_at') or item.get('date')
                        if not d_str: continue
                        key = d_str[:10]
                        if '2026-01-16' <= key <= '2026-01-28':
                            if key not in candidates_by_date: candidates_by_date[key] = []
                            candidates_by_date[key].append(item)
            except:
                continue

    valid_data = {}
    for key, items in candidates_by_date.items():
        best_item = max(items, key=lambda x: len(x.get('event', '') or x.get('content', '')) + len(str(x.get('ai_analysis', ''))) + len(str(x.get('ai_comment', ''))) + len(str(x)) )
        valid_data[key] = best_item

    updated_count = 0
    for date_key, item in valid_data.items():
        try:
            target_date = datetime.datetime.strptime(date_key, '%Y-%m-%d').date()
            start = datetime.datetime.combine(target_date, datetime.time.min).replace(tzinfo=datetime.timezone.utc)
            end = datetime.datetime.combine(target_date, datetime.time.max).replace(tzinfo=datetime.timezone.utc)
            
            record = HaruOn.objects.filter(user=u, created_at__range=(start - datetime.timedelta(days=1), end + datetime.timedelta(days=1))).first()
            if not record:
                record = HaruOn(user=u, created_at=start + datetime.timedelta(hours=9))
            
            # --- NORMALIZATION LOGIC (Updated to match SyncDataView) ---
            ai_data = {}
            
            # Direct mapping
            if item.get('ai_comment'): ai_data['ai_comment'] = item.get('ai_comment')
            if item.get('ai_advice'): ai_data['ai_advice'] = item.get('ai_advice')
            if item.get('ai_analysis'): ai_data['ai_analysis'] = item.get('ai_analysis')
            if item.get('ai_prediction'): ai_data['ai_prediction'] = item.get('ai_prediction')
            
            # Key Renaming (Legacy -> Standard)
            if item.get('sleep'): ai_data['sleep_condition'] = item.get('sleep')
            elif item.get('sleep_condition'): ai_data['sleep_condition'] = item.get('sleep_condition')
            
            if item.get('meaning'): ai_data['emotion_meaning'] = item.get('meaning')
            elif item.get('emotion_meaning'): ai_data['emotion_meaning'] = item.get('emotion_meaning')
            
            if item.get('selftalk'): ai_data['self_talk'] = item.get('selftalk')
            elif item.get('self_talk'): ai_data['self_talk'] = item.get('self_talk')
            
            if item.get('emotion'): ai_data['emotion_desc'] = item.get('emotion')
            elif item.get('emotion_desc'): ai_data['emotion_desc'] = item.get('emotion_desc')
            
            if item.get('weather'): ai_data['weather'] = item.get('weather')
            if item.get('medication_taken'): ai_data['medication_taken'] = item.get('medication_taken')
            if item.get('symptoms'): ai_data['symptoms'] = item.get('symptoms')
            if item.get('gratitude'): ai_data['gratitude_note'] = item.get('gratitude')
            elif item.get('gratitude_note'): ai_data['gratitude_note'] = item.get('gratitude_note')

            # -----------------------------------------------------------

            record.content = item.get('event', '') or item.get('content', '') or record.content
            record.mood_score = item.get('score', 0)
            record.analysis_result = ai_data # Save Normalized Data
            
            record.save()
            updated_count += 1
            print(f'Restored & Normalized {date_key} (Keys: {list(ai_data.keys())})')
        except Exception as e:
            print(f"Error restoring {date_key}: {e}")

    print(f'Normalized Restoration Complete. Updated {updated_count} records.')

run()
