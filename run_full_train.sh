#!/bin/bash

# 1. 환경 변수 설정
export HF_TOKEN="YOUR_HUGGINGFACE_TOKEN_HERE"
export HF_HOME=/Volumes/DATA2/vibe_coding/huggingface_cache

# 2. 풀 파인튜닝 실행 (약 3.5~4시간 소요 예상)
# 배치 사이즈 2, 반복 횟수 13,000, 500스텝마다 저장 (lora-layers 옵션 제거)
~/Library/Python/3.9/bin/mlx_lm.lora \
  --model google/gemma-2-2b-it \
  --train \
  --data ./data \
  --iters 13000 \
  --batch-size 2 \
  --learning-rate 2e-5 \
  --adapter-path adapters_maumon_full \
  --save-every 500
