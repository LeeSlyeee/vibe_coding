
# 2. Start Fine-Tuning (MLX)
# ==============================================================================
# 모델: google/gemma-2-2b-it (2B 경량화 모델, Instruction Tuned)
# 데이터: data/final_train.jsonl (위에서 생성한 최종 데이터)
# ==============================================================================

# [학습 파라미터 추천]
# - iters: 600~1000 (데이터 5천개 기준 1 Epoch 정도)
# - batch-size: 4 (M1/M2 맥북 메모리 고려)
# - lora-layers: 16 (전체 레이어 튜닝으로 성능 극대화)
# - learning-rate: 1e-5 (안정적인 학습)

echo "Starting Fine-tuning..."
python -m mlx_lm.lora \
  --model google/gemma-2-2b-it \
  --train \
  --data ./data \
  --iters 1000 \
  --batch-size 4 \
  --lora-layers 16 \
  --learning-rate 1e-5 \
  --adapter-path adapters_maumon \
  --save-every 100

echo "✅ Fine-tuning Completed!"

# 3. Fuse & Test
# ==============================================================================
# 학습된 LoRA 어댑터를 원본 모델과 합쳐서 최종 모델 생성
# ==============================================================================
# python -m mlx_lm.fuse \
#   --model google/gemma-2-2b-it \
#   --adapter-path adapters_maumon \
#   --save-path models/haruON-gemma-2b-v1
