import pytest
import os
import sys

# 상위 디렉토리를 sys.path에 추가
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, base_path)

# 테스트 시 환경변수로 DB를 in-memory SQLite로 강제 설정 (app.py 모듈 초기화 에러 방지)
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import app as flask_app
from models import db

@pytest.fixture
def app():
    """테스트용 Flask 앱 인스턴스"""
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-secret-key-1234',
        'WTF_CSRF_ENABLED': False
    })
    
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """테스트용 HTTP 클라이언트"""
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
