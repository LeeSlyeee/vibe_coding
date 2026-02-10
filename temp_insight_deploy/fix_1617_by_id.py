from haru_on.models import HaruOn

def update_record(rid, data_dict):
    try:
        r = HaruOn.objects.get(id=rid)
        print(f"Updating ID {rid} (Current Date: {r.created_at})")
        r.content = '오랜만에 산책을 다녀왔다.'
        r.mood_score = 4
        if not r.analysis_result: r.analysis_result = {}
        for k, v in data_dict.items():
            r.analysis_result[k] = v
        r.save()
        print(f"Updated ID {rid} successfully with keys: {list(data_dict.keys())}")
        # Verify
        print(f"  Emot: {r.analysis_result.get('emotion_desc')}")
        print(f"  Sleep: {r.analysis_result.get('sleep_condition')}")
    except Exception as e:
        print(f"Failed to update ID {rid}: {e}")

# Data for Jan 16 (ID 791)
data16 = {
    'ai_comment': '당신의 마음을 이해합니다. 상쾌하고 기분이 한결 가벼워졌다.',
    'sleep_condition': '중간에 깼다.', # Unique to Jan 16
    'emotion_desc': '상쾌하고 기분이 한결 가벼워졌다.',
    'emotion_meaning': '이 감정이 나에게 어떤 의미인지 생각해보았다.',
    'self_talk': '그래도 오늘 하루 잘 버텼어. 내일은 더 좋을 거야.',
    'medication_taken': False
}

# Data for Jan 17 (ID 790)
data17 = {
    'ai_comment': '당신의 마음을 이해합니다. 상쾌하고 기분이 한결 가벼워졌다.',
    'sleep_condition': '푹 잤다.', # Unique to Jan 17
    'emotion_desc': '상쾌하고 기분이 한결 가벼워졌다.',
    'emotion_meaning': '이 감정이 나에게 어떤 의미인지 생각해보았다.',
    'self_talk': '그래도 오늘 하루 잘 버텼어. 내일은 더 좋을 거야.',
    'medication_taken': False
}

update_record(791, data16)
update_record(790, data17)
