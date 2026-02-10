import os
import django
import json
from datetime import datetime
from django.utils import timezone

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from haru_on.models import HaruOn

User = get_user_model()

def run():
    # Target User
    username = 'slyeee'
    user = User.objects.filter(username=username).first()
    if not user:
        print(f"User {username} not found! Creating...")
        user = User.objects.create(username=username, email='slyeee@example.com')
        user.set_unusable_password()
        user.save()
    
    print(f"Importing data for user: {user.username}")

    try:
        with open('fake_diaries_2026.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("fake_diaries_2026.json not found!")
        return

    count = 0
    for item in data:
        date_str = item.get('date')
        if not date_str: continue

        # Parse Date (Assuming YYYY-MM-DD)
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Create aware datetime for 09:00:00 KST (or just use date)
        # Using timezone.now() replacement for time part
        dt = datetime.combine(target_date, datetime.min.time())
        # Make jump to 9 AM for cleaner timeline if desired, or just use 00:00
        dt = dt.replace(hour=21, minute=0) # Previous day 9PM? No.
        # Let's just set it to 09:00:00 KST roughly (UTC 00:00)
        # But server is KST based now?
        # If server TIME_ZONE='Asia/Seoul', then naive datetime might be interpreted as such if strict mode is off,
        # but better to be explicit.
        # However, since we just fixed the view to use LocalTime, stored time is UTC.
        # So if we want 9 AM KST, we should store 00:00 UTC.
        dt = dt.replace(hour=9, minute=0) 
        created_at = timezone.make_aware(dt)

        # Content construction
        weather = item.get('weather', '')
        sleep = item.get('sleep_condition', '')
        event = item.get('event', '')
        emotion = item.get('emotion', '')
        meaning = item.get('meaning', '')
        selftalk = item.get('self_talk', '')
        medication = item.get('medication_taken', '없음')
        score = item.get('mood_score', 5)

        full_content = f"{event}\n\n[감정: {emotion}]"

        # AI Analysis JSON
        ai_data = {
            "weather": weather,
            "sleep_condition": sleep,
            "emotion_desc": emotion,
            "emotion_meaning": meaning,
            "self_talk": selftalk,
            "medication_taken": medication,
            "ai_prediction": "가상 데이터 생성됨",
            "ai_comment": "꾸준한 기록이 멋집니다!",
            "ai_advice": "오늘도 수고하셨어요.",
            "ai_analysis": meaning
        }

        # Check existing
        # Filter by range to avoid time conflict
        start = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
        end = timezone.make_aware(datetime.combine(target_date, datetime.max.time()))
        
        exists = HaruOn.objects.filter(user=user, created_at__range=(start, end)).exists()
        
        if not exists:
            HaruOn.objects.create(
                user=user,
                content=full_content,
                mood_score=score,
                is_high_risk=(score <= 2),
                analysis_result=ai_data,
                created_at=created_at
            )
            print(f"Created diary for {date_str}")
            count += 1
        else:
            print(f"Skipped {date_str} (Already exists)")

    print(f"Import Complete. Added {count} entries.")

if __name__ == "__main__":
    run()
