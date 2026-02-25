# 🚀 Maum-On × EXAONE-3.5-7.8B RunPod Serverless 배포 가이드

> Git 없이, RunPod GPU Pod에서 직접 Docker 이미지를 빌드하고 Serverless로 배포하는 전체 과정

---

## 📋 사전 준비물

| 준비물              | 설명                                                 | 확인 |
| ------------------- | ---------------------------------------------------- | :--: |
| **RunPod 계정**     | [runpod.io](https://www.runpod.io) 가입              |  ☐   |
| **RunPod 크레딧**   | $10~20 (빌드 Pod 임시 사용 + Serverless 테스트)      |  ☐   |
| **Docker Hub 계정** | [hub.docker.com](https://hub.docker.com) 가입 (무료) |  ☐   |

---

## 🔰 전체 흐름 (3단계)

```
[1단계] RunPod GPU Pod 생성 (임시 작업용)
    ↓
[2단계] Pod 안에서 Docker 이미지 빌드 & Push
    ↓
[3단계] RunPod Serverless Endpoint 생성 & 백엔드 연동
```

---

## 1단계: RunPod GPU Pod 생성 (임시 빌드용)

### 1-1. RunPod 콘솔 접속

- [https://www.runpod.io/console/pods](https://www.runpod.io/console/pods) 접속
- 좌측 메뉴에서 **"Pods"** 클릭

### 1-2. GPU Pod 생성

- **"+ GPU Pod"** 버튼 클릭
- **GPU 선택**: 아무거나 (빌드만 할 거라 저렴한 것 추천)
  - 추천: `RTX 4090` 또는 `RTX A5000` (Community Cloud → 가장 싼 것)
  - ⚠️ 실제 AI 추론은 안 하므로 GPU 성능은 상관없음
- **Template**: `RunPod Pytorch 2.x` 선택

### 1-3. 디스크 설정 (매우 중요!)

- **Container Disk**: **100 GB** (Docker 이미지 빌드에 필요)
- **Volume Disk**: **0 GB** (필요 없음)

### 1-4. Deploy

- **"Deploy On-Demand"** 또는 **"Deploy Spot"** (Spot이 더 저렴) 클릭
- Pod가 시작될 때까지 1~3분 대기

### 1-5. 터미널 접속

- Pod 목록에서 생성된 Pod의 **"Connect"** 버튼 클릭
- **"Start Web Terminal"** 또는 **"Start Jupyter Lab"** 클릭
- Web Terminal이 열리면 준비 완료

---

## 2단계: Pod 안에서 Docker 이미지 빌드

### 2-1. 작업 폴더 생성

```bash
mkdir -p /workspace/maumon-exaone/src
cd /workspace/maumon-exaone
```

### 2-2. 파일 생성 (Web Terminal에서 직접 붙여넣기)

#### ① Dockerfile 생성

```bash
cat > Dockerfile << 'DOCKERFILE_END'
FROM vllm/vllm-openai:v0.8.3
WORKDIR /app
RUN pip install runpod huggingface_hub
COPY src/handler.py /app/handler.py
COPY src/start.sh /app/start.sh
RUN chmod +x /app/start.sh
RUN python3 -c "\
from huggingface_hub import snapshot_download; \
snapshot_download( \
    repo_id='LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct', \
    local_dir='/app/model', \
    ignore_patterns=['*.pth', '*.pt', '*.gguf'] \
); \
print('✅ EXAONE-3.5-7.8B-Instruct 다운로드 완료')"
ENTRYPOINT ["/app/start.sh"]
CMD []
DOCKERFILE_END
```

#### ② handler.py 생성

```bash
cat > src/handler.py << 'HANDLER_END'
"""
RunPod Serverless Handler — Maum-On × EXAONE-3.5-7.8B-Instruct
"""

import runpod
from vllm import LLM, SamplingParams
import traceback
import sys

MODEL_PATH = "/app/model"

print("🚀 [Init] EXAONE-3.5-7.8B-Instruct 로딩 시작...", flush=True)

try:
    llm = LLM(
        model=MODEL_PATH,
        dtype="float16",
        gpu_memory_utilization=0.90,
        max_model_len=4096,
        trust_remote_code=True,
        enforce_eager=True,
    )
    print("✅ [Init] EXAONE-3.5-7.8B-Instruct 로딩 완료!", flush=True)
except Exception as e:
    print(f"❌ [Init] 모델 로딩 실패: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

SYSTEM_PROMPT = """당신은 깊은 공감 능력과 전문적 통찰력을 갖춘 AI 심리 상담사 '마음온'입니다.

[핵심 행동 수칙]
1. 절대 영어 금지: 사용자가 영어를 써도, 오직 한국어(존댓말 해요체)로만 답해주세요.
2. 감정 미러링: 사용자가 느끼는 감정을 있는 그대로 받아들이고, 그 감정이 타당함을 인정해주세요.
3. 능동적 대화: 사용자의 말을 경청하고, 관련된 질문을 던져 대화를 자연스럽게 이어가세요.
4. 반복 금지: 같은 표현을 반복하지 마세요. 다양하고 자연스러운 표현을 사용하세요.
5. 위기 대응: 자살, 자해 관련 언급 시 따뜻하게 위로하고, 자살예방상담전화 1393을 안내하세요.
6. 답변 길이: 3~5문장으로 간결하되 진심이 담긴 답변을 제공하세요."""

def build_prompt(user_text, history=""):
    parts = []
    parts.append(f"[|system|]{SYSTEM_PROMPT}[|endofturn|]")
    if history:
        parts.append(f"[|user|][이전 대화 기록]\n{history}\n[|endofturn|]")
        parts.append(f"[|assistant|]네, 이전 대화를 기억하고 있어요.[|endofturn|]")
    parts.append(f"[|user|]{user_text}")
    parts.append("[|assistant|]")
    return "\n".join(parts)

def handler(job):
    job_input = job.get("input", {})
    user_text = job_input.get("text") or job_input.get("prompt")
    history = job_input.get("history", "")
    max_tokens = job_input.get("max_tokens", 512)
    temperature = job_input.get("temperature", 0.7)

    if not user_text:
        return {"error": "입력 텍스트가 없습니다."}

    full_prompt = build_prompt(user_text, history)

    sampling_params = SamplingParams(
        temperature=temperature,
        top_p=0.9,
        max_tokens=max_tokens,
        stop=["[|endofturn|]", "[|user|]"],
        repetition_penalty=1.1,
    )

    try:
        outputs = llm.generate(full_prompt, sampling_params)
        generated_text = outputs[0].outputs[0].text.strip()
        print(f"💬 In: {user_text[:30]}... → Out: {generated_text[:30]}...", flush=True)
        return {"reaction": generated_text}
    except Exception as e:
        print(f"❌ 추론 실패: {e}", flush=True)
        return {"reaction": "잠시 상담 시스템에 문제가 있어요. 곧 돌아올게요. 🙏"}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
HANDLER_END
```

#### ③ start.sh 생성

```bash
cat > src/start.sh << 'START_END'
#!/bin/bash
echo "🚀 [Start] Maum-On × EXAONE-3.5-7.8B Container Started!"
if [ -d "/app/model" ] && [ -f "/app/model/config.json" ]; then
    echo "✅ [Start] EXAONE 모델 파일 확인 완료"
    du -sh /app/model
else
    echo "❌ [Start] 모델 파일 없음!"
    exit 1
fi
echo "🚀 [Start] Handler 시작..."
python3 -u /app/handler.py
START_END
```

### 2-3. 파일 확인

```bash
echo "=== 파일 구조 확인 ==="
find . -type f
echo ""
echo "=== Dockerfile 확인 ==="
cat Dockerfile
```

### 2-4. Docker Hub 로그인

```bash
docker login
# Username: (Docker Hub 아이디 입력)
# Password: (Docker Hub 비밀번호 또는 Access Token 입력)
```

> 💡 **Access Token 사용 권장**: Docker Hub → Account Settings → Security → New Access Token

### 2-5. Docker 이미지 빌드 🔨

```bash
# ⏱️ 이 과정은 10~20분 소요 (31GB 모델 다운로드 포함)
docker build -t YOUR_DOCKERHUB_ID/maumon-exaone:latest .
```

> ⚠️ `YOUR_DOCKERHUB_ID`를 본인의 Docker Hub 아이디로 교체!
> 예: `docker build -t slyeee/maumon-exaone:latest .`

**빌드 중 진행 상황:**

```
Step 1/8 : FROM vllm/vllm-openai:v0.8.3     ← vLLM 베이스 이미지 (5분)
Step 5/8 : RUN python3 -c "..."              ← 모델 다운로드 (10분)
✅ EXAONE-3.5-7.8B-Instruct 다운로드 완료
Successfully built abc123def456                ← 성공!
```

### 2-6. Docker Hub에 Push 📤

```bash
# ⏱️ 이 과정은 10~15분 소요 (이미지 업로드)
docker push YOUR_DOCKERHUB_ID/maumon-exaone:latest
```

### 2-7. 빌드 Pod 종료 (비용 절약!)

- Push 완료 후, RunPod 콘솔에서 **빌드용 Pod를 즉시 종료(Terminate)** 하세요!
- 더 이상 필요 없습니다.

---

## 3단계: RunPod Serverless Endpoint 생성

### 3-1. Serverless 메뉴 이동

- [https://www.runpod.io/console/serverless](https://www.runpod.io/console/serverless) 접속
- **"+ New Endpoint"** 클릭

### 3-2. Endpoint 설정

| 설정 항목             | 값                                       | 설명                         |
| --------------------- | ---------------------------------------- | ---------------------------- |
| **Endpoint Name**     | `maumon-exaone`                          | 아무 이름                    |
| **Docker Image**      | `YOUR_DOCKERHUB_ID/maumon-exaone:latest` | 2단계에서 Push한 이미지      |
| **GPU Type**          | `24GB` → `RTX 4090` 또는 `RTX 3090` 선택 | EXAONE fp16에 필요           |
| **Active Workers**    | `0`                                      | 비용 절약 (요청 시에만 가동) |
| **Max Workers**       | `1` (또는 예산에 따라 2~3)               | 동시 처리 수                 |
| **Idle Timeout**      | `5` 초                                   | Worker 유휴 시 빠르게 종료   |
| **Execution Timeout** | `300` 초 (5분)                           | AI 추론 최대 대기 시간       |
| **FlashBoot**         | ✅ 활성화                                | Cold Start 최소화            |

### 3-3. Deploy

- **"Create"** 또는 **"Deploy"** 클릭
- Endpoint ID가 생성됨 (예: `mp2w6kb0npg0tp`)

### 3-4. API 테스트 (RunPod 콘솔에서)

Endpoint 상세 페이지 → **"Requests"** 탭 → **"Run"** 클릭

```json
{
  "input": {
    "text": "오늘 기분이 너무 안 좋아요",
    "mode": "reaction",
    "history": ""
  }
}
```

**예상 응답:**

```json
{
  "output": {
    "reaction": "많이 힘드신 하루를 보내셨나봐요... 어떤 일이 있었는지 이야기해 주시겠어요?"
  }
}
```

---

## 4단계: 백엔드 연동

### 4-1. RunPod API Key 확인

- [https://www.runpod.io/console/user/settings](https://www.runpod.io/console/user/settings)
- **API Keys** 섹션에서 키 복사

### 4-2. 서버 .env 업데이트

```bash
# OCI 서버 (217)에 SSH 접속 후:
nano /home/ubuntu/project/backend/.env

# 아래 두 줄을 추가/수정:
RUNPOD_API_KEY=rpa_XXXXXXXXXXXXXXXXXXXXX
RUNPOD_LLM_URL=https://api.runpod.ai/v2/YOUR_ENDPOINT_ID
```

### 4-3. Flask 서버 재시작

```bash
sudo systemctl restart flask
```

### 4-4. 연동 확인

```bash
sudo journalctl -u flask -f
# 채팅 시 아래 로그가 보이면 성공:
# 🚀 Sending Async request to RunPod Serverless...
# ✅ RunPod Job Completed!
```

---

## 💰 예상 비용

| 항목                     | 비용        | 비고               |
| ------------------------ | ----------- | ------------------ |
| **빌드 Pod** (1시간)     | ~$0.5~1.0   | 빌드 후 즉시 종료  |
| **Serverless 추론**      | ~$0.0004/초 | 사용한 만큼만 과금 |
| **1회 상담 응답** (10초) | ~$0.004     | 약 4원             |
| **하루 100회 상담**      | ~$0.40      | 약 550원           |

---

## ❓ 자주 묻는 질문

**Q: 빌드 중 디스크 부족 에러가 나요**
→ Container Disk을 100GB 이상으로 설정하세요.

**Q: Cold Start가 너무 오래 걸려요**
→ FlashBoot 활성화 + Active Workers를 1로 설정하면 항상 1대가 대기합니다 (비용 증가).

**Q: OOM 에러가 나요**
→ handler.py의 `max_model_len`을 4096 → 2048로 줄이세요.

**Q: 모델을 파인튜닝하고 싶어요**
→ 별도 학습 Pod에서 LoRA 파인튜닝 후, handler.py에 LoRA 어댑터 경로를 추가하면 됩니다.
