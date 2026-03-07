"""
ADK Tool: Kick 분석 파이프라인 도구
=====================================
기존 kick_analysis/ 하위 모듈의 분석 함수들을 ADK Tool 인터페이스로 래핑.
기존 코드를 수정하지 않고, 함수 호출을 위임(Delegation)하는 얇은 래퍼(Thin Wrapper)입니다.

래핑 대상:
  - Phase 1: analyze_timeseries          (시계열 패턴 감지)
  - Phase 2: analyze_linguistic           (언어 지문 분석)
  - Phase 3: analyze_relational           (관계 지형도)
  - 종합:    generate_condition           (마음 컨디션 산출)
  - 편지:    generate_weekly_letter_for_user (주간 편지 생성)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from typing import Any, Dict
from adk.core.agent_base import BaseTool


class TimeseriesAnalysisTool(BaseTool):
    """
    Phase 1: 시계열 패턴 감지 (미기록, 빈도 변화, 마음온도 추세, 새벽 기록)
    기존 함수: kick_analysis.analyze_timeseries()
    """
    name = "TimeseriesAnalysisTool"
    description = "사용자의 일기 기록 패턴(미기록, 빈도, 마음온도 추세)을 시계열로 분석합니다."

    def execute(self, user_id: int, db_session=None, Diary=None, today=None) -> Dict[str, Any]:
        from kick_analysis import analyze_timeseries
        return analyze_timeseries(user_id, db_session, Diary, today=today)


class LinguisticAnalysisTool(BaseTool):
    """
    Phase 2: 언어 지문 분석 (어휘 다양성, 문장 복잡도, 자기참조 비율)
    기존 함수: kick_analysis.linguistic.analyze_linguistic()
    """
    name = "LinguisticAnalysisTool"
    description = "사용자의 언어 패턴(어휘 다양성, 문장 구조 변화)을 Kiwi 형태소 분석기로 분석합니다."

    def execute(self, user_id: int, db_session=None, Diary=None,
                crypto_decrypt=None, today=None) -> Dict[str, Any]:
        from kick_analysis.linguistic import analyze_linguistic
        return analyze_linguistic(user_id, db_session, Diary,
                                  crypto_decrypt=crypto_decrypt, today=today)


class RelationalAnalysisTool(BaseTool):
    """
    Phase 3: 관계 지형도 (인물 추출, 인물-감정 매핑, 사회적 밀도)
    기존 함수: kick_analysis.relational.analyze_relational()
    """
    name = "RelationalAnalysisTool"
    description = "사용자 일기에서 등장 인물을 추출하고 인물별 감정 관계를 분석합니다."

    def execute(self, user_id: int, db_session=None, Diary=None,
                crypto_decrypt=None, today=None) -> Dict[str, Any]:
        from kick_analysis.relational import analyze_relational
        return analyze_relational(user_id, db_session, Diary,
                                  crypto_decrypt=crypto_decrypt, today=today)


class ConditionTool(BaseTool):
    """
    마음 컨디션 종합 산출 (Phase 1~3 교차 분석 → 0~100 점수 + 등급/메시지)
    기존 함수: kick_analysis.condition.generate_condition()
    """
    name = "ConditionTool"
    description = "Phase 1~3 분석 결과를 교차 분석하여 종합 마음 컨디션 점수와 등급을 산출합니다."

    def execute(self, user_id: int, db_session=None, Diary=None,
                crypto_decrypt=None, today=None, skip_phase3: bool = False) -> Dict[str, Any]:
        from kick_analysis.condition import generate_condition
        return generate_condition(user_id, db_session, Diary,
                                  crypto_decrypt=crypto_decrypt,
                                  today=today, skip_phase3=skip_phase3)


class WeeklyLetterTool(BaseTool):
    """
    AI 주간 편지 생성 (Ollama LLM 호출 포함)
    기존 함수: kick_analysis.weekly_letter.generate_weekly_letter_for_user()
    """
    name = "WeeklyLetterTool"
    description = "사용자의 지난 1주일 데이터를 기반으로 AI 주간 편지를 생성합니다."

    def execute(self, user_id: int, db_session=None, User=None, Diary=None,
                crypto_decrypt=None, target_date=None) -> Dict[str, Any]:
        from kick_analysis.weekly_letter import generate_weekly_letter_for_user
        return generate_weekly_letter_for_user(
            user_id, db_session, User, Diary,
            crypto_decrypt=crypto_decrypt, target_date=target_date
        )
