import unittest
import os
import sys

# 상위 디렉토리를 sys.path에 추가하여 app.py import 보장
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import app
from models import db

class BasicAppTestCase(unittest.TestCase):
    """
    핵심 서버 상태 및 Blueprint 등록 상태를 검증하는 가장 기본적인 통합 테스트
    """

    def setUp(self):
        # 테스트 클라이언트 설정
        app.config['TESTING'] = True
        # 테스트용 in-memory DB (기존 DB 영향 주지 않음)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_health_check(self):
        """서버가 정상적으로 켜져서 /api 헬스체크 응답을 주는지 검증"""
        response = self.app.get('/api')
        self.assertEqual(response.status_code, 200)
        self.assertIn("서버가 정상 작동 중입니다", response.data.decode('utf-8'))

    def test_unknown_route(self):
        """존재하지 않는 경로 호출 시 404 리턴 확인"""
        response = self.app.get('/api/unknown/route/123')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
