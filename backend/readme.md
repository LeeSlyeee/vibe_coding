# Mood Diary AI 백엔드

무드 다이어리(Mood Diary) 애플리케이션을 위한 Flask 기반 백엔드로, 고급 감정 분석 및 공감형 AI 코멘트 생성 기능을 특징으로 합니다.

## 🚀 주요 기능

### 1. 감정 분석 (LSTM)

- **모델**: 128 유닛을 가진 양방향 LSTM (Bidirectional LSTM).
- **클래스**: 5가지 감정 (행복해, 평온해, 그저그래, 우울해, 화가나).
- **훈련 데이터**: 약 47,000개의 결합된 데이터셋.
  - `GoEmotions-Korean`: 50,000개 이상의 라벨링된 문장 (Google).
  - `감성대화말뭉치`: 36,000개 이상의 대화 쌍 (AI Hub).
  - `User Data`: 10,000개 이상의 실제 일기 데이터 (파인 튜닝).
- **성능**: 저장된 모델(`emotion_model.h5`)을 통해 높은 정확도 제공.

### 2. 생성형 AI 코멘트 (고급 하이브리드 시스템)

- **시스템**: 3단계 우선순위 아키텍처.
  1.  **안전장치 (규칙 기반)**: "시험", "이별"과 같은 중요 키워드에 대해 즉각적이고 높은 품질의 조언 제공.
  2.  **KoGPT-2 (LLM)**: SKT의 `kogpt2-base-v2` 모델을 사용하여 창의적이고 시적인 답변 생성.
  3.  **Seq2Seq (대체 모델)**: 경량 백업 모델.
- **기능**: 사용자 일기를 바탕으로 공감하고 맥락을 파악하여 조언 생성.
- **최적화**: 효율적인 한국어 토큰화를 위해 `PreTrainedTokenizerFast` 사용.
- **파일**: `comment_bank.json` (규칙), `comment_model.h5` (레거시).

### 3. 능동형 학습 및 키워드 추출

- **키워드 추출**: 사용자 일기에서 감정별 키워드를 자동으로 학습.
- **지식 베이스**: `EmotionKeyword` 테이블에 현재 **30,000개 이상의 학습된 키워드** 보유.
- **지속적 학습**: 일기 데이터가 쌓일수록 시스템의 성능이 향상됨.

---

## 🛠 설정 및 실행

### A. 환경 설정

```bash
cd backend
source venv/bin/activate
```

### B. 서버 실행

```bash
python app.py
```

- 서버는 `http://127.0.0.1:5000`에서 시작됩니다.
- API 문서: `app.py`의 `/api/` 엔드포인트를 참조하세요.

### C. 스크립트를 통한 AI 관리

- **전체 모델 재훈련**: `python retrain_model.py` (강제 재훈련)
- **기존 데이터 일괄 업데이트**: `python batch_update_ai.py` (기존 일기에 새로운 AI 분석 적용)
- **코멘트 검증**: `python verify_comments.py`

## 📁 프로젝트 구조

- `ai_analysis.py`: 핵심 AI 로직 (훈련, 추론, 지속성 관리).
- `app.py`: Flask REST API 라우트.
- `models.py`: SQLAlchemy 데이터베이스 모델 (`User`, `Diary`, `EmotionKeyword`).
- `*.h5 / *.pickle`: 최적화된 AI 모델 파일.
