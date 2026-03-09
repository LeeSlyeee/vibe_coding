# MongoDB 전환 마이그레이션 계획서

## 1. 개요 (Overview)

본 문서는 기존 SQLite(SQLAlchemy) 기반의 데이터베이스 계층을 **MongoDB**로 전환하기 위한 실행 계획을 기술합니다.
목표는 정형화된 RDBMS 구조에서 벗어나, 유연한 Document 기반 구조로 변경하여 향후 기능 확장(사진, 음성 등 다양한 데이터 타입 추가)에 대비하고 NoSQL 환경을 학습하는 것입니다.

## 2. 기술 스택 변경 (Tech Stack)

- **Current**: SQLite + SQLAlchemy (ORM)
- **Target**: MongoDB + Flask-PyMongo (Driver)
  - _ODM(MongoEngine) 대신 PyMongo를 사용하여 NoSQL의 유연성을 최대한 활용합니다._

## 3. 데이터 모델링 변경 (Schema Mapping)

### 3.1. Diary (일기 데이터)

SQLite의 정형 테이블에서 JSON Document로 변경됩니다.

**[AS-IS] SQLite Table**

```sql
id (Integer, PK)
date (String)
mood (String) -- Happy, Sad...
content (Text) -- 질문 답변들 통합? or 개별 컬럼? (현재는 질문 컬럼이 고정됨)
created_at (DateTime)
ai_result (Text)
```

**[TO-BE] MongoDB Document**

```json
{
  "_id": ObjectId("..."),
  "date": "2024-01-16",
  "mood_level": 3,
  "event": "오늘 있었던 일...",
  "emotion_desc": "느낀 감정...",
  "emotion_meaning": "감정의 의미...",
  "self_talk": "나에게 하는 말...",
  "created_at": ISODate("2024-01-16T10:00:00Z"),
  "ai_prediction": "행복 (98%)",
  "ai_comment": "정말 행복하시겠어요!",
  "task_id": "celery-task-uuid"  // AI 분석 작업 ID
}
```

_장점: 추후 질문이 5개로 늘어나거나, 'photo_url' 필드가 추가되어도 기존 데이터에 영향 없이 즉시 저장 가능._

### 3.2. EmotionKeyword (AI 학습/분석용 키워드)

```json
{
  "_id": ObjectId("..."),
  "keyword": "눈물",
  "emotion_label": 1, // 0~5
  "frequency": 15
}
```

## 4. 실행 단계 (Action Plan)

### Phase 1: 환경 설정 (Setup)

1. **패키지 설치**: `pip install flask-pymongo dnspython`
2. **MongoDB 준비**:
   - 로컬 설치(Docker 또는 Native) 또는
   - MongoDB Atlas (클라우드 프리티어) 계정 생성 및 연결 문자열 확보.
3. **DB 연결 설정**: `config.py`에서 `SQLALCHEMY_DATABASE_URI` 코드를 제거하고 `MONGO_URI` 설정 추가.

### Phase 2: 코드 리팩토링 (Refactoring)

가장 많은 작업이 필요한 단계입니다.

1. **`app.py` (API 로직 교체)**

   - `db.session.add()` / `commit()` → `mongo.db.diaries.insert_one()`
   - `Diary.query.filter_by()...` → `mongo.db.diaries.find_one()`
   - **ID 처리**: MongoDB의 `_id`는 ObjectId 객체이므로, 프론트엔드로 보낼 때 `str(_id)`로 변환하는 유틸리티 함수 필요.

2. **`models.py` (삭제 또는 변경)**

   - SQLAlchemy 모델 클래스는 더 이상 필요 없으므로 삭제하거나, 데이터 유효성 검사(Validation) 용도로만 남김.

3. **`ai_brain.py` (AI 로직 데이터 연동)**
   - 기존 SQL 쿼리로 학습 데이터 가져오던 부분을 MongoDB Aggregation 또는 `find()` 쿼리로 변경.
   - `tasks.py` (Celery)에서 DB 상태 업데이트하는 로직을 MongoDB용으로 변경.

### Phase 3: 데이터 마이그레이션 (Optional)

기존 SQLite에 저장된 소중한 일기들이 있다면, 이를 읽어서 MongoDB로 옮기는 스크립트(`migrate_sql_to_mongo.py`)를 작성하여 실행.

### Phase 4: 테스트 및 안정화

- 프론트엔드 연동 테스트 (로그인, 일기 작성, 수정, 삭제, 리스트 조회)
- AI 분석 프로세스 동작 확인 (Celery 연동)

## 5. 예상 리스크 및 해결 방안

- **Risk**: 기존 데이터의 ID가 숫자(1, 2, 3...)였다가 MongoDB ObjectId(문자열 난수)로 바뀌면서 프론트엔드 라우팅(`/diary/1` → `/diary/65a12b...`)에 문제가 생길 수 있음.
  - **Solution**: 프론트엔드는 이미 ID를 문자열로 처리하도록 되어 있으나, 확인 필요. 백엔드에서 ID를 내려줄 때 `id` 필드에 문자열로 변환 값을 담아줌.

---

**작성일**: 2026-01-16
**작성자**: Vibe Coding Agent
