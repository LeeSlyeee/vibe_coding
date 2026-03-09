# 📋 마음온(Maum-On) 전국 단위 상위 관리 시스템 구현 계획서

> **문서 버전**: v1.0  
> **작성일**: 2026-02-23  
> **목적**: 보건소 단위 의료진 시스템을 시·도 및 전국 단위로 확장하기 위한 **Super-Admin 계층 관리 시스템** 설계 및 구현 계획

---

## 1. 현황 분석 (As-Is)

### 1.1 현재 아키텍처 요약

```
┌─────────────────┐     ┌─────────────────┐
│   iOS 환자 앱    │────▶│  Node 217 (AI)  │
│  (On-Device AI)  │     │  Flask Satellite │
└─────────────────┘     └────────┬────────┘
                                 │ Relay
┌─────────────────┐     ┌────────▼────────┐
│ 의료진 웹 대시보드│────▶│  Node 150 (Hub) │
│  (Vue.js SPA)    │     │  Django Master   │
└─────────────────┘     └─────────────────┘
```

### 1.2 현재 데이터 모델 (단일 보건소 기준)

| 엔티티             | 역할                  | 한계점                     |
| :----------------- | :-------------------- | :------------------------- |
| `Center`           | 보건소 1개 단위       | 상위 조직(시·도) 개념 없음 |
| `User(is_staff)`   | 보건소 소속 상담사    | 보건소 간 데이터 조회 불가 |
| `User(manager)`    | 담당 환자 1:N 매핑    | 센터 내부에서만 유효       |
| `VerificationCode` | 환자-보건소 연동 코드 | 단일 센터에만 귀속         |

### 1.3 핵심 문제점

1. **수평적 구조**: 모든 Center가 동등한 레벨 → 상위 기관이 하위 보건소를 통합 관리할 수 없음
2. **데이터 사일로(Silo)**: 보건소 A의 담당자는 보건소 B의 데이터에 접근 불가
3. **통계의 부재**: 시·도 단위, 전국 단위의 통합 통계/대시보드가 존재하지 않음
4. **권한 모델 부족**: `is_superuser` 또는 `is_staff`의 2단계만 존재 → 광역/중앙 관리자 역할이 없음

---

## 2. 목표 아키텍처 (To-Be)

### 2.1 4계층 조직 구조

```
                    ┌──────────────────────┐
          Level 4   │   중앙 관리본부 (HQ)   │  ← 보건복지부 / 마음온 본사
                    │   Central Admin       │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼──────┐ ┌──────▼───────┐ ┌──────▼───────┐
L3  │ 서울특별시 본부  │ │ 경기도 본부   │ │ 부산광역시    │  ← 시·도 광역 단위
    │ Region Admin   │ │ Region Admin │ │ Region Admin │
    └───────┬────────┘ └──────┬───────┘ └──────┬───────┘
            │                 │                │
     ┌──────┼──────┐    ┌────┼────┐      ┌────┼────┐
     │      │      │    │    │    │      │    │    │
   ┌─▼─┐ ┌─▼─┐ ┌─▼─┐ ┌▼─┐ ┌▼─┐ ┌▼─┐  ┌▼─┐ ┌▼─┐ ┌▼─┐
L2 │도봉│ │강북│ │노원│ │수원││성남││용인│ │해운││사하││북 │  ← 보건소 (기존 Center)
   │보건│ │보건│ │보건│ │보건││보건││보건│ │대 ││보건││구 │
   │소  │ │소  │ │소  │ │소 ││소 ││소 │ │보건││소 ││보건│
   └─┬──┘ └─┬──┘ └─┬──┘ └┬─┘└┬─┘ └┬─┘ └┬─┘ └┬─┘ └┬─┘
     │      │      │     │   │    │    │    │    │
L1  상담사  상담사  상담사  ← 기존 Staff (담당 환자 관리)
     │
    환자들
```

### 2.2 권한 매트릭스 (RBAC)

