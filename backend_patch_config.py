import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

class GetConfigView(APIView):
    # 앱 초기 실행 시 필요한 설정값 반환
    permission_classes = [AllowAny] # 누구나 접근 가능 (앱 실행 시 필요하므로)

    def get(self, request):
        return Response({
            "huggingface": {
                "repo_id": "slyeee/maum-on-gemma-2b",
                "token": os.getenv("HF_TOKEN", "") 
            },
            "server_status": "active"
        })
