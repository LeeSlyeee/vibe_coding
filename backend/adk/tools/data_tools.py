"""
ADK Tool: 일기 데이터 조회 도구
================================
기존 SQLAlchemy 기반의 일기 조회 로직을 에이전트가 호출 가능한 Tool로 래핑.
기존 모듈(models.py, crypto_utils.py) 의존성을 유지하되,
ADK BaseTool 인터페이스를 통해 호출합니다.
"""

import sys
import os

# backend/ 경로를 sys.path에 추가 (adk/ 하위에서 상위 모듈 참조)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from adk.core.agent_base import BaseTool


class DiaryFetchTool(BaseTool):
    """
    특정 사용자의 일기 목록을 조회하는 도구.
    에이전트가 사용자의 최근 N일치 일기를 가져올 때 사용합니다.
    """
    name = "DiaryFetchTool"
    description = "특정 사용자의 최근 일기 데이터를 DB에서 조회합니다."

    def execute(self, user_id: int, days: int = 7, db_session=None, Diary=None, crypto_decrypt=None) -> List[Dict]:
        """
        Args:
            user_id: 사용자 ID
            days: 조회할 일수 (기본 7일)
            db_session: SQLAlchemy session
            Diary: Diary 모델 클래스
            crypto_decrypt: 복호화 함수 (선택)

        Returns:
            list[dict]: 일기 목록 (날짜, 감정, 내용 포함)
        """
        if db_session is None or Diary is None:
            return []

        today = datetime.utcnow().date()
        start_date = (today - timedelta(days=days)).strftime('%Y-%m-%d')

        diaries = (
            db_session.query(Diary)
            .filter(
                Diary.user_id == user_id,
                Diary.date >= start_date
            )
            .order_by(Diary.date.desc())
            .all()
        )

        results = []
        for d in diaries:
            entry = {
                'id': d.id,
                'date': d.date,
                'mood_level': d.mood_level,
                'emotion': d.emotion,
            }
            # 복호화가 가능하면 텍스트 필드도 포함
            if crypto_decrypt:
                entry['event'] = crypto_decrypt(d.event or '')
                entry['emotion_desc'] = crypto_decrypt(d.emotion_desc or '')
            else:
                entry['event'] = d.event
                entry['emotion_desc'] = d.emotion_desc

            results.append(entry)

        return results


class UserProfileTool(BaseTool):
    """
    사용자의 프로필 정보(이름, 위험도, 센터 정보 등)를 조회하는 도구.
    """
    name = "UserProfileTool"
    description = "사용자의 기본 프로필 정보를 조회합니다."

    def execute(self, user_id: int, db_session=None, User=None) -> Optional[Dict]:
        """
        Args:
            user_id: 사용자 ID
            db_session: SQLAlchemy session
            User: User 모델 클래스

        Returns:
            dict or None: 사용자 프로필 정보
        """
        if db_session is None or User is None:
            return None

        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        return {
            'id': user.id,
            'username': user.username,
            'real_name': getattr(user, 'real_name', None),
            'risk_level': getattr(user, 'risk_level', 1),
            'center_code': getattr(user, 'center_code', None),
        }
