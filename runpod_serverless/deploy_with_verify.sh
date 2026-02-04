#!/bin/bash
set -e # 에러 발생 시 즉시 중단

# Offline 모드이므로 HF_TOKEN 불필요
# Build Argument도 제거
IMAGE_NAME="slyeee/runpod-serverless-v1:latest"

echo "=========================================="
echo "🚀 1. 오프라인 빌드 시작 (Offline Build)"
echo "   - 로컬 모델 파일(15GB)을 포함하여 빌드합니다."
echo "   - 시간이 꽤 걸릴 수 있습니다."
echo "=========================================="

# Docker Build (No Build Args needed)
docker build --platform linux/amd64 -t $IMAGE_NAME .

echo ""
echo "=========================================="
echo "🧐 2. 로컬 이미지 검증 (Verification)"
echo "   - 모델 파일이 제대로 들어갔는지 확인합니다."
echo "=========================================="

# 컨테이너 내부의 파일 존재 여부 확인
# /app/model_data/adapter/adapter_config.json
if docker run --platform linux/amd64 --rm --entrypoint ls $IMAGE_NAME /app/model_data/adapter/adapter_config.json > /dev/null 2>&1; then
    echo "✅ [검증 성공] 이미지 내부에 모델 파일이 확실히 있습니다."
    
    # 용량 확인용 출력
    echo "📂 모델 파일 목록 및 용량:"
    docker run --platform linux/amd64 --rm --entrypoint ls $IMAGE_NAME -lh /app/model_data/base
else
    echo "❌ [검증 실패] 이미지 내부에 모델 파일이 없습니다!"
    echo "🚫 배포를 중단합니다."
    exit 1
fi

echo ""
echo "=========================================="
echo "☁️ 3. Docker Hub 푸시 (Push)"
echo "   - 검증된 이미지만 배포합니다."
echo "=========================================="

docker push $IMAGE_NAME

echo ""
echo "🎉 [완료] 배포가 성공적으로 끝났습니다."
echo "RunPod에서 해당 파드를 재시작(Stop -> Start) 해주세요."
