"""
ADK Workflow: 주간 분석 오케스트레이션
========================================
여러 에이전트를 순차적으로 실행하여 사용자의 주간 종합 분석을 수행합니다.

실행 순서:
  1. CrisisDetectionAgent  → 위기 수준 판단
  2. WeeklySummaryAgent     → 주간 감정 요약 (향후 LLM 연동)
  3. (향후) B2GReportAgent  → 보건소 담당자용 리포트 자동 생성

이 워크플로우는 현재 Celery 태스크(tasks.py)의 흐름을 에이전트 패턴으로
재구성한 설계도(Blueprint)입니다.
기존 Celery 파이프라인을 대체하지 않으며, 병렬 운용이 가능합니다.
"""

from typing import Dict, Any, List
from adk.agents.crisis_agent import CrisisDetectionAgent
from adk.agents.summary_agent import WeeklySummaryAgent


class WeeklyAnalysisWorkflow:
    """
    주간 분석 오케스트레이션 워크플로우.
    복수의 에이전트를 순차적으로 실행하고 결과를 통합합니다.
    """
    def __init__(self):
        self.agents = [
            CrisisDetectionAgent(),
            WeeklySummaryAgent(),
        ]

    def run(self, user_id: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        주간 분석 워크플로우를 실행합니다.

        Args:
            user_id: 대상 사용자 ID
            context: 공유 실행 맥락 (db_session, Diary, User, crypto_decrypt 등)

        Returns:
            dict: 각 에이전트의 실행 결과를 통합한 딕셔너리
        """
        context['user_id'] = user_id
        results = {}

        for agent in self.agents:
            try:
                result = agent.run(input_data=str(user_id), context=context)
                results[agent.name] = {
                    'status': 'success',
                    'output': result,
                }
                print(f"✅ [ADK Workflow] {agent.name} 완료")
            except Exception as e:
                results[agent.name] = {
                    'status': 'error',
                    'error': str(e),
                }
                print(f"❌ [ADK Workflow] {agent.name} 실패: {e}")

        return {
            'user_id': user_id,
            'workflow': 'WeeklyAnalysisWorkflow',
            'agent_results': results,
        }

    def run_batch(self, user_ids: List[int], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        여러 사용자에 대해 배치로 주간 분석을 실행합니다.
        향후 Celery Beat에서 주기적으로 호출하는 구조로 연동 가능합니다.

        Args:
            user_ids: 대상 사용자 ID 목록
            context: 공유 실행 맥락

        Returns:
            list[dict]: 각 사용자별 실행 결과
        """
        results = []
        for uid in user_ids:
            result = self.run(user_id=uid, context=context)
            results.append(result)
        return results
