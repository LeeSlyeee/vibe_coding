#!/bin/bash

# 0. 환경 변수 설정 (필수)
export HF_TOKEN="YOUR_HUGGINGFACE_TOKEN_HERE"
export HF_HOME=/Volumes/DATA2/vibe_coding/huggingface_cache

# 1. 모델 병합 (Fuse)
# 학습된 어댑터를 원본 모델과 합쳐서 고해상도(F16) 모델로 저장합니다.
echo "🔄 [1/2] 모델 병합 중 (Fusing)..."
~/Library/Python/3.9/bin/mlx_lm.fuse \
  --model google/gemma-2-2b-it \
  --adapter-path adapters_maumon_full \
  --save-path models/maum-on-gemma-2b-v2-full-f16

# 2. 4비트 양자화 (Quantization)
# 병합된 모델을 모바일용 1.4GB 사이즈로 압축합니다.
echo "📦 [2/2] 4비트 양자화 중 (Quantizing)..."
~/Library/Python/3.9/bin/mlx_lm.convert \
  --hf-path models/maum-on-gemma-2b-v2-full-f16 \
  --mlx-path models/maum-on-gemma-2b-v2-full-4bit \
  -q \
  --q-bits 4

echo "✅ 모든 작업 완료! 4비트 모델 위치: models/maum-on-gemma-2b-v2-full-4bit"