| Level  | 역할          | 코드명          | 데이터 접근 범위       | 주요 기능                              |
| :----: | :------------ | :-------------- | :--------------------- | :------------------------------------- |
| **L4** | 중앙 관리자   | `CENTRAL_ADMIN` | **전국 전체**          | 전국 통계, 정책 배포, 시·도 관리       |
| **L3** | 광역 관리자   | `REGION_ADMIN`  | **관할 시·도 내 전체** | 광역 통계, 보건소 성과 비교, 인력 배치 |
| **L2** | 보건소 관리자 | `CENTER_ADMIN`  | **소속 보건소 내**     | 기존 기능 (환자 관리, 코드 발급)       |
| **L1** | 담당 상담사   | `COUNSELOR`     | **담당 환자만**        | 기존 기능 (일기 조회, 분석 확인)       |

---

## 3. DB 스키마 변경 계획

### 3.1 신규 모델: `Region` (광역 시·도)

```python
# centers/models.py (Django Hub - Node 150)
class Region(models.Model):
    """시·도 광역 단위 조직"""
    code = models.CharField(max_length=10, unique=True)       # 예: 'SEOUL', 'GYEONGGI'
    name = models.CharField(max_length=50)                     # 예: '서울특별시'
    region_type = models.CharField(max_length=20, choices=[
        ('metropolitan', '특별시/광역시'),
        ('province', '도'),
        ('special', '특별자치시/도'),
    ])
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "광역 시·도"
```

### 3.2 `Center` 모델 확장

```python
class Center(models.Model):
    # 기존 필드 유지
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)

    # ✅ 신규: Region 소속
    region = models.ForeignKey(
        Region, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='centers',
        verbose_name="소속 광역 시·도"
    )

    # ✅ 신규: 보건소 메타데이터
    address = models.TextField(blank=True)
    capacity = models.IntegerField(default=0, help_text="수용 가능 환자 수")
    is_active = models.BooleanField(default=True)
```

### 3.3 `User` 모델 확장

```python
class User(AbstractUser):
    # 기존 필드 유지 (center, manager 등)

    # ✅ 신규: 역할 계층
    admin_level = models.CharField(max_length=20, choices=[
        ('counselor', '담당 상담사'),          # L1
        ('center_admin', '보건소 관리자'),      # L2
        ('region_admin', '광역 관리자'),        # L3
        ('central_admin', '중앙 관리자'),       # L4
    ], default='counselor')

    # ✅ 신규: 광역 관리자의 소속 Region
    managed_region = models.ForeignKey(
        'centers.Region', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='region_admins',
        verbose_name="관리 광역 시·도"
    )
```

### 3.4 신규 모델: `PolicyBroadcast` (정책 하달)

```python
class PolicyBroadcast(models.Model):
    """중앙/광역에서 하위 보건소로 정책·공지를 전달"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    broadcast_level = models.CharField(max_length=20, choices=[
        ('national', '전국'),
        ('regional', '시·도'),
        ('center', '보건소'),
    ])
    target_region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.CASCADE)
    target_center = models.ForeignKey(Center, null=True, blank=True, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_urgent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

### 3.5 ERD (Entity Relationship)

```
┌──────────┐    1:N    ┌──────────┐    1:N    ┌──────────┐
│  Region  │──────────▶│  Center  │──────────▶│   User   │
│ (시·도)   │           │ (보건소)  │           │ (상담사)  │
└──────────┘           └──────────┘           └────┬─────┘
     │                                             │ 1:N (manager)
     │                                        ┌────▼─────┐
     └─── RegionAdmin (managed_region FK) ────│   User   │
                                              │ (환자)    │
                                              └──────────┘
