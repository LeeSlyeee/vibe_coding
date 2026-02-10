from haru_on.models import HaruOn
from django.contrib.auth import get_user_model
import datetime
import json

def json_serial(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    return str(obj)

u = get_user_model().objects.get(username='slyeee')

# Fetch Feb 1 (Reference)
start_feb = datetime.datetime(2026, 2, 1, tzinfo=datetime.timezone.utc)
end_feb = datetime.datetime(2026, 2, 2, tzinfo=datetime.timezone.utc)
feb_record = HaruOn.objects.filter(user=u, created_at__range=(start_feb, end_feb)).first()

# Fetch Jan 28 (Restored)
start_jan = datetime.datetime(2026, 1, 28, tzinfo=datetime.timezone.utc)
end_jan = datetime.datetime(2026, 1, 29, tzinfo=datetime.timezone.utc)
jan_record = HaruOn.objects.filter(user=u, created_at__range=(start_jan, end_jan)).first()

print("--- Data Structure Comparison ---")

if feb_record:
    print(f"[Feb 1 - Reference]")
    print(f"Content: {feb_record.content[:30]}...")
    print(f"Stats: Score={feb_record.mood_score}, AI Len={len(str(feb_record.analysis_result))}")
    if feb_record.analysis_result:
        print(f"Keys: {sorted(list(feb_record.analysis_result.keys()))}")
        # Sample deep value
        print(f"Comment: {feb_record.analysis_result.get('ai_comment', 'N/A')[:30]}...")
else:
    print("[Feb 1] NOT FOUND!")

print("-" * 30)

if jan_record:
    print(f"[Jan 28 - Restored]")
    print(f"Content: {jan_record.content[:30]}...")
    print(f"Stats: Score={jan_record.mood_score}, AI Len={len(str(jan_record.analysis_result))}")
    if jan_record.analysis_result:
        print(f"Keys: {sorted(list(jan_record.analysis_result.keys()))}")
        print(f"Comment: {jan_record.analysis_result.get('ai_comment', 'N/A')[:30]}...")
else:
    print("[Jan 28] NOT FOUND!")
    
# Deep Diff
if feb_record and jan_record:
    feb_keys = set(feb_record.analysis_result.keys()) if feb_record.analysis_result else set()
    jan_keys = set(jan_record.analysis_result.keys()) if jan_record.analysis_result else set()
    
    missing = feb_keys - jan_keys
    if missing:
        print(f"CRITICAL: Jan 28 is missing keys present in Feb 1: {missing}")
    else:
        print("Structure Match: Jan 28 has all keys present in Feb 1.")
