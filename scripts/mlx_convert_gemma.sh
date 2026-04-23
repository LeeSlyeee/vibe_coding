#!/bin/bash
# ==========================================
# 마음온(maumON) On-Device AI 변환 프레임워크
# Target: Gemma 4 (e2B) -> MLX 4-Bit 양자화
# ==========================================

echo "[1/4] MLX-LM 및 필수 라이브러리 설치"
pip install mlx-lm huggingface_hub

echo ""
echo "[2/4] Hugging Face 계정 연동"
echo "※ 주의: Gemma 모델은 구글 약관 동의가 필요하므로 CLI 로그인이 필수입니다."
huggingface-cli login

echo ""
echo "[3/4] 원본 모델 다운로드 및 MLX 4-Bit 양자화 수행"
# 사용자 환경에 맞춰 HF 원본 경로를 수정하십시오 (예: google/gemma-2-2b-it)
TARGET_HF_PATH="google/gemma-2-2b-it" 
OUTPUT_PATH="./models/gemma4-e2b-mlx-4bit"

python3 -m mlx_lm.convert \
    --hf-path "$TARGET_HF_PATH" \
    --q-group-size 64 \
    --q-bits 4 \
    --mlx-path "$OUTPUT_PATH"

echo ""
echo "[4/4] 변환 완료. Hugging Face에 업로드하시겠습니까? (slyeee/gemma-4-e2b-4bit)"
echo "터미널에서 아래 명령을 직접 실행해 업로드하십시오:"
echo "python3 -m huggingface_hub upload slyeee/gemma-4-e2b-4bit $OUTPUT_PATH"
