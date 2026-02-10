import requests
import os
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

class ChatReactionView(APIView):
    # 테스트 편의를 위해 AllowAny로 하되, 필요시 IsAuthenticated로 변경
    # iOS APIService.swift에서 토큰을 보내므로 IsAuthenticated 권장되나, 데모용이라면 AllowAny도 무방
    permission_classes = [AllowAny] 
    
    def post(self, request):
        """
        iOS 앱 -> 217 서버 -> RunPod (vLLM) -> 217 서버 -> iOS 앱
        """
        user_text = request.data.get("text", "")
        history = request.data.get("history", "")
        
        # RunPod vLLM 설정
        # .env 혹은 하드코딩 (사용자에게 수정 가이드 필요)
        # 예: https://IDs-8000.proxy.runpod.net/v1
        runpod_base_url = os.environ.get("RUNPOD_LLM_URL", "https://api.runpod.ai/v2/YOUR_ENDPOINT/openai/v1") 
        runpod_api_key = os.environ.get("RUNPOD_API_KEY", "EMPTY")
        
        # vLLM (OpenAI Compatible) 엔드포인트
        target_url = f"{runpod_base_url.rstrip('/')}/chat/completions"
        
        # 프롬프트 구성 (history + user_text)
        # 이미 history에 대화 내역이 formatting되어 온다고 가정하거나, 여기서 재구성
        # vLLM은 messages 배열을 원하므로, history 문자열을 파싱하거나 통째로 system/user prompt로 넣어야 함.
        # iOS 앱(AppChatView.swift)은 history를 Plain Text로 보냄.
        
        messages = [
            {"role": "system", "content": "당신은 따뜻한 공감을 주는 심리 상담사 '하루온'입니다. 한국어로만 답변하세요."},
            {"role": "user", "content": f"{history}\nUser: {user_text}"}
        ]

        payload = {
            "model": "meta-llama/Meta-Llama-3-8B-Instruct", # 모델명은 vLLM 로드 시 정해짐 (확인 필요) 혹은 'slyeee/haruon-llama3-8b-lora' 등
            # vLLM은 보통 모델명을 무시하거나 로드된 모델을 씀. 하지만 필수 파라미터.
            "messages": messages,
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        if runpod_api_key != "EMPTY":
            headers["Authorization"] = f"Bearer {runpod_api_key}"

        try:
            print(f"🚀 [ChatView] Forwarding to RunPod: {target_url}")
            
            # vLLM 호출
            # 타임아웃 60초 (모델 로딩/연산 시간 고려)
            resp = requests.post(target_url, json=payload, headers=headers, timeout=60)
            
            if resp.status_code == 200:
                data = resp.json()
                # OpenAI 포맷: choices[0].message.content
                ai_reply = data["choices"][0]["message"]["content"]
                return Response({"reaction": ai_reply})
            else:
                print(f"❌ [ChatView] RunPod Error: {resp.status_code} {resp.text}")
                # Mockup Response (RunPod 연결 실패 시 비상용)
                return Response({
                    "reaction": "(서버 연동 실패) RunPod 접속에 문제가 있습니다. 관리자에게 문의하세요.", 
                    "debug_error": resp.text
                }, status=502)
                
        except Exception as e:
            print(f"❌ [ChatView] Exception: {e}")
            return Response({"reaction": f"(서버 오류) {str(e)}"}, status=500)
