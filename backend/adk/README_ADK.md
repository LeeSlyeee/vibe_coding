# 🤖 Maum-On ADK (Agent Development Kit) 아키텍처

> **작성일**: 2026-03-07  
> **태그**: `[ARCH_CHANGE]`  
> **목적**: Google ADK 기반의 멀티 에이전트 시스템 도입을 위한 뼈대(Scaffolding)

---

## 1. 디렉토리 구조

```
backend/adk/
├── README_ADK.md          ← 이 문서
├── __init__.py
│
├── core/                  ← 추상화 베이스 클래스
│   ├── __init__.py
│   └── agent_base.py      (BaseAgent, BaseTool ABC)
│
├── tools/                 ← 에이전트가 호출하는 도구 (기존 로직 래핑)
│   ├── __init__.py
│   ├── data_tools.py       (DiaryFetchTool, UserProfileTool)
│   └── kick_tools.py       (TimeseriesAnalysisTool, LinguisticAnalysisTool,
│                            RelationalAnalysisTool, ConditionTool,
│                            WeeklyLetterTool)
│
├── agents/                ← 단일 목적 에이전트
│   ├── __init__.py
│   ├── summary_agent.py    (WeeklySummaryAgent — PoC)
│   └── crisis_agent.py     (CrisisDetectionAgent — 위기 감지)
│
└── workflows/             ← 멀티 에이전트 오케스트레이션
    ├── __init__.py
    └── weekly_workflow.py   (WeeklyAnalysisWorkflow)
```

## 2. 설계 원칙

### 기존 코드 비파괴 (Zero Side Effect)

- `adk/`는 기존 `app.py`, `celery_app.py`, `tasks.py`에 **아무런 영향을 주지 않는** 독립 모듈입니다.
- `tools/kick_tools.py`는 기존 `kick_analysis/` 하위 함수를 **호출만 할 뿐 수정하지 않습니다.**

### 래핑 패턴 (Thin Wrapper → Delegation)

```
[에이전트] → Tool.execute() → kick_analysis.analyze_timeseries() → 결과 반환
             ↑ ADK 인터페이스       ↑ 기존 코드 그대로
```

### 점진적 통합 (Incremental Migration)

1. **현재**: 독립 PoC 모듈. 프로덕션에 영향 없음.
2. **다음 단계**: Celery 워커에서 ADK workflow를 호출하는 브릿지 코드 작성.
3. **최종 단계**: Celery 태스크를 ADK 에이전트로 완전 교체.

## 3. 에이전트 목록

| 에이전트               | 역할                                     | 사용 도구                                      | 상태         |
| ---------------------- | ---------------------------------------- | ---------------------------------------------- | ------------ |
| `WeeklySummaryAgent`   | 주간 감정 요약 생성                      | (향후 LLM 연동)                                | 🟡 PoC       |
| `CrisisDetectionAgent` | 위기 수준 판단 (green/yellow/orange/red) | TimeseriesAnalysisTool, LinguisticAnalysisTool | 🟢 구현 완료 |

## 4. 도구(Tool) 목록

| 도구                     | 래핑 대상                                                       | 역할                   |
| ------------------------ | --------------------------------------------------------------- | ---------------------- |
| `DiaryFetchTool`         | SQLAlchemy 쿼리                                                 | 사용자 일기 N일치 조회 |
| `UserProfileTool`        | SQLAlchemy 쿼리                                                 | 사용자 프로필 조회     |
| `TimeseriesAnalysisTool` | `kick_analysis.analyze_timeseries()`                            | Phase 1 시계열 분석    |
| `LinguisticAnalysisTool` | `kick_analysis.linguistic.analyze_linguistic()`                 | Phase 2 언어 지문      |
| `RelationalAnalysisTool` | `kick_analysis.relational.analyze_relational()`                 | Phase 3 관계 지형도    |
| `ConditionTool`          | `kick_analysis.condition.generate_condition()`                  | 종합 마음 컨디션       |
| `WeeklyLetterTool`       | `kick_analysis.weekly_letter.generate_weekly_letter_for_user()` | 주간 편지 생성         |

## 5. 워크플로우 목록

| 워크플로우               | 실행 순서                       | 설명                            |
| ------------------------ | ------------------------------- | ------------------------------- |
| `WeeklyAnalysisWorkflow` | CrisisDetection → WeeklySummary | 주간 종합 분석 + 배치 실행 지원 |

## 6. 향후 확장 계획

- [ ] `B2GReportAgent`: 보건소 담당자용 클리니컬 리포트 자동 생성
- [ ] `NotificationAgent`: 위기 등급에 따른 FCM/APNs 알림 자동 트리거
- [ ] Google ADK 정식 SDK 연동 (현재 자체 추상화 → SDK 교체)
- [ ] Celery Beat → ADK Workflow 브릿지 코드 작성

---

> **이 모듈은 기존 프로덕션 파이프라인과 독립적으로 동작합니다.**  
> `app.py`나 `celery_app.py`를 수정하지 않고도 테스트 및 검증이 가능합니다.
