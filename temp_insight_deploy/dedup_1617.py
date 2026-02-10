from haru_on.models import HaruOn
from django.contrib.auth import get_user_model
import datetime

u = get_user_model().objects.get(username='slyeee')

# Check Jan 16
start = datetime.datetime(2026, 1, 16, tzinfo=datetime.timezone.utc)
end = datetime.datetime(2026, 1, 17, tzinfo=datetime.timezone.utc)
# Strict range for UTC day Jan 16
# Wait, if stored as 16:04 (which is Jan 17 KST), user considers it Jan 17?
# But log date says '2026-01-16'.
# We should check "Logic Date".
# Let's check wide range and print details for dedup.

print("--- Dedup Check Jan 15-18 ---")
start_wide = datetime.datetime(2026, 1, 15, tzinfo=datetime.timezone.utc)
end_wide = datetime.datetime(2026, 1, 19, tzinfo=datetime.timezone.utc)

records = HaruOn.objects.filter(user=u, created_at__range=(start_wide, end_wide)).order_by('created_at')

for r in records:
    print(f"ID: {r.id} | Date: {r.created_at} | Content: {r.content[:20]} | AI Keys: {len(r.analysis_result.keys()) if r.analysis_result else 0}")
