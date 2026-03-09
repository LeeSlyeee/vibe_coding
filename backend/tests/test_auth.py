import json
from models import db, User
from werkzeug.security import generate_password_hash

def test_health_check(client):
    """서버 헬스체크 API 테스트"""
    response = client.get('/api')
    assert response.status_code == 200
    assert b"\"" not in response.data  # plain string response

def test_register_and_login(client, app):
    """회원가입 및 로그인 통합 흐름 테스트"""
    
    # 1. 회원가입 테스트
    reg_data = {
        'username': 'testuser1',
        'password': 'testpassword123',
        'nickname': 'Tester'
    }
    res_reg = client.post('/api/register', json=reg_data)
    assert res_reg.status_code == 201
    
    with app.app_context():
        user = User.query.filter_by(username='testuser1').first()
        assert user is not None
        assert user.nickname == 'Tester'

    # 2. 중복 가입 방지 테스트
    res_reg_dup = client.post('/api/register', json=reg_data)
    assert res_reg_dup.status_code == 400

    # 3. 로그인 테스트
    login_data = {
        'username': 'testuser1',
        'password': 'testpassword123'
    }
    res_login = client.post('/api/login', json=login_data)
    assert res_login.status_code == 200
    
    data = res_login.get_json()
    assert 'access_token' in data
    assert data['user']['username'] == 'testuser1'
    
    # 토큰 검증 테스트
    token = data['access_token']
    res_me = client.get('/api/user/me', headers={'Authorization': f'Bearer {token}'})
    assert res_me.status_code == 200
    
    me_data = res_me.get_json()
    assert me_data['username'] == 'testuser1'
