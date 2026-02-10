# 🏥 보건소 연동형 하루-ON 시스템 구현 계획 (B2G Health Sync)

본 문서는 기존 '하루-ON' 프로젝트를 기반으로, **보건소(관공서)와 연동**되는 B2G 특화 시스템을 **MariaDB**, **Django**, **Vue.js** 스택으로 재구축하기 위한 상세 구현 계획입니다.

---

## 1. 프로젝트 개요 (Overview)

- **목표**: 개인 사용자의 감정/정신건강 데이터를 안전하게 보건소(정신건강복지센터) 담당자와 공유하여, 위험군 조기 발굴 및 케어 연계 시스템 구축.
- **핵심 가치**:
  - **Data Rights**: 사용자가 자신의 데이터 공유 범위를 주도적으로 결정.
  - **Security**: 민감한 의료 정보의 분리 저장 및 전송 구간 암호화.
  - **Connectivity**: 기관 코드(Code) 기반의 간편한 연동.

---

## 2. 기술 스택 (Tech Stack Specification)

사용자의 요구사항에 맞춰 다음과 같이 기술 스택을 정의합니다.

### 🗄️ Database: MariaDB (Relational)

기존 NoSQL(MongoDB) 구조를 관계형 DB로 이관하여 데이터 무결성과 보건소 행정 데이터와의 호환성을 확보합니다.

- **선정 이유**: 공공기관 표준 준수, 강력한 트랜잭션 관리, 정형화된 데이터 관리 용이.
- **주요 특징**: 사용자-센터 간의 N:1 관계 매핑 및 엄격한 외래 키(FK) 제약 조건 적용.

### 🔙 Backend: Django + DRF (Python)

기존 Flask 경량 서버를 Django의 강력한 ORM과 기능을 활용하여 엔터프라이즈급 백엔드로 업그레이드합니다.

- **Framework**: Django REST Framework (DRF)
- **Authentication**: JWT (JSON Web Token) + SimpleJWT
- **Documentation**: Swagger (drf-yasg)
- **Admin**: Django Admin을 활용한 데이터 관리자(슈퍼유저) 대시보드 구축.

### 🎨 Frontend: Vue.js 3

사용자 경험(UX)을 극대화하기 위해 Vue.js 3 (Composition API) 기반으로 SPA를 구축합니다.

- **State Management**: Pinia (기존 Vuex 대체)
- **Routing**: Vue Router
- **Styling**: Tailwind CSS (권장) 또는 Scoped CSS
- **HTTP Client**: Axios (Interceptors를 통한 토큰 관리)

---

## 3. 데이터베이스 설계 (MariaDB Schema Design)

보건소 연동을 위한 핵심 테이블 구조입니다.

### 1) Users (사용자)

가입한 일반 사용자 정보입니다. (민감정보 최소화)

| Field        | Type                       | Description          |
| :----------- | :------------------------- | :------------------- |
| `id`         | BigInt (PK)                | 고유 ID              |
| `username`   | Varchar(150)               | 아이디 (암호화 가능) |
| `password`   | Varchar(128)               | 해싱된 비밀번호      |
| `risk_level` | Enum('LOW', 'MID', 'HIGH') | 위험도 등급          |
| `is_active`  | Boolean                    | 활성 상태            |
| `created_at` | DateTime                   | 가입일               |

### 2) Centers (보건소/센터)

협약된 보건소 및 정신건강복지센터 정보입니다.

| Field         | Type         | Description                          |
| :------------ | :----------- | :----------------------------------- |
| `id`          | BigInt (PK)  | 고유 ID                              |
| `name`        | Varchar(100) | 센터명 (예: 도봉구 정신건강복지센터) |
| `center_code` | Varchar(20)  | **연동용 고유 코드** (Unique)        |
| `region`      | Varchar(50)  | 관할 지역                            |
| `admin_email` | Varchar(254) | 담당자 이메일                        |

### 3) B2GConnection (연동 정보)

사용자와 보건소 간의 연결 관계를 관리합니다.

| Field          | Type                                 | Description             |
| :------------- | :----------------------------------- | :---------------------- |
| `id`           | BigInt (PK)                          | 고유 ID                 |
| `user_id`      | FK (Users)                           | 사용자 참조             |
| `center_id`    | FK (Centers)                         | 센터 참조               |
| `status`       | Enum('PENDING', 'ACTIVE', 'REVOKED') | 연동 상태               |
| `consented_at` | DateTime                             | 정보 제공 동의 일시     |
| `expired_at`   | DateTime                             | 연동 만료 일시 (선택적) |

