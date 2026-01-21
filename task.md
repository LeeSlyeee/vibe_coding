# Task: iOS 앱 AI 분석 결과 표시 수정

## Status: Completed

## User Objective

- iOS 앱의 'AI 분석' 탭에서 이미 분석 결과가 있는 계정임에도 불구하고, 결과 대신 '새로 분석하기' 버튼이 나타나는 문제를 해결하고자 합니다.

## Solution

- **iOS 클라이언트 수정 (`StatsView.swift`)**:
  - 뷰가 로드될 때(`onAppear`), 기존의 통계 데이터뿐만 아니라 AI 분석 리포트의 상태도 조회하도록 수정했습니다.
  - `fetchExistingReports()` 함수를 새로 추가하여 `/api/analysis/report/status` 엔드포인트를 호출합니다.
  - 분석 상태가 `completed`인 경우, 즉시 리포트 내용을 화면에 표시합니다.

## Changes Implemented

### `StatsView.swift`

- `fetchExistingReports()` 메서드 추가:
  - 단기 리포트와 장기 리포트(Insight)의 상태를 각각 확인.
  - 완료된 리포트가 있으면 상태 변수(`reportContent`, `longTermContent`) 업데이트.
- `onAppear` 수정:
  - `fetchStats()`와 `fetchExistingReports()`를 동시에 실행하도록 변경.

## Verification

1. iOS 앱 실행 및 '마음 분석' 탭 이동.
2. 'AI분석' 탭 선택.
3. 이전에 분석을 수행한 계정이라면, '분석 시작하기' 버튼 대신 분석 결과 텍스트가 바로 표시되어야 함.
