# Voice Diary (Speaking Diary) Implementation Plan

## 개요

사용자가 글로 쓰기 힘든 날, 말로 일기를 작성하면 AI가 텍스트로 변환해주고 분석해주는 "말하는 일기" 기능을 구현합니다.
목표는 현재 OCI 서버(4 Core / 24GB RAM)에서 무리 없이 돌아가는 효율적인 음성 인식 시스템을 구축하는 것입니다.

## 기술적 접근 (성능 최적화)

OCI 서버 자원을 고려하여 가장 가볍고 빠른 모델을 선택해야 합니다.

- **Engine**: `faster-whisper` (OpenAI Whisper의 최적화 버전, CTranslate2 기반).
  - 기존 Whisper 대비 CPU에서 최대 4배 빠름.
  - 메모리 사용량 절반 이하.
- **Model**: `small` 또는 `process` (한국어 인식률과 속도의 타협점).
  - `tiny`: 빠르지만 한국어 정확도 낮음.
  - `base`: 무난함.
  - `small`: 정확도 좋음, CPU에서 약간의 지연(3~5초) 있을 수 있음. -> **Small 권장** (정확도가 중요).

## 구현 단계

### 1단계: 백엔드 (Backend)

1. **의존성 추가**: `faster-whisper` 패키지 설치.
2. **AI 모듈 확장 (`voice_brain.py`)**:
   - Whisper 모델 로딩 및 추론 로직 구현.
   - CPU 처리에 최적화된 설정(`int8` quantization 등) 적용.
3. **API 엔드포인트 추가 (`app.py`)**:
   - `POST /api/voice/transcribe`: 오디오 파일 업로드 및 텍스트 반환.
   - 임시 파일 저장 및 정리 로직.

### 2단계: 프론트엔드 (Frontend)

1. **일기 작성 모달 수정**:
   - 마이크 아이콘 버튼 추가.
   - 녹음 상태 UI (녹음 중, 처리 중 등) 구현.
2. **녹음 로직 구현**:
   - Web Audio API (`MediaRecorder`) 사용하여 브라우저에서 녹음.
   - `audio/webm` 또는 `audio/mp4` 형식으로 백엔드 전송.
3. **텍스트 연동**:
   - 변환된 텍스트를 일기 입력창에 자동 입력.

### 3단계: OCI 배포 및 테스트

1. `requirements.txt` 업데이트.
2. OCI 서버에서 `libcublas` 등 필요한 라이브러리(GPU 없다면 불필요) 확인.
3. CPU 부하 테스트.

## 서버 부하 예상 (OCI 4 Core / 24 RAM)

- **RAM**: 24GB는 매우 충분합니다. (Whisper Small 모델은 약 1GB 미만 소모)
- **CPU**: 음성 변환 순간 1~2개 코어가 100% 사용될 수 있습니다.
  - `faster-whisper` 사용 시 1분 분량 오디오 처리에 약 5~10초(CPU) 소요 예상.
  - 동시 접속자 100명이 **동시에** 말을 걸지 않는 이상, 간헐적인 요청은 충분히 처리가능합니다.
  - **결론**: 현재 스펙으로 충분히 구현 가능합니다.
