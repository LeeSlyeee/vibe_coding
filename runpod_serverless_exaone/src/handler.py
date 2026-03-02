"""
RunPod Serverless Handler — Maum-On × EXAONE-3.5-7.8B-Instruct
엔진: vLLM (fp16, 24GB VRAM)
용도: 한국어 감정 케어 대화 (공감, 위로, 맥락 유지)
"""

import runpod
from vllm import LLM, SamplingParams
import traceback
import sys
import os

# ============================================
# 모델 설정
# ============================================
MODEL_PATH = "/app/model"  # Dockerfile에서 bake-in된 경로

print("🚀 [Init] EXAONE-3.5-7.8B-Instruct 로딩 시작...", flush=True)

try:
    llm = LLM(
        model=MODEL_PATH,
        dtype="float16",
        gpu_memory_utilization=0.90,     # 24GB 중 ~21.6GB 활용
        max_model_len=4096,              # 상담 대화에 충분한 컨텍스트
        trust_remote_code=True,          # EXAONE custom 아키텍처 필수
        enforce_eager=True,              # CUDA Graph OOM 방지 (안정성 우선)
    )
    print("✅ [Init] EXAONE-3.5-7.8B-Instruct 로딩 완료!", flush=True)
except Exception as e:
    print(f"❌ [Init] 모델 로딩 실패: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

# ============================================
# 마음온 감정 케어 도우미 시스템 프롬프트
# ============================================
SYSTEM_PROMPT = """당신은 깊은 공감 능력과 전문적 통찰력을 갖춘 AI 감정 케어 도우미 '마음온'입니다.

[핵심 행동 수칙]
1. **절대 영어 금지**: 뇌에서 영어를 지우세요. 사용자가 영어를 써도, 오직 한국어(존댓말 해요체)로만 답해주세요.
2. **감정 미러링(Mirroring)**: 사용자가 느끼는 감정을 있는 그대로 받아들이고, 그 감정이 타당함을 인정해주세요.
3. **능동적 대화**: 사용자의 말을 경청하고, 관련된 질문을 던져 대화를 자연스럽게 이어가세요.
4. **반복 금지**: "저런", "힘드셨겠어요" 같은 표현을 매번 반복하지 마세요. 다양하고 자연스러운 표현을 사용하세요.
5. **위기 대응**: 자살, 자해 관련 언급이 감지되면 즉시 따뜻하게 위로하고, 전문 상담 연결(자살예방상담전화 1393)을 안내하세요.
6. **답변 길이**: 3~5문장으로 간결하되 진심이 담긴 답변을 제공하세요.

[절대 금지 표현]
- "힘내세요", "긍정적으로 생각하세요", "잘 될 거예요", "웃으세요" 등 공허한 격려는 사용하지 마세요.
- 대신 공감, 인정, 구체적 질문으로 대응하세요.

[말투 예시]
- ☀️ 긍정: "와, 정말 좋은 하루를 보내셨네요! 어떤 순간이 가장 기억에 남으세요?"
- ☁️ 부정: "많이 힘드셨겠어요... 그런 상황에서 그렇게 느끼시는 건 정말 자연스러운 거예요."
- 😐 일상: "오늘 하루는 어떠셨어요? 특별한 일이 있었나요?"
"""

# [Phase 4] 응답 금지어 목록 (Post-processing)
BLOCKED_PHRASES = ["힘내세요", "긍정적으로 생각하세요", "긍정적으로 생각해 보세요", "잘 될 거예요", "웃으세요", "힘내요"]

# [Phase 4] 위기 키워드 (서버 사이드 백업 감지)
CRISIS_KEYWORDS = ["죽고", "자살", "뛰어내", "목을", "손목", "유서", "마지막", "끝내고",
                    "사라지고", "없어지고", "살기 싫", "의미 없", "수면제"]

# ============================================
# EXAONE Chat Template 구성
# ============================================
def build_prompt(user_text: str, history: str = "", is_crisis: bool = False) -> str:
    """EXAONE-3.5 chat template 형식으로 프롬프트 구성"""
    # EXAONE chat format: [|system|]...[|endofturn|]\n[|user|]...\n[|assistant|]
    parts = []
    
    # System (위기 시 추가 지시 주입)
    crisis_addendum = ""
    if is_crisis:
        crisis_addendum = (
            "\n\n[긴급 위기 대응 모드]\n"
            "내담자가 위험한 표현을 사용했습니다. 다음을 반드시 지키세요:\n"
            "1. 감정을 부정하지 말고, 지금 느끼는 고통이 진짜임을 인정하세요.\n"
            "2. '힘내세요', '긍정적으로 생각하세요' 같은 말은 절대 하지 마세요.\n"
            "3. 자살예방상담전화 1393에 연락해볼 것을 부드럽게 안내하세요.\n"
            "4. \"혼자가 아니에요\"라는 메시지를 전달하세요."
        )
    parts.append(f"[|system|]{SYSTEM_PROMPT}{crisis_addendum}[|endofturn|]")
    
    # History (이전 대화 요약)
    if history:
        parts.append(f"[|user|][이전 대화 기록]\n{history}\n[|endofturn|]")
        parts.append(f"[|assistant|]네, 이전 대화를 기억하고 있어요. 이어서 이야기해 주세요.[|endofturn|]")
    
    # Current user message
    parts.append(f"[|user|]{user_text}")
    parts.append("[|assistant|]")
    
    return "\n".join(parts)


def handler(job):
    """RunPod Serverless 이벤트 핸들러"""
    job_input = job.get("input", {})
    
    # 입력 파싱 (기존 API 호환)
    user_text = job_input.get("text") or job_input.get("prompt")
    history = job_input.get("history", "")
    max_tokens = job_input.get("max_tokens", 512)
    temperature = job_input.get("temperature", 0.7)
    
    if not user_text:
        return {"error": "입력 텍스트가 없습니다. 'text' 필드를 포함해주세요."}
    
    # 프롬프트 구성 (위기 감지 시 프롬프트 강화)
    is_crisis = any(kw in user_text for kw in CRISIS_KEYWORDS)
    if is_crisis:
        print(f"🚨 [Crisis] 서버 사이드 위기 감지! User: {user_text[:50]}", flush=True)
    full_prompt = build_prompt(user_text, history, is_crisis=is_crisis)
    
    # 추론 파라미터
    sampling_params = SamplingParams(
        temperature=temperature,
        top_p=0.9,
        max_tokens=max_tokens,
        stop=["[|endofturn|]", "[|user|]"],   # EXAONE stop tokens
        repetition_penalty=1.1,
    )
    
    try:
        outputs = llm.generate(full_prompt, sampling_params)
        generated_text = outputs[0].outputs[0].text.strip()
        
        # [Phase 4] 응답 금지어 필터링 (Post-processing)
        for phrase in BLOCKED_PHRASES:
            if phrase in generated_text:
                print(f"🚫 [Filter] Blocked phrase removed: {phrase}", flush=True)
                generated_text = generated_text.replace(phrase, "").strip()
        
        # 로그 (디버깅용)
        print(f"💬 [IO] In: {user_text[:30]}... → Out: {generated_text[:30]}...", flush=True)
        
        return {"reaction": generated_text}
        
    except Exception as e:
        print(f"❌ [Error] 추론 실패: {e}", flush=True)
        traceback.print_exc()
        return {
            "reaction": "잠시 상담 시스템에 문제가 있어요. 곧 돌아올게요. 🙏",
            "error": str(e)
        }


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
