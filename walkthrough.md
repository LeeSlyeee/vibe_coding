# 웹-앱 일기 동기화 개선 (Web-App Sync Fix)

## 문제 상황 (Issue)

1. **웹(Web)**에서 일기를 작성한 후, **iOS 앱**을 열었을 때 해당 일기가 바로 보이지 않음.
2. 앱이 이미 백그라운드에 실행 중인 경우, 다시 열어도 데이터가 갱신되지 않음 (새로고침 트리거 부재).

## 해결 방법 (Solution)

### 1. 앱 활성화 시 자동 동기화 (Auto-Sync on Active)

- **파일**: `ios_app/AppMainTabView.swift`
- **내용**: 앱이 백그라운드에서 포그라운드(활성 상태)로 돌아올 때마다 `scenePhase` 변화를 감지하여 자동으로 서버와 동기화를 수행하도록 수정했습니다.
  ```swift
  .onChange(of: scenePhase) { newPhase in
      if newPhase == .active && authManager.isAuthenticated {
          LocalDataManager.shared.syncWithServer() // 자동 동기화
      }
  }
  ```
- **사용자 경험(UX)**: 별도의 버튼 조작 없이, 앱을 켜면 자동으로 최신 데이터가 반영됩니다.

## 동작 흐름 (Workflow)

1. **웹 작성**: 웹에서 일기를 작성하고 저장합니다.
2. **앱 실행/전환**:
   - 앱을 새로 켜거나, 백그라운드에서 다시 열면 **즉시 자동 동기화**가 시작됩니다.
   - 캘린더 화면이 자동으로 갱신되어 작성한 일기가 표시됩니다.

## 배포 및 적용 (Deployment)

- iOS 앱 코드가 수정되었으므로, **NodeJS/Vite 서버 재배포는 필요 없으나**, iOS 앱을 Xcode에서 다시 빌드하여 설치해야 변경 사항이 적용됩니다.
