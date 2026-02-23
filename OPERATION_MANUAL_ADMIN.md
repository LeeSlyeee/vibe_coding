# 📋 마음온(Maum-On) 전국 관리 시스템 운영 매뉴얼

> **버전**: v1.0  
> **최종 수정일**: 2026-02-23  
> **대상**: 시스템 관리자, DevOps 엔지니어

---

## 1. 시스템 아키텍처 개요

```
┌─────────────────────────────────────────────────┐
│                   Nginx (217)                    │
│  /admin/* → frontend_admin_dist/                │
│  /api/*   → Gunicorn (127.0.0.1:8000)           │
└───────────────────┬─────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
   ┌────▼────┐ ┌────▼────┐ ┌───▼────┐
   │Gunicorn │ │  Redis  │ │ Nginx  │
   │ :8000   │ │ :6379   │ │ Static │
   │(Django) │ │ (Cache) │ │ Files  │
   └────┬────┘ └─────────┘ └────────┘
        │
   ┌────▼────┐
   │PostgreSQL│
   │  (RDS)  │
   └─────────┘
```

### 서버 정보

| 항목            | 값                                  |
| --------------- | ----------------------------------- |
| 서버 IP         | 217.142.253.35                      |
| OS              | Ubuntu 22.04 LTS                    |
| 도메인          | 217.142.253.35.nip.io               |
| Django 경로     | `/home/ubuntu/backend_new/`         |
| 프론트엔드 경로 | `/home/ubuntu/frontend_admin_dist/` |
| SSH 키          | `ssh-key/ssh-key-2026-01-15.key`    |

---

## 2. 서비스 관리

### 2.1 Gunicorn (Django 백엔드)

```bash
# 상태 확인
ps aux | grep gunicorn | grep -v grep

# 재시작
kill $(cat /tmp/gunicorn_new.pid)
sleep 1
cd /home/ubuntu/backend_new
./venv/bin/gunicorn config.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 2 \
  --timeout 30 \
  --daemon \
  --pid /tmp/gunicorn_new.pid

# 로그 확인
tail -f /home/ubuntu/backend_new/app.log
```

### 2.2 Redis (캐시 서버)

```bash
# 상태 확인
redis-cli ping  # 정상이면 "PONG" 반환

# 캐시 초기화 (통계 데이터 즉시 갱신 필요 시)
redis-cli -n 1 FLUSHDB

# 특정 키 삭제
redis-cli -n 1 DEL national_summary
```

### 2.3 Nginx

```bash
# 설정 검증
sudo nginx -t

# 재시작
sudo systemctl reload nginx

# 로그 확인
sudo tail -f /var/log/nginx/error.log
```

---

## 3. 데이터베이스 관리

### 3.1 접속 정보

```bash
# .env 파일에서 DB 정보 로드
cd /home/ubuntu/backend_new
source .env
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME
```

### 3.2 주요 테이블

| 테이블                        | 설명                      |
| ----------------------------- | ------------------------- |
| `centers_region`              | 17개 시·도 광역 단위      |
| `centers_center`              | 보건소 (Region FK)        |
| `accounts_user`               | 사용자 (admin_level 필드) |
| `admin_api_policybroadcast`   | 정책 하달                 |
| `admin_api_auditlog`          | 감사 로그                 |
| `admin_api_alertnotification` | 실시간 알림               |

### 3.3 백업 및 복원

```bash
# 백업
PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > backup_$(date +%Y%m%d).sql

# 복원
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME < backup_YYYYMMDD.sql
```

---

## 4. 캐시 관리 (Redis)

### 4.1 캐시 정책

| 캐시 키            | TTL         | 설명           |
| ------------------ | ----------- | -------------- |
| `national_summary` | 300초 (5분) | 전국 현황 통계 |

### 4.2 캐시 무효화

데이터 변경 후 즉시 반영이 필요한 경우:

```bash
redis-cli -n 1 DEL national_summary
```

---

## 5. 프론트엔드 배포

### 5.1 빌드 및 배포 절차

```bash
# 1. 로컬에서 빌드
cd frontend_admin
npx vite build

# 2. 서버로 배포
scp -i ssh-key/ssh-key-2026-01-15.key -r dist/* \
  ubuntu@217.142.253.35:/home/ubuntu/frontend_admin_dist/

# 3. 브라우저 캐시 새로고침 (Cmd+Shift+R)
```

### 5.2 롤백

```bash
# 이전 빌드 파일이 있다면
ssh ubuntu@217.142.253.35
cp -r /home/ubuntu/frontend_admin_dist_backup/* /home/ubuntu/frontend_admin_dist/
```

---

## 6. 보안 관리

### 6.1 권한 계층 (RBAC)

