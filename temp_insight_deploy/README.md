# Haru-On B2G System (InsightMind)

보건소 연동형 하루-ON 시스템 프로젝트입니다.

## 📂 프로젝트 구조

- **backend/**: Django REST Framework 기반 API 서버
- **frontend/**: Vue.js 3 + Vite 기반 클라이언트

## 🚀 시작하기 가이드

### 1. 데이터베이스 준비 (MariaDB)

로컬 MariaDB에 접속하여 데이터베이스를 생성해주세요.

```sql
CREATE DATABASE maumon_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 백엔드 설정 (Backend)

1. **환경 변수 설정**: `backend/.env` 파일을 열어 DB 접속 정보를 수정해주세요.

   ```ini
   DB_NAME=maumon_db
   DB_USER=root        <-- 본인 DB 아이디
   DB_PASSWORD=password <-- 본인 DB 비밀번호
   ```

2. **가상환경 실행 및 패키지 설치** (최초 1회)

   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt  # (생성 예정)
   ```

   _현재는 직접 설치됨._

3. **마이그레이션 (DB 테이블 생성)**

   ```bash
   python manage.py migrate
   ```

4. **서버 실행**
   ```bash
   python manage.py runserver
   ```

### 3. 프론트엔드 설정 (Frontend)

1. **패키지 설치**

   ```bash
   cd frontend
   npm install
   ```

2. **개발 서버 실행**
   ```bash
   npm run dev
   ```