```

---

## 4. 상위 관리 대시보드 (Super-Admin Dashboard)

### 4.1 중앙 관리자 (L4) 대시보드 화면 구성

| 화면               | 기능                              | 핵심 지표                                    |
| :----------------- | :-------------------------------- | :------------------------------------------- |
| **전국 현황 지도** | 시·도별 색상 코딩된 대한민국 지도 | 환자 수, 고위험군 비율, 활성도               |
| **광역 비교 분석** | 시·도 간 성과 비교 차트           | 평균 감정 점수, Red Flag 발생률, 복약 순응도 |
| **보건소 랭킹**    | 전국 보건소 KPI 순위표            | 환자 대비 상담 비율, 응답 시간, 이용률       |
| **정책 배포**      | 전국/광역/보건소별 공지 발송      | 수신 확인율, 이행 현황                       |
| **인력·자원 관리** | 시·도별 상담사 현황               | 인력 부족 보건소 알림                        |

### 4.2 광역 관리자 (L3) 대시보드 화면 구성

| 화면                 | 기능                         | 핵심 지표                          |
| :------------------- | :--------------------------- | :--------------------------------- |
| **관할 보건소 현황** | 소속 보건소 목록 및 상태     | 활성 환자 수, 고위험군, 최근 활동  |
| **보건소 상세**      | 특정 보건소 드릴 다운        | 상담사별 담당 환자, 일기 분석 추이 |
| **광역 통계**        | 관할 지역 종합 통계          | 월간 신규 등록, 위기 개입 건수     |
| **인력 배치**        | 보건소 간 상담사 재배치 요청 | 업무 과부하 지표                   |

---

## 5. API 설계 (신규 엔드포인트)

### 5.1 조직 관리 API

```
# Region CRUD (L4만 접근)
GET    /api/v1/admin/regions/                    # 전국 시·도 목록
POST   /api/v1/admin/regions/                    # 시·도 등록
GET    /api/v1/admin/regions/{id}/               # 시·도 상세 (소속 보건소 포함)
PUT    /api/v1/admin/regions/{id}/               # 시·도 정보 수정

# Center 관리 (L3 이상 접근)
GET    /api/v1/admin/regions/{id}/centers/        # 해당 시·도 소속 보건소 목록
POST   /api/v1/admin/regions/{id}/centers/        # 보건소 등록 (시·도에 귀속)
```

### 5.2 통합 통계 API

```
# 전국 통계 (L4)
GET    /api/v1/stats/national/summary/            # 전국 요약 (환자 수, 고위험군 등)
GET    /api/v1/stats/national/trend/              # 전국 감정 추이 (기간별)
GET    /api/v1/stats/national/risk-map/           # 시·도별 위험도 지도 데이터

# 광역 통계 (L3)
GET    /api/v1/stats/region/{id}/summary/         # 시·도 요약
GET    /api/v1/stats/region/{id}/centers/compare/ # 보건소 간 비교
GET    /api/v1/stats/region/{id}/trend/           # 시·도 감정 추이

# 보건소 통계 (L2, 기존 확장)
GET    /api/v1/stats/center/{id}/summary/         # 보건소 요약
```

### 5.3 권한 미들웨어 (Permission Middleware)

```python
# permissions.py
class HierarchicalPermission(BasePermission):
    """계층적 데이터 접근 제어"""

    def has_permission(self, request, view):
        user = request.user
        target_level = view.kwargs.get('admin_level')

        if user.admin_level == 'central_admin':
            return True  # L4: 전체 접근

        if user.admin_level == 'region_admin':
            # L3: 자신의 관할 Region 내 데이터만
            target_region = view.kwargs.get('region_id')
            return str(user.managed_region_id) == str(target_region)

        if user.admin_level == 'center_admin':
            # L2: 자신의 Center 내 데이터만
            target_center = view.kwargs.get('center_id')
            return str(user.center_id) == str(target_center)

        # L1: 기존 manager 기반 필터링
        return False
