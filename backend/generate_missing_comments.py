
import requests
import json
import re

def generate_ai_comment_batch(diary_data):
    """
    diary_data: dict with date, event, emotion_desc, etc.
    Returns: a generated AI comment string
    """
    
    # Construct Prompt
    # We want a summary/comment on the day's record.
    
    content = f"""
    [일기 내용]
    날짜: {diary_data.get('date')}
    사건: {diary_data.get('event')}
    감정: {diary_data.get('emotion_desc')}
    의미: {diary_data.get('emotion_meaning')}
    스스로에게 한 말: {diary_data.get('self_talk')}
    """
    
    prompt_text = (
        f"너는 심리 상담사 '하루온'이야. 아래 회원의 일기를 읽고, 따뜻하고 공감하는 코멘트를 남겨줘.\n"
        f"{content}\n\n"
        "### 지시사항:\n"
        "1. 회원의 감정을 깊이 이해하고 위로하거나 격려해줘.\n"
        "2. 사건보다는 감정과 그 의미에 집중해줘.\n"
        "3. 부드러운 '해요체'를 사용해.\n"
        "4. 200자 이내로 작성해.\n"
        "5. 답변만 출력해.\n\n"
        "상담사 코멘트:"
    )
    
    try:
        payload = {
            "model": "haru-on-gemma",
            "prompt": prompt_text,
            "stream": False,
            "options": {
                "temperature": 0.7, 
                "num_predict": 300
            }
        }
        res = requests.post("http://localhost:11434/api/generate", json=payload, timeout=60)
        if res.status_code == 200:
             return res.json().get('response', '').strip()
    except Exception as e:
        print(f"AI Gen Error: {e}")
        return "오늘 하루도 고생 많으셨어요. 당신의 마음을 항상 응원합니다. (AI 연결 불안정)"