| Level | 역할          | 코드            | 접근 범위   |
| ----- | ------------- | --------------- | ----------- |
| L4    | 중앙 관리자   | `central_admin` | 전국 전체   |
| L3    | 광역 관리자   | `region_admin`  | 관할 시·도  |
| L2    | 보건소 관리자 | `center_admin`  | 소속 보건소 |
| L1    | 상담사        | `counselor`     | 담당 환자   |

### 6.2 관리자 계정 생성

```bash
cd /home/ubuntu/backend_new
./venv/bin/python manage.py shell -c "
from accounts.models import User
user = User.objects.create_user(
    username='new_admin',
    password='SecurePass123!',
    is_staff=True,
    admin_level='central_admin'
)
print(f'Created: {user.username}')
"
```

### 6.3 감사 로그 조회

```bash
# DB에서 직접 조회
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME \
  -c "SELECT user_id, action, target_type, ip_address, timestamp FROM admin_api_auditlog ORDER BY timestamp DESC LIMIT 20;"

# API로 조회 (인증 필요)
curl -H "Authorization: Bearer {TOKEN}" \
  https://217.142.253.35.nip.io/api/v1/admin/audit-logs/?days=7
```

---

## 7. 모니터링 및 알림

### 7.1 건강 체크

```bash
# 백엔드 API 응답 확인
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/v1/admin/regions/
# 403 = 정상 (인증 필요), 500 = 에러

# Redis 상태
redis-cli ping

# 디스크 사용량
df -h

# 메모리 사용량
free -h
```

### 7.2 알림 시스템

- **API**: `GET /api/v1/admin/alerts/` — 미읽음 알림 조회
- **읽음 처리**: `POST /api/v1/admin/alerts/` (body: `{"alert_id": 1}` 또는 `{"alert_id": "all"}`)

---

## 8. 트러블슈팅

### 8.1 일반적인 문제

| 증상                | 원인             | 해결                     |
| ------------------- | ---------------- | ------------------------ |
| 502 Bad Gateway     | Gunicorn 다운    | Gunicorn 재시작          |
| 지도 데이터 안 나옴 | API 403          | 관리자 토큰 확인         |
| 통계 갱신 안됨      | Redis 캐시       | `redis-cli -n 1 FLUSHDB` |
| 로그인 안됨         | JWT 만료         | 재로그인                 |
| 500 에러            | Django 코드 에러 | `app.log` 확인           |

### 8.2 긴급 복구 절차

```bash
# 1. 현재 상태 확인
ps aux | grep gunicorn
redis-cli ping
sudo systemctl status nginx

# 2. 로그 확인
tail -50 /home/ubuntu/backend_new/app.log

# 3. Gunicorn 재시작
kill $(cat /tmp/gunicorn_new.pid) 2>/dev/null
cd /home/ubuntu/backend_new
./venv/bin/gunicorn config.wsgi:application \
  --bind 127.0.0.1:8000 --workers 2 --timeout 30 \
  --daemon --pid /tmp/gunicorn_new.pid

# 4. Nginx 재시작
sudo systemctl restart nginx
```

---

## 9. API 엔드포인트 목록

| 메서드   | 경로                                    | 설명                | 권한 |
| -------- | --------------------------------------- | ------------------- | ---- |
| GET      | `/api/v1/admin/me/`                     | 현재 관리자 정보    | L3+  |
| GET      | `/api/v1/admin/national/summary/`       | 전국 현황 (캐시)    | L4   |
| GET      | `/api/v1/admin/regions/`                | 시·도 목록          | L4   |
| GET      | `/api/v1/admin/regions/{id}/`           | 시·도 상세          | L4   |
| GET      | `/api/v1/admin/regions/{id}/dashboard/` | 광역 대시보드       | L3+  |
| GET      | `/api/v1/admin/centers/`                | 보건소 목록         | L3+  |
| GET      | `/api/v1/admin/staff/`                  | 인력 목록           | L3+  |
| GET/POST | `/api/v1/admin/broadcasts/`             | 정책 배포           | L4   |
| GET      | `/api/v1/admin/export/national/`        | 전국 CSV 내보내기   | L4   |
| GET      | `/api/v1/admin/export/region/{id}/`     | 시·도 CSV 내보내기  | L3+  |
| GET/POST | `/api/v1/admin/alerts/`                 | 알림 조회/읽음 처리 | L4   |
| GET      | `/api/v1/admin/audit-logs/`             | 감사 로그 조회      | L4   |

---

## 10. 변경 이력

| 날짜       | 버전 | 내용                       |
| ---------- | ---- | -------------------------- |
| 2026-02-23 | v1.0 | 초기 작성 (Phase 1~4 완료) |
