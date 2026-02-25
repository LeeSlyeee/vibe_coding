# ============================================
# Maum-On × EXAONE-3.5-7.8B RunPod Serverless
# vLLM Engine + fp16 (24GB VRAM)
# ============================================

# vLLM 공식 이미지 (CUDA 지원)
FROM vllm/vllm-openai:v0.8.3

WORKDIR /app

# RunPod SDK 설치
RUN pip install runpod huggingface_hub

# 핸들러 복사
COPY src/handler.py /app/handler.py
COPY src/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# [빌드 시 모델 다운로드] — Docker 이미지에 bake-in하여 Cold Start 제거
# HF_TOKEN은 빌드 시 ARG로 전달 (EXAONE은 gated=false라 불필요하지만 안전장치)
ARG HF_TOKEN=""
RUN python3 -c "\
from huggingface_hub import snapshot_download; \
snapshot_download( \
    repo_id='LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct', \
    local_dir='/app/model', \
    token='${HF_TOKEN}' if '${HF_TOKEN}' else None, \
    ignore_patterns=['*.pth', '*.pt', '*.gguf'] \
); \
print('✅ EXAONE-3.5-7.8B-Instruct 다운로드 완료')"

ENTRYPOINT ["/app/start.sh"]
CMD []
