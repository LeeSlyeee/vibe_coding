from haru_on.models import HaruOn
from django.contrib.auth import get_user_model
import datetime
import json

u = get_user_model().objects.get(username='slyeee')

# Range Jan 15 to Jan 18 to catch 16/17 with margin
start = datetime.datetime(2026, 1, 15, tzinfo=datetime.timezone.utc)
end = datetime.datetime(2026, 1, 19, tzinfo=datetime.timezone.utc)

records = HaruOn.objects.filter(user=u, created_at__range=(start, end)).order_by('created_at')

print(f"Checking Jan 16-17 Data (Found {records.count()} records)")

for r in records:
    print("-" * 30)
    print(f"Date: {r.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Content: {r.content}")
    print(f"AI Keys: {list(r.analysis_result.keys()) if r.analysis_result else 'None'}")
    if r.analysis_result:
        # Print actual values to see if empty
        print(f"  Comment: {r.analysis_result.get('ai_comment', '')[:30]}")
        print(f"  Emotion Desc: {r.analysis_result.get('emotion_desc', '')[:30]}")
        print(f"  Sleep: {r.analysis_result.get('sleep_condition', '')[:30]}")
