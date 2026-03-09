import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import app
from models import db, User, Diary
from datetime import datetime
from crypto_utils import crypto_manager
from analysis_worker import start_analysis_thread

with app.app_context():
    # 1. tester 계정 찾기
    user = User.query.filter_by(username='tester').first()
    if not user:
        print('tester user not found')
        sys.exit(1)
        
    print(f'Found user: {user.username} (ID: {user.id})')
    
    # 2. 가상 일기 생성 (실감나는 내용으로 작성!)
    test_content = '오늘은 주말이라 늦잠을 잤다. 일어나서 창문을 열었는데 햇살이 너무 포근해서 기분이 좋았다. 오랜만에 요리도 해먹고 좋아하는 넷플릭스 드라마를 보면서 푹 쉬었더니 한 주간의 스트레스가 다 날아간 것 같다.'
    
    enc_event = crypto_manager.encrypt(test_content)
    enc_emotion_desc = crypto_manager.encrypt('편안함, 만족스러움')
    enc_sleep = crypto_manager.encrypt('아주 잘 잠 (10시간)')
    enc_self_talk = crypto_manager.encrypt('이런 여유로운 주말이 있어서 참 다행이야')
    
    new_diary = Diary(
        user_id=user.id,
        created_at=datetime.utcnow(),
        date=datetime.utcnow().strftime('%Y-%m-%d'),
        event=enc_event,
        emotion_desc=enc_emotion_desc,
        sleep_condition=enc_sleep,
        emotion_meaning=enc_self_talk,
        mood_intensity=5,
        # mood_score 필드는 구 버전과 호환을 위해 제거
        safety_flag=False
    )
    
    db.session.add(new_diary)
    db.session.commit()
    diary_id = new_diary.id
    
    print(f'✅ Created test diary ID: {diary_id}')
    
    # 3. AI 분석 워커 즉시 실행
    # start_analysis_thread 함수 내부에서 분석이 끝나면 자동으로 notify_guardians_ai_report 함수가 호출됨
    print('🚀 Starting analysis worker...')
    start_analysis_thread(
        diary_id=diary_id, 
        date=datetime.utcnow().strftime('%Y-%m-%d'),
        event='테스트 가상 일기 작성',
        sleep='아주 잘 잠 (10시간)',
        emotion_desc='편안함, 만족스러움',
        emotion_meaning='이런 여유로운 주말이 있어서 참 다행이야',
        self_talk='나 자신에게 주는 휴식'
    )
    
    print('✨ Analysis dispatched! Wait about 5-10 seconds for the push notification to arrive on the guardian device.')
    
    # 워커가 별도 스레드에서 돌기 때문에 즉시 종료되지 않도록 살짝 대기
    time.sleep(3)
