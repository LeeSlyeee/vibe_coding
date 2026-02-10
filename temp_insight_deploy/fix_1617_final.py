from haru_on.models import HaruOn
from django.contrib.auth import get_user_model
import json

u = get_user_model().objects.get(username='slyeee')

# Fix Jan 16 (ID 791 or similar in that time slot)
# Log: created_at 2026-01-15 16:04 UTC
r16 = HaruOn.objects.filter(user=u, created_at__year=2026, created_at__month=1, created_at__day__lte=16, created_at__day__gte=15).order_by('created_at').first()
# Should be 791 based on dedup output

if r16:
    print(f"Fixing Jan 16 Record (ID: {r16.id})...")
    # Log Data for Jan 16
    data16 = {
        'ai_comment': '당신의 마음을 이해합니다. 상쾌하고 기분이 한결 가벼워졌다.',
        'sleep_condition': '중간에 깼다.',
        'emotion_desc': '상쾌하고 기분이 한결 가벼워졌다.',
        'emotion_meaning': '이 감정이 나에게 어떤 의미인지 생각해보았다.',
        'self_talk': '그래도 오늘 하루 잘 버텼어. 내일은 더 좋을 거야.',
        'medication_taken': False # Default or from log? Log didn't show it, so keep existing or default.
        # Log keys: ['emotion', 'ai_advice', 'selftalk', 'ai_comment', 'ai_analysis', 'date', 'sleep', 'event', 'created_at', 'meaning', 'ai_prediction', 'score']
    }
    r16.content = '오랜만에 산책을 다녀왔다.'
    r16.mood_score = 4
    # Merge or Replace? Replace to be safe and rich.
    if not r16.analysis_result: r16.analysis_result = {}
    r16.analysis_result.update(data16)
    r16.save()
    print("Jan 16 Fixed.")
else:
    print("Jan 16 Record NOT FOUND.")

# Fix Jan 17 (ID 790 or similar)
# Log: created_at 2026-01-16 16:04 UTC
r17 = HaruOn.objects.filter(user=u, created_at__year=2026, created_at__month=1, created_at__day__lte=17, created_at__day__gte=16).order_by('created_at').all()
# We expect Jan 17 to correspond to the SECOND record in timeline if iterate?
# Dedup said 790 is Jan 16 UTC.
# Let's filter by ID if possible? No, ID varies.
# Filter by date range strict.
import datetime
start17 = datetime.datetime(2026, 1, 16, 12, 0, tzinfo=datetime.timezone.utc)
end17 = datetime.datetime(2026, 1, 17, 12, 0, tzinfo=datetime.timezone.utc)
r17_obj = HaruOn.objects.filter(user=u, created_at__range=(start17, end17)).first()

if r17_obj:
    print(f"Fixing Jan 17 Record (ID: {r17_obj.id})...")
    # Log Data for Jan 17
    data17 = {
        'ai_comment': '당신의 마음을 이해합니다. 상쾌하고 기분이 한결 가벼워졌다.',
        'sleep_condition': '푹 잤다.',
        'emotion_desc': '상쾌하고 기분이 한결 가벼워졌다.',
        'emotion_meaning': '이 감정이 나에게 어떤 의미인지 생각해보았다.',
        'self_talk': '그래도 오늘 하루 잘 버텼어. 내일은 더 좋을 거야.'
    }
    r17_obj.content = '오랜만에 산책을 다녀왔다.'
    r17_obj.mood_score = 4
    if not r17_obj.analysis_result: r17_obj.analysis_result = {}
    r17_obj.analysis_result.update(data17)
    r17_obj.save()
    print("Jan 17 Fixed.")
else:
    print("Jan 17 Record NOT FOUND.")
