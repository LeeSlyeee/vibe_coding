
import random
from datetime import datetime, timedelta
from app import app, db
from models import User, Diary
from sqlalchemy import func

def create_dummy_data():
    with app.app_context():
        # 1. Get User
        user = User.query.first()
        if not user:
            print("No user found. Creating 'testuser'...")
            user = User(username='testuser')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            print(f"Created user: {user.username} (ID: {user.id})")
        else:
            print(f"Using existing user: {user.username} (ID: {user.id})")

        # 2. Config
        COUNT = 1000
        END_DATE = datetime(2026, 1, 10)
        START_DATE = datetime(2025, 1, 1) # Generate from 2025
        
        # 3. Dummy Texts
        events = [
            "오늘은 친구와 맛집을 갔다.", "회사에서 중요한 프로젝트를 끝냈다.", "집에서 하루종일 넷플릭스를 봤다.",
            "오랜만에 운동을 하러 헬스장에 갔다.", "길가다 귀여운 고양이를 마주쳤다.", "비가 와서 기분이 좀 차분해졌다.",
            "새로운 카페를 발견해서 커피를 마셨다.", "부모님께 안부 전화를 드렸다.", "책을 읽으며 여유로운 시간을 보냈다.",
            "밤늦게까지 야근을 해서 피곤했다.", "주말이라 늦잠을 잤다.", "친구들과 술 한잔 하며 회포를 풀었다."
        ]
        moods = [1, 2, 3, 4, 5]
        
        print(f"Generating {COUNT} dummy entries...")
        
        new_entries = []
        for i in range(COUNT):
            # Random Date
            days_range = (END_DATE - START_DATE).days
            random_days = random.randint(0, days_range - 1)
            date = START_DATE + timedelta(days=random_days)
            # Add random time
            date = date.replace(hour=random.randint(6, 23), minute=random.randint(0, 59))

            # Random Content
            event = random.choice(events)
            mood = random.choice(moods)
            
            emotion_mapping = {
                5: ("행복해", "기분이 정말 날아갈 것 같았다.", "성취감과 기쁨"),
                4: ("평온해", "마음이 잔잔하고 편안했다.", "안정과 휴식"),
                3: ("그저그래", "특별한 감정은 없었다.", "무덤덤함"),
                2: ("우울해", "기분이 축 처지고 힘들었다.", "슬픔과 무기력"),
                1: ("화가나", "짜증이 나고 답답했다.", "분노와 스트레스")
            }
            
            label, desc, meaning = emotion_mapping.get(mood, ("그저그래", "보통", "보통"))
            
            entry = Diary(
                user_id=user.id,
                event=event,
                emotion_desc=desc,
                emotion_meaning=meaning,
                self_talk=f"오늘 하루도 수고했어. 내일은 더 좋은 날이 될 거야.",
                mood_level=mood,
                ai_prediction=f"{label} ({random.randint(70, 99)}%)", # Dummy Prediction
                ai_comment="당신의 하루를 응원합니다! (Dummy AI)",
                created_at=date
            )
            new_entries.append(entry)
            
            if len(new_entries) % 100 == 0:
                print(f"Prepared {len(new_entries)} entries...")

        # Bulk Insert
        db.session.add_all(new_entries)
        db.session.commit()
        print(f"Successfully added {COUNT} dummy entries!")

if __name__ == "__main__":
    create_dummy_data()
