#!/bin/bash
echo "🚀 [Start] Maum-On × EXAONE-3.5-7.8B Container Started!"

# 모델 파일 확인
if [ -d "/app/model" ] && [ -f "/app/model/config.json" ]; then
    echo "✅ [Start] EXAONE 모델 파일 확인 완료"
    MODEL_SIZE=$(du -sh /app/model | cut -f1)
    echo "📦 [Start] 모델 크기: $MODEL_SIZE"
else
    echo "❌ [Start] 모델 파일 없음! /app/model 경로를 확인하세요."
    ls -la /app/
    exit 1
fi

echo "🚀 [Start] Handler 시작..."
python3 -u /app/handler.py
