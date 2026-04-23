# 🤖 마음온(Maum-On) Android 앱 구현 계획서

> 작성일: 2026-02-24
> 방식: Kotlin Native (Android Studio)

---

## 📱 프로젝트 개요

기존 iOS(Swift) 앱과 동등한 기능을 갖춘 Android 네이티브 앱을 구축합니다.
백엔드(Flask API)는 기존 서버(217.142.253.35)를 그대로 사용합니다.

---

## 🏗 기술 스택

| 영역             | 기술                                     |
| ---------------- | ---------------------------------------- |
| 언어             | Kotlin                                   |
| UI 프레임워크    | Jetpack Compose (선언형 UI)              |
| 네트워크         | Retrofit2 + OkHttp (JWT 인터셉터)        |
| 로컬 DB          | Room (SQLite ORM)                        |
| DI (의존성 주입) | Hilt                                     |
| 온디바이스 AI    | Google AI Edge (MediaPipe LLM Inference) |
| 음성 녹음        | Android MediaRecorder                    |
| 상태 관리        | ViewModel + StateFlow                    |
| 네비게이션       | Jetpack Navigation Compose               |
| 빌드             | Gradle (Kotlin DSL)                      |
| 최소 SDK         | API 26 (Android 8.0)                     |
| 타겟 SDK         | API 34 (Android 14)                      |

---

## 📋 iOS → Android 기능 매핑

### Phase 1: 핵심 기능 (MVP) — 1~2주

| #   | iOS 파일                   | 기능               | Android 대응                |
| --- | -------------------------- | ------------------ | --------------------------- |
| 1   | `AppLoginView.swift`       | 로그인/회원가입    | `LoginScreen.kt`            |
| 2   | `AppMainTabView.swift`     | 메인 탭 네비게이션 | `MainScreen.kt` + BottomNav |
| 3   | `MoodCalendarView.swift`   | 감정 캘린더        | `CalendarScreen.kt`         |
| 4   | `AppDiaryWriteView.swift`  | AI 채팅 일기 작성  | `DiaryWriteScreen.kt`       |
| 5   | `AppDiaryDetailView.swift` | 일기 상세 보기     | `DiaryDetailScreen.kt`      |
| 6   | `APIService.swift`         | API 통신           | `ApiService.kt` (Retrofit)  |
| 7   | `AuthManager.swift`        | 인증 관리          | `AuthManager.kt`            |
| 8   | `LocalDataManager.swift`   | 로컬 데이터 관리   | `LocalRepository.kt` (Room) |
| 9   | `Diary.swift`              | 데이터 모델        | `Diary.kt` (data class)     |

### Phase 2: 확장 기능 — 2~3주

| #   | iOS 파일                  | 기능           | Android 대응           |
| --- | ------------------------- | -------------- | ---------------------- |
| 10  | `AppStatsView.swift`      | 통계/분석      | `StatsScreen.kt`       |
| 11  | `AppShareView.swift`      | 가족 공유      | `ShareScreen.kt`       |
| 12  | `SharedStatsView.swift`   | 공유 통계 보기 | `SharedStatsScreen.kt` |
| 13  | `ShareManager.swift`      | 공유 관리자    | `ShareRepository.kt`   |
| 14  | `AppSettingsView.swift`   | 설정           | `SettingsScreen.kt`    |
| 15  | `AppAssessmentView.swift` | 심리 평가      | `AssessmentScreen.kt`  |
| 16  | `B2GManager.swift`        | B2G 연동       | `B2GManager.kt`        |
| 17  | `AppEmergencyView.swift`  | 긴급 도움      | `EmergencyScreen.kt`   |
| 18  | `VoiceRecorder.swift`     | 음성 녹음      | `VoiceRecorder.kt`     |

### Phase 3: 온디바이스 AI — 3~4주

| #   | iOS 파일            | 기능           | Android 대응                |
| --- | ------------------- | -------------- | --------------------------- |
| 19  | `LLMService.swift`  | 온디바이스 LLM | `LLMService.kt` (MediaPipe) |
| 20  | `AppChatView.swift` | AI 채팅 UI     | `ChatScreen.kt`             |

---

## 📂 프로젝트 구조 (예정)

```
android_app/
├── app/
│   ├── src/main/
│   │   ├── java/com/maumon/app/
│   │   │   ├── ui/
│   │   │   │   ├── login/         # 로그인 화면
│   │   │   │   ├── calendar/      # 캘린더 화면
│   │   │   │   ├── diary/         # 일기 작성/상세
│   │   │   │   ├── stats/         # 통계
│   │   │   │   ├── share/         # 공유
│   │   │   │   ├── settings/      # 설정
│   │   │   │   ├── chat/          # AI 채팅
│   │   │   │   └── components/    # 공통 컴포넌트
│   │   │   ├── data/
│   │   │   │   ├── api/           # Retrofit API
│   │   │   │   ├── local/         # Room DB
│   │   │   │   ├── model/         # 데이터 모델
│   │   │   │   └── repository/    # Repository 패턴
│   │   │   ├── di/                # Hilt 모듈
│   │   │   ├── ai/               # 온디바이스 AI
│   │   │   └── util/             # 유틸리티
│   │   └── res/                   # 리소스 (레이아웃, 아이콘 등)
│   └── build.gradle.kts
├── build.gradle.kts
└── settings.gradle.kts
```

---

## 🚀 진행 단계

### Step 0: 환경 설정

- [ ] Android Studio 설치
- [ ] Android SDK 설치 (API 34)
- [ ] 에뮬레이터 설정

### Step 1: 프로젝트 생성

- [ ] Jetpack Compose 프로젝트 초기화
- [ ] Gradle 의존성 설정 (Retrofit, Room, Hilt, Navigation)
- [ ] 디자인 시스템 (색상, 타이포그래피, 테마)

### Step 2: Phase 1 개발 (MVP)

- [ ] 로그인/회원가입
- [ ] 메인 탭 구조
- [ ] 캘린더 (감정 이모지 표시)
- [ ] 일기 작성 (서버 AI 연동)
- [ ] 일기 상세 보기

### Step 3: Phase 2 개발 (확장)

- [ ] 통계/분석
- [ ] 가족 공유
- [ ] 설정
- [ ] B2G 연동
- [ ] 음성 녹음

### Step 4: Phase 3 개발 (AI)

- [ ] MediaPipe LLM 통합
- [ ] Gemma 4 모델 번들링
- [ ] 하이브리드 AI (온디바이스 + 서버 폴백)

### Step 5: 배포

- [ ] Google Play Console 등록
- [ ] 내부 테스트 (Internal Testing)
- [ ] 비공개 테스트 → 공개 출시

---

## ⚠️ 주의사항

1. **Android Studio가 아직 미설치**되어 있으므로 먼저 설치 필요
2. iOS의 MLX-Swift-LM → Android의 MediaPipe LLM으로 대체 (Phase 3)
3. 디자인은 Material Design 3 기반으로 iOS와 **동일한 UX 흐름** 유지
4. 백엔드 API는 변경 없이 기존 서버 그대로 사용