```

---

## 6. 프론트엔드 구조

### 6.1 신규 프로젝트: `frontend_admin`

```
frontend_admin/
├── src/
│   ├── views/
│   │   ├── NationalDashboard.vue      # L4 전국 현황
│   │   ├── RegionDashboard.vue        # L3 광역 현황
│   │   ├── RegionManagement.vue       # 시·도 관리 CRUD
│   │   ├── CenterManagement.vue       # 보건소 관리
│   │   ├── StaffManagement.vue        # 인력 관리
│   │   ├── PolicyBroadcast.vue        # 정책 배포
│   │   └── NationalRiskMap.vue        # 전국 위험도 지도
│   ├── components/
│   │   ├── KoreaMap.vue               # 대한민국 지도 시각화
│   │   ├── RegionCard.vue             # 시·도 카드
│   │   ├── CenterRankingTable.vue     # 보건소 순위표
│   │   ├── HierarchyBreadcrumb.vue    # 계층 네비게이션
│   │   └── StatComparisonChart.vue    # 비교 차트
│   ├── composables/
│   │   └── useHierarchicalAuth.js     # 계층 권한 관리
│   └── router/
│       └── index.js                   # 권한 기반 라우팅
```

### 6.2 기존 `frontend_staff` 변경사항

- **최소 변경 원칙**: 기존 보건소 상담사 워크플로우는 유지
- 추가: 상단 배너에 **상위 기관 공지사항** 표시 영역
- 추가: 보건소 관리자(L2)용 사이드바에 "소속 기관 정보" 메뉴

---

## 7. 인프라 확장 계획

### 7.1 현재 → 목표 인프라

```
[현재]                              [목표]
Node 150 (Hub) ──── 단일 인스턴스    Node 150 (Hub) ──── 확장 가능 구조
Node 217 (AI)  ──── 단일 인스턴스    Node 217 (AI)  ──── 부하 분산 대비

                                    ┌─ PostgreSQL (기존 MariaDB 마이그레이션 권장)
                                    ├─ Redis (세션/캐시/Celery)
                                    └─ MongoDB (AI 분석 데이터)
