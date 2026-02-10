from haru_on.models import HaruOn
from django.contrib.auth import get_user_model
import datetime

user = get_user_model().objects.get(username='slyeee')
print(f"--- Server Data Verification for user: {user.username} ---")

start_date = datetime.datetime(2026, 1, 15, tzinfo=datetime.timezone.utc)
end_date = datetime.datetime(2026, 1, 29, tzinfo=datetime.timezone.utc)

records = HaruOn.objects.filter(
    user=user, 
    created_at__range=(start_date, end_date)
).order_by('created_at')

if not records.exists():
    print("No records found in range Jan 15-29!")
else:
    print(f"Found {records.count()} records.")

for r in records:
    print(f"Date: {r.created_at.date()}")
    try:
        content_preview = r.content.replace('\n', ' ')[:40]
    except:
        content_preview = str(r.content)[:40]
    print(f"  Content: {content_preview}...")
    
    has_ai = bool(r.analysis_result)
    ai_len = len(str(r.analysis_result)) if has_ai else 0
    ai_comment = r.analysis_result.get('ai_comment', 'N/A') if has_ai else 'N/A'
    
    print(f"  AI Data: {'YES' if has_ai else 'NO'} (Len: {ai_len})")
    if has_ai:
        print(f"  AI Comment: {ai_comment[:40]}...")
        if ai_len > 100:
             keys = list(r.analysis_result.keys())
             print(f"  Keys: {keys[:5]}... (+{len(keys)-5} more)")
    print("-" * 20)
