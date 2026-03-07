"""
ADK 사용법 예시 스크립트
========================
Flask 앱 컨텍스트 내에서 ADK 에이전트를 실행하는 방법을 보여줍니다.

실행 방법:
  cd /Users/slyeee/Desktop/DATA/DATA2/vibe_coding/backend
  python adk/example_usage.py
"""

import sys
import os

# backend/ 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
from models import db, User, Diary
from crypto_utils import crypto_manager


def example_1_single_tool():
    """
    ═══ 예시 1: 도구(Tool) 하나만 단독 사용 ═══
    특정 사용자의 시계열 분석만 실행하고 싶을 때
    """
    print("\n" + "=" * 60)
    print("📊 예시 1: TimeseriesAnalysisTool 단독 실행")
    print("=" * 60)

    from adk.tools.kick_tools import TimeseriesAnalysisTool

    tool = TimeseriesAnalysisTool()
    result = tool.execute(user_id=1, db_session=db.session, Diary=Diary)

    print(f"  분석 대상: user_id=1")
    print(f"  플래그 수: {result.get('flag_count', 0)}")
    print(f"  위험 여부: {'⚠️ 위험' if result.get('has_critical') else '✅ 정상'}")

    if result.get('flags'):
        for flag in result['flags']:
            print(f"    - [{flag['severity']}] {flag['message']}")
    else:
        print("    - 감지된 위험 신호 없음")

    return result


def example_2_crisis_agent():
    """
    ═══ 예시 2: 위기감지 에이전트 실행 ═══
    시계열 + 언어분석을 조합하여 위기 등급을 판단
    """
    print("\n" + "=" * 60)
    print("🚨 예시 2: CrisisDetectionAgent 실행")
    print("=" * 60)

    from adk.agents.crisis_agent import CrisisDetectionAgent

    agent = CrisisDetectionAgent()

    # 에이전트에 전달할 실행 맥락(Context)
    context = {
        'user_id': 1,
        'db_session': db.session,
        'Diary': Diary,
        'crypto_decrypt': crypto_manager.decrypt,
    }

    result = agent.run(input_data="user_id=1 위기 분석 요청", context=context)

    print(f"  결과: {result}")

    return result


def example_3_weekly_workflow():
    """
    ═══ 예시 3: 주간 분석 워크플로우 (멀티 에이전트) ═══
    CrisisDetection → WeeklySummary 순서로 연쇄 실행
    """
    print("\n" + "=" * 60)
    print("📅 예시 3: WeeklyAnalysisWorkflow 실행")
    print("=" * 60)

    from adk.workflows.weekly_workflow import WeeklyAnalysisWorkflow

    workflow = WeeklyAnalysisWorkflow()

    context = {
        'db_session': db.session,
        'Diary': Diary,
        'User': User,
        'crypto_decrypt': crypto_manager.decrypt,
    }

    result = workflow.run(user_id=1, context=context)

    print(f"  워크플로우: {result['workflow']}")
    for agent_name, agent_result in result['agent_results'].items():
        status = agent_result['status']
        emoji = "✅" if status == "success" else "❌"
        print(f"    {emoji} {agent_name}: {status}")

    return result


def example_4_batch_workflow():
    """
    ═══ 예시 4: 배치 실행 (전체 사용자 대상) ═══
    모든 사용자에 대해 주간 분석을 한 번에 실행
    향후 Celery Beat 크론 작업으로 연동 가능
    """
    print("\n" + "=" * 60)
    print("🔄 예시 4: WeeklyAnalysisWorkflow 배치 실행")
    print("=" * 60)

    from adk.workflows.weekly_workflow import WeeklyAnalysisWorkflow

    workflow = WeeklyAnalysisWorkflow()

    # DB에서 활성 사용자 ID 목록 조회
    user_ids = [u.id for u in db.session.query(User.id).limit(5).all()]
    print(f"  대상 사용자: {user_ids}")

    context = {
        'db_session': db.session,
        'Diary': Diary,
        'User': User,
        'crypto_decrypt': crypto_manager.decrypt,
    }

    results = workflow.run_batch(user_ids=user_ids, context=context)

    for r in results:
        uid = r['user_id']
        agent_results = r['agent_results']
        crisis = agent_results.get('CrisisDetectionAgent', {})
        print(f"    user_id={uid}: {crisis.get('status', 'N/A')}")

    return results


# ═══════════════════════════════════════════════════════
# 실행
# ═══════════════════════════════════════════════════════
if __name__ == '__main__':
    with app.app_context():
        print("🤖 Maum-On ADK 사용법 예시")
        print("=" * 60)

        # 1. 도구(Tool) 단독 사용
        example_1_single_tool()

        # 2. 에이전트 실행
        example_2_crisis_agent()

        # 3. 워크플로우 (멀티 에이전트)
        example_3_weekly_workflow()

        # 4. 배치 실행
        example_4_batch_workflow()

        print("\n" + "=" * 60)
        print("✅ 모든 예시 실행 완료!")
        print("=" * 60)
