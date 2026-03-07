from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseTool(ABC):
    """
    ADK 환경에서 에이전트가 호출할 수 있는 도구의 기본 클래스.
    """
    name: str = "BaseTool"
    description: str = "도구에 대한 설명입니다."

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        pass


class BaseAgent(ABC):
    """
    ADK 기반 에이전트의 추상화 클래스.
    특정 목적을 가진 에이전트(예: 요약, 분석)는 이 클래스를 상속받습니다.
    """
    def __init__(self, name: str, description: str, tools: Optional[List[BaseTool]] = None):
        self.name = name
        self.description = description
        self.tools = tools or []

    @abstractmethod
    def run(self, input_data: str, context: Dict[str, Any] = None) -> str:
        """
        에이전트의 메인 실행 루프입니다.
        내부적으로 LLM 호출 및 tool 사용(ReAct 패턴 등)을 오케스트레이션합니다.
        """
        pass