### 4) haruON (감정 일기)

사용자가 작성한 일기 및 분석 데이터입니다.

| Field             | Type        | Description                      |
| :---------------- | :---------- | :------------------------------- |
| `id`              | BigInt (PK) | 고유 ID                          |
| `user_id`         | FK (Users)  | 작성자                           |
| `content`         | Text        | 일기 내용 (AES 암호화 저장 권장) |
| `mood_score`      | Integer     | 감정 점수 (1-10)                 |
| `analysis_result` | JSON        | AI 분석 결과 (감정 키워드 등)    |
| `is_high_risk`    | Boolean     | 위험 징후 포착 여부              |
| `created_at`      | DateTime    | 작성일                           |

---

## 4. 백엔드 구현 계획 (Django App Structure)

프로젝트를 기능 단위의 App으로 분리하여 개발합니다.

### 📂 Apps

1.  **`accounts`**: 회원가입, 로그인, JWT 발급, 프로필 관리.
2.  **`centers`**: 보건소 정보 관리, 기관 코드 생성 및 검증 로직.
3.  **`diaries`**: 일기 CRUD, AI 모델(Gemma 2/Ollama) 연동 분석 로직.
4.  **`b2g_sync`**:
    - **Core Logic**: 데이터 동기화 API. 사용자의 동의 하에 `haruON` 중 위험도가 높거나 요약된 데이터를 조회할 수 있는 API 제공.
    - **Security**: 보건소 담당자 전용 권한(Permission) 처리.

### 📡 API Endpoints (Draft)

- `POST /api/v1/auth/login/`: 사용자 로그인
- `POST /api/v1/diaries/`: 일기 작성
- `POST /api/v1/connect/verify/`: 보건소 코드 검증 (예: "DOBONG01" 입력 시 센터 정보 반환)
- `POST /api/v1/connect/confirm/`: 보건소 연동 확정 (개인정보 제3자 제공 동의 필수)
- `GET /api/v1/b2g/dashboard/users/`: (보건소용) 연동된 사용자 리스트 조회
- `GET /api/v1/b2g/dashboard/risk-alerts/`: (보건소용) 고위험 알림 조회

---

## 5. 프론트엔드 구현 계획 (Vue.js)

### 🖥️ 주요 화면 구성

1.  **사용자 앱 (Client Side)**
    - **설정 > 기관 연동**: 보건소 코드 입력 입력창, 약관 동의 모달.
    - **메인 홈**: '도봉구 보건소와 연결됨' 상태 표시 뱃지.
    - **일기 쓰기**: 기존 UX 유지하되, 위험 단어 감지 시 '센터에 알림이 전송됩니다' 팝업 (설정에 따라).

2.  **보건소 대시보드 (Admin Side)** (추가 개발 고려)
    - 보건소 담당자가 로그인하여 관할 사용자의 상태를 모니터링하는 웹 페이지.
    - Django Template으로 빠르게 구축하거나 Vue.js 어드민 템플릿 사용.

---

## 6. 개발 로드맵 (Roadmap)

### Phase 1: 환경 구축 (Week 1)

- [ ] Django 프로젝트 초기화 및 MariaDB 연동.
- [ ] User, Center 모델 설계 및 Migration.
- [ ] Vue.js 프로젝트 생성 (Vite 기반).

### Phase 2: 핵심 기능 구현 (Week 2-3)

- [ ] JWT 인증 시스템 구현.
- [ ] 일기 작성 및 조회 API (CRUD).
- [ ] 보건소 코드 검증 및 연동 로직 (`VerificationCode` 로직).

### Phase 3: AI 및 고도화 (Week 4)

- [ ] 기존 AI 모델(Gemma 2)을 Django 백엔드 내 Celery Task로 통합.
- [ ] 위험군 자동 분류 알고리즘 이식.
- [ ] 연동 테스트 및 버그 수정.

### Phase 4: 배포 (Deployment)

- [ ] OCI(Oracle Cloud) ARM 인스턴스 배포.
- [ ] Nginx + Gunicorn 설정.
- [ ] SSL 인증서 적용.

---

## 7. 마이그레이션 전략 (Migration from Flask/Mongo)

- **데이터 이관**: 기존 MongoDB의 JSON 데이터를 추출하여 형태 변환 후 MariaDB에 Bulk Insert 하는 스크립트 작성 (`migrate_mongo_to_maria.py`).
- **AI 모델**: `ai_brain.py` 등 기존 모듈은 Django의 `utils` 또는 별도 서비스 레이어로 이동하여 재사용.
