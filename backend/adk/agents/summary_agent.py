from typing import List, Dict, Any
from adk.core.agent_base import BaseAgent

class WeeklySummaryAgent(BaseAgent):
    """
    사용자의 일주일치 일기 데이터를 기반으로 주간 감정 요약을 생성하는 에이전트.
    향후 Celery의 generate_weekly_letter_for_user 태스크를 대체하기 위한 PoC 클래스.
    """
    def __init__(self):
        super().__init__(
            name="WeeklySummaryAgent",
            description="Analyzes a week of diary entries and generates a clinical summary."
        )

    def run(self, input_data: str, context: Dict[str, Any] = None) -> str:
        """
        [ADK 구현 예정 구역]
        1. Context에서 user_id 추출
        2. tools에 등록된 DiaryFetchTool 을 통해 최근 7일치 일기 로드
        3. LLM 프롬프트 조립 및 호출
        4. 결과 반환
        """
        # TODO: 실제 Google ADK의 컴포넌트나 커스텀 LLM 호출 추상화 로직 연결
        return "[Scaffold] 주간 감정 분석 및 요약 결과가 반환될 자리입니다."
