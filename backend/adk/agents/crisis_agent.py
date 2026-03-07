"""
ADK Agent: 위기 감지 에이전트
================================
Phase 1(시계열)과 Phase 2(언어지문) 결과를 조합하여
사용자의 위기 수준을 판단하고, 필요 시 알림 트리거를 생성하는 에이전트.

향후 B2G 보건소 연동 시, 이 에이전트의 결과가
보건소 담당자 대시보드에 자동 리포트로 전달될 수 있습니다.
"""

from typing import Dict, Any, List
from adk.core.agent_base import BaseAgent
from adk.tools.kick_tools import TimeseriesAnalysisTool, LinguisticAnalysisTool


class CrisisDetectionAgent(BaseAgent):
    """
    위기 감지 에이전트.
    시계열 분석과 언어 지문 분석 도구를 조합하여
    사용자의 위기 수준을 판단합니다.
    """
    def __init__(self):
        tools = [TimeseriesAnalysisTool(), LinguisticAnalysisTool()]
        super().__init__(
            name="CrisisDetectionAgent",
            description="시계열/언어 분석을 통합하여 사용자 위기 수준을 판단합니다.",
            tools=tools
        )

    def run(self, input_data: str, context: Dict[str, Any] = None) -> str:
        """
        [ADK 에이전트 실행 루프]

        현재 구현: 도구를 순차 실행하고 규칙 기반으로 위기 등급을 산출합니다.
        향후 구현: LLM 기반 ReAct 패턴으로 동적 판단 가능.

        Args:
            input_data: 분석 요청 내용 (자연어 또는 user_id 문자열)
            context: 실행 맥락 (db_session, Diary, user_id, crypto_decrypt 등)

        Returns:
            str: 위기 판단 결과 메시지 (JSON 직렬화 가능)
        """
        if context is None:
            return '{"error": "context가 필요합니다 (db_session, Diary, user_id)."}'

        user_id = context.get('user_id')
        db_session = context.get('db_session')
        Diary = context.get('Diary')
        crypto_decrypt = context.get('crypto_decrypt')

        if not all([user_id, db_session, Diary]):
            return '{"error": "user_id, db_session, Diary가 context에 필요합니다."}'

        # 1단계: Phase 1 시계열 분석 실행
        ts_tool = self.tools[0]  # TimeseriesAnalysisTool
        ts_result = ts_tool.execute(user_id=user_id, db_session=db_session, Diary=Diary)

        # 2단계: Phase 2 언어 지문 분석 실행
        lg_tool = self.tools[1]  # LinguisticAnalysisTool
        lg_result = lg_tool.execute(
            user_id=user_id, db_session=db_session, Diary=Diary,
            crypto_decrypt=crypto_decrypt
        )

        # 3단계: 규칙 기반 위기 판단
        crisis_level = self._evaluate_crisis(ts_result, lg_result)

        return str({
            'user_id': user_id,
            'crisis_level': crisis_level['level'],
            'crisis_label': crisis_level['label'],
            'ts_flags': ts_result.get('flag_count', 0),
            'lg_flags': lg_result.get('flag_count', 0),
            'summary': crisis_level['summary'],
        })

    def _evaluate_crisis(self, ts_result: Dict, lg_result: Dict) -> Dict[str, str]:
        """
        시계열 + 언어 분석 결과를 종합하여 위기 등급을 산출합니다.

        등급 체계:
          - green  (안전): 플래그 없음
          - yellow (관찰): 단일 Phase에서 플래그 1~2개
          - orange (주의): 두 Phase 모두 플래그 있음
          - red    (위기): critical 플래그 존재 또는 복합 고위험
        """
        ts_flags = ts_result.get('flag_count', 0)
        ts_critical = ts_result.get('has_critical', False)
        lg_flags = lg_result.get('flag_count', 0)

        total_flags = ts_flags + lg_flags

        if ts_critical or total_flags >= 4:
            return {
                'level': 'red',
                'label': '위기',
                'summary': f'복합 위험 신호 감지. 시계열 {ts_flags}건 + 언어 {lg_flags}건. 즉시 관심 필요.'
            }
        elif ts_flags > 0 and lg_flags > 0:
            return {
                'level': 'orange',
                'label': '주의',
                'summary': f'두 영역에서 신호 감지. 시계열 {ts_flags}건 + 언어 {lg_flags}건. 지속 모니터링 필요.'
            }
        elif total_flags > 0:
            return {
                'level': 'yellow',
                'label': '관찰',
                'summary': f'단일 영역에서 신호 감지. 총 {total_flags}건. 추이 관찰 중.'
            }
        else:
            return {
                'level': 'green',
                'label': '안전',
                'summary': '현재 위험 신호 없음. 정상 범위.'
            }