```

### 7.2 확장 시 고려사항

| 항목     | 현재              | 목표                    | 비고                                         |
| :------- | :---------------- | :---------------------- | :------------------------------------------- |
| **DB**   | MariaDB + MongoDB | PostgreSQL + MongoDB    | PostgreSQL 파티셔닝으로 Region별 성능 최적화 |
| **캐시** | 없음              | Redis                   | 전국 통계 캐싱 (5분 TTL)                     |
| **인증** | JWT (단순)        | JWT + RBAC 미들웨어     | 계층별 토큰 클레임 추가                      |
| **로그** | nohup.out         | 중앙 로그 수집 (ELK 등) | 감사 추적(Audit Trail) 필수                  |

---

## 8. 데이터 프라이버시 및 보안

### 8.1 계층별 데이터 격리 원칙

1. **상위는 집계 데이터만 조회**: L3/L4는 개별 환자의 일기 원문에 접근 불가 (통계/요약만)
2. **개인정보 비식별화**: 상위 통계에서 환자 이름·닉네임은 제거, 연령대/성별만 집계
3. **접근 로그 의무화**: 모든 데이터 조회에 대한 Audit Log 기록
4. **Region 간 격리**: 서울시 관리자는 경기도 데이터 조회 불가 (DB 쿼리 레벨 강제)

### 8.2 감사 추적 모델

```python
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)  # 'VIEW_STATS', 'EXPORT_DATA' 등
    target_type = models.CharField(max_length=50)  # 'region', 'center', 'patient'
    target_id = models.IntegerField()
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    detail = models.JSONField(default=dict)
```

---

## 9. 단계별 로드맵

### Phase 1: 기반 구축 ✅ (2026-02-23 완료)

- [x] `Region` 모델 생성 및 마이그레이션 (17개 시·도 시드 데이터 입력)
- [x] `User.admin_level`, `User.managed_region` 필드 추가
- [x] `Center.region` FK 추가 및 기존 데이터 매핑 (서울 3개 보건소 자동 연결)
- [x] 계층적 Permission 미들웨어 구현 (`IsCentralAdmin`, `IsRegionAdminOrAbove`, `HierarchicalDataAccess`)
- [x] Django Admin에서 Region/Center/User 계층 관리 가능하도록 설정
- [x] `PolicyBroadcast` 모델 생성 (정책 하달 시스템)
- [x] `AuditLog` 모델 생성 (감사 추적)
- [x] `admin_api` 앱 생성 및 통계 API 구현 (전국 현황, 광역 대시보드, 시·도 CRUD)
- [x] 기존 `PatientListView`에 `get_accessible_patients()` 계층 권한 로직 적용
- [x] 기존 `frontend_staff` 하위 호환성 유지 확인

### Phase 2: 광역 관리자 대시보드 ✅ (2026-02-23 완료)

- [x] `frontend_admin` 프로젝트 초기 세팅 (Vue.js + Vite)
- [x] 광역 관리자(L3) 로그인 및 인증 플로우
- [x] 관할 보건소 목록 조회 및 상세 드릴다운
- [x] 광역 단위 통계 API 및 차트 구현 (보건소별 환자/일기 비교 바 차트)
- [x] 보건소 간 비교 분석 화면

### Phase 3: 중앙 관리 시스템 ✅ (2026-02-23 완료)

- [x] 중앙 관리자(L4) 전국 대시보드 (6종 통계 카드 + 시·도별 그리드)
- [x] 대한민국 지도 기반 시각화 (SVG 인터랙티브 맵, 위험도 색상 코딩)
- [x] 전국 통합 통계 + 시·도별 드릴다운 (클릭 → 광역 대시보드)
- [x] 정책 배포(PolicyBroadcast) 시스템 (CRUD UI + API)
- [x] 데이터 내보내기(CSV) 기능 (전국/시·도별 보고서)

### Phase 4: 고도화 및 안정화 ✅ (2026-02-23 완료)

- [x] 성능 최적화: django-redis 설치, CACHES 설정, NationalSummaryView에 5분 TTL 캐시 적용
- [x] 실시간 알림: AlertNotification 모델/테이블, 알림 조회·읽음 처리 API (`/api/v1/admin/alerts/`)
- [x] 보안 감사: AuditLogMiddleware (관리자 API 접근 자동 기록), 감사 로그 조회 API (`/api/v1/admin/audit-logs/`)
- [x] 운영 매뉴얼 작성: `OPERATION_MANUAL_ADMIN.md` (아키텍처, 서비스 관리, 배포, 보안, 트러블슈팅)

---

## 10. 리스크 및 제약사항

| 리스크                               | 영향도  | 대응 방안                                         |
| :----------------------------------- | :-----: | :------------------------------------------------ |
| 기존 보건소 데이터 마이그레이션 실패 | 🔴 높음 | 마이그레이션 스크립트 사전 테스트, 롤백 계획 수립 |
| 대규모 동시 접속 시 DB 병목          | 🟡 중간 | Redis 캐싱, 읽기 전용 Replica DB 구성             |
| 개인정보보호법 저촉                  | 🔴 높음 | 법률 자문 후 데이터 접근 범위 확정                |
| 기존 frontend_staff 회귀(Regression) | 🟡 중간 | 기존 시스템과 분리된 신규 프로젝트로 구현         |
| 보건소별 인터넷 환경 차이            | 🟢 낮음 | 경량 정적 빌드, CDN 활용                          |

---

## 11. 예상 성과

1. **행정 효율화**: 시·도 단위 통합 모니터링으로 보건소별 개별 보고 불필요
2. **정책 근거 확보**: 전국 단위 정신건강 데이터로 예산 배분의 객관적 근거 제공
3. **위기 대응 강화**: 전국 고위험군 실시간 모니터링으로 골든타임 확보
4. **확장성 확보**: B2G 전국 단위 사업 수주 시 즉시 대응 가능한 인프라
5. **Top-down 보급 전략 실현**: 보건복지부 → 시·도 → 보건소 하향식 배포 구조 완성
