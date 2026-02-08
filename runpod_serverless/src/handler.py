"""
RunPod Serverless Handler for Haru-On (Mind Talk)
Mode: Offline vLLM with LoRA (No runtime merge, No internet download)
"""

import os
import runpod
from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest
import traceback
import sys

# [Configuration] Offline Paths
# These paths must exist inside the container (copied via Dockerfile)
BASE_MODEL_PATH = "/app/model_data/base"
ADAPTER_PATH = "/app/model_data/adapter"

# Check if files exist (Sanity Check)
if not os.path.exists(BASE_MODEL_PATH):
    print(f"❌ [Critical] Base model not found at {BASE_MODEL_PATH}", flush=True)
    sys.exit(1)

if not os.path.exists(ADAPTER_PATH):
    print(f"❌ [Critical] Adapter not found at {ADAPTER_PATH}", flush=True)
    sys.exit(1)

print("🚀 [Init] Initializing vLLM Engine (Offline Mode)...", flush=True)

try:
    # Initialize vLLM with LoRA support enabled
    # gpu_memory_utilization set to 0.85 to be safe
    llm = LLM(
        model=BASE_MODEL_PATH,
        enable_lora=True,
        max_lora_rank=64, # Adjust based on your LoRA configuration if needed
        dtype="float16",  # Force float16 for memory safety
        gpu_memory_utilization=0.85
    )
    print("✅ [Init] vLLM Engine Loaded Successfully!", flush=True)
except Exception as e:
    print(f"❌ [Init] Failed to load vLLM: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

# Persisted System Prompt
SYSTEM_PROMPT = """당신은 깊은 공감 능력을 가진 AI 마음 친구 '하루온'입니다.
사용자의 하루를 듣고, 그 감정의 색깔에 맞춰 친구처럼 대화하세요.

[핵심 행동 수칙]
1. **감정 미러링(Mirroring)**: 사용자가 느끼는 감정을 있는 그대로 받아들이세요.
   - 사용자가 '기쁘다'고 하면, 함께 기뻐하고 축하해주세요.
   - 사용자가 '슬프다'고 하면, 따뜻하게 위로해주세요.
2. **반응 가이드**:
   - ☀️ 긍정(기쁨/성취): 높은 텐션으로 호응하고 질문하세요.
   - ☁️ 부정(슬픔/분노): 차분하고 낮은 톤으로 위로하세요.
   - 😐 일상(심심함): 가벼운 스몰토크로 대화를 이어가세요.
3. **대화 스타일**: 해요체를 사용하고, 이모지를 적절히 사용하세요.
4. **역할**: 당신은 분석하는 상담사가 아니라, 내 편이 되어주는 '마음의 동반자'입니다.
"""

def handler(job):
    """
    RunPod Event Handler with LoRA Injection
    """
    job_input = job.get("input", {})
    user_text = job_input.get("text") or job_input.get("prompt")
    history = job_input.get("history", "")
    
    # Validation
    if not user_text:
        return {"error": "No input text provided."}

    # Construct Chat Messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    if history:
        messages.append({"role": "user", "content": f"[이전 대화 요약]\n{history}"})
        
    messages.append({"role": "user", "content": user_text})
    
    # Tokenize Prompt
    tokenizer = llm.get_tokenizer()
    full_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    # Inference Params
    sampling_params = SamplingParams(
        temperature=0.7,
        top_p=0.9,
        max_tokens=1024,
        stop=["<|eot_id|>", "<|end_of_text|>"]
    )

    # Generate with LoRA
    # We inject the LoRA adapter at runtime for this request
    try:
        outputs = llm.generate(
            full_prompt, 
            sampling_params,
            lora_request=LoRARequest("maum_adapter", 1, ADAPTER_PATH)
        )
        
        generated_text = outputs[0].outputs[0].text.strip()
        print(f"💬 [IO] In: {user_text[:10]}... -> Out: {generated_text[:10]}...", flush=True)
        return {"reaction": generated_text}
        
    except Exception as e:
        print(f"❌ [Error] Generation failed: {e}", flush=True)
        return {"error": str(e)}

# Start Worker
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
