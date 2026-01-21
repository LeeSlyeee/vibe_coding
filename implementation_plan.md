# 구현 계획: iOS 앱 AI 분석 결과 표시 로직 수정

## 목표

- 사용자가 iOS 앱의 통계(StatsView) 탭에 진입했을 때, 이미 생성된 AI 분석 결과가 있다면 '분석 시작' 버튼 대신 결과 내용을 바로 보여줍니다.

## 문제 상황

- 현재 `StatsView`는 진입 시 `/api/statistics`만 호출하여 통계 데이터만 가져옵니다.
- AI 리포트(`/api/analysis/report`)는 '분석 시작' 버튼을 눌러야만 생성/조회 로직이 시작됩니다.
- 따라서 이미 분석을 완료한 사용자라도 앱을 껐다 켜거나 탭을 이동하면 다시 '분석 시작' 화면이 나옵니다.

## 구현 상세

### 1. `StatsView.swift` 수정

- **`fetchExistingReports` 함수 추가**:
  - GET `/api/analysis/report/status`: 단기 분석(심층 리포트) 상태 확인
  - GET `/api/analysis/report/longterm/status`: 장기 분석(메타 분석) 상태 확인
  - 각 API 응답의 `status`가 `"completed"`인 경우, `reportContent` 및 `longTermContent` 상태 변수를 업데이트.

- **`onAppear` 로직 변경**:
  - 기존 `perform: fetchStats` 방식에서 클로저 블록 `{ fetchStats(); fetchExistingReports() }`으로 변경하여 두 함수를 모두 실행.

## 기대 효과

- 사용자는 자신의 AI 분석 결과를 다시 분석할 필요 없이 즉시 확인할 수 있습니다.
- 앱의 사용자 경험(UX)이 개선됩니다.
