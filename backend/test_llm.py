import requests
import json

url = "http://localhost:11434/api/generate"

text = "수면 상태: 잘 잤어\n사건: 오늘은 혜진씨의 리부트 프로젝트를 열심히개발했어\n감정: 역시 개발은 재미있다\n생각: 뭔가를 만드는일은 재미있는 일이다\n나에게 하는 말: 넌 지금 매우 잘하고 있어"

prompt_text = (
    f"너는 심리 상담 전문가야. 다음 내담자의 일기를 읽고 분석해줘.\n"
    f"내담자의 현재 상태: 안정(Normal) (Level 1)\n"
    f"\n"
    f"### [오늘의 일기 데이터]:\n{text}\n\n"
    f"### [분석 지침]:\n"
    f"1. 내담자의 '수면 상태'와 '감정'의 연관성을 깊이 있게 분석해줘.\n"
    f"2. 만약 내담자가 '죽고 싶다' 등 위험한 표현을 했거나([]), 감정이 오랫동안 가라앉아 있다면 '추가 질문'을 생성해줘.\n"
    f"3. 단순히 내용을 요약하지 말고, 전문적인 심리 분석 코멘트를 해줘.\n\n"
    f"### [필수 답변 형식]:\n"
    f"Emotion: ('행복', '우울', '분노', '평온', '불안', '당황' 중 하나, 반드시 한국어로)\n"
    f"Confidence: (0~100 숫자만)\n"
    f"NeedFollowup: (YES 또는 NO)\n"
    f"Question: (NeedFollowup이 YES일 때만, 내담자에게 물어볼 추가 질문 1문장. 아니면 'None')\n"
    f"Comment: (수면 상태를 언급하며 100자 이내의 따뜻한 한국어 위로)\n"
    f"반드시 위 형식만 지켜서 답변해."
)

payload = {
    "model": "haruON-gemma",
    "prompt": prompt_text,
    "stream": False,
    "options": {
        "temperature": 0.3, 
        "num_predict": 160
    }
}

print("Sending request...")
try:
    response = requests.post(url, json=payload, timeout=60)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json().get('response')}")
except Exception as e:
    print(f"Error: {e}")
