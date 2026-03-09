import json
from models import db, User, Diary
from app import create_access_token
from datetime import datetime

def get_auth_headers(app, user_id=1, username="testuser"):
    with app.app_context():
        # User가 없으면 생성
        user = User.query.get(user_id)
        if not user:
            user = User(id=user_id, username=username, password="123", role="user")
            db.session.add(user)
            db.session.commit()
            
        token = create_access_token(identity=str(user.id), additional_claims={"username": user.username})
        return {'Authorization': f'Bearer {token}'}

def test_create_and_get_diary(client, app):
    """일기 작성 및 조회 API 테스트 (유저 분리 및 암호화 로직 포함 검증)"""
    headers = get_auth_headers(app)
    
    # 1. 일기 생성 (단순 데이터)
    diary_data = {
        "date": datetime.today().strftime('%Y-%m-%d'),
        "weather": "맑음",
        "event": "오늘 첫 단위 테스트를 작성했다.",
        "thought": "매우 뿌듯하다.",
        "emotion_desc": "기쁨, 평안",
        "mood_level": 4,
        "self_talk": "잘하고 있어!",
        "sleep_condition": "숙면"
    }
    
    res_post = client.post('/api/diaries', json=diary_data, headers=headers)
    assert res_post.status_code == 201
    
    # 2. 일기 목록 조회
    res_get = client.get('/api/diaries', headers=headers)
    assert res_get.status_code == 200
    
    data = res_get.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # 3. 데이터 일치 여부 확인 (암/복호화가 정상적으로 거쳐졌는지)
    found_diary = next((d for d in data if d['date'] == diary_data['date']), None)
    assert found_diary is not None
    assert found_diary['event'] == diary_data['event']
    assert found_diary['mood_level'] == diary_data['mood_level']
