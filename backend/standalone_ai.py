import requests
import re
import random

def generate_analysis_reaction_standalone(user_text, mode='reaction', history=None):
    print(f"DEBUG: generate_analysis_reaction_standalone called. Mode={mode}, HistoryLen={len(history) if history else 0}")
    if not user_text: return None
    
    # 1. Sanitize
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '[EMAIL]', user_text)
    sanitized = text[:300]
    
    # 2. History Formatting
    context_str = ""
    if history:
        # history is expected to be a string or list of "User: ... / AI: ..."
        context_str = f"### [이전 대화 기록]\n{history}\n\n"

    # 3. Prompt Switching
    # Combined Prompt for continuous conversation
    prompt_text = (
        f"너는 다정하고 통찰력 있는 '심리 상담사'야.\n"
        f"{context_str}"
        f"### [내담자의 현재 말]: \"{sanitized}\"\n\n"
        "### [지시사항]:\n"
        "1. 이전 대화 기록이 있다면 그 흐름을 자연스럽게 이어서 답변해.\n"
        "2. 내담자의 감정을 읽어주고, 그 말이 타당함을 지지해줘.\n"
        "3. 딱딱한 분석보다는, 옆에서 이야기하듯 따뜻하고 부드러운 '해요체'를 사용해.\n"
        "4. 혼자 떠들지 말고, 내담자가 이야기를 계속 할 수 있도록 이끌어줘.\n"
        "5. 150자 이내로 간결하게.\n\n"
        "상담사 답변:"
    )
    
    try:
        payload = {
            "model": "maum-on-gemma",
            "prompt": prompt_text,
            "stream": False,
            "options": {
                "temperature": 0.7, 
                "num_predict": 180
            }
        }
        res = requests.post("http://localhost:11434/api/generate", json=payload, timeout=60)
        
        if res.status_code == 200:
            result = res.json().get('response', '').strip()
            if result.startswith('"') and result.endswith('"'):
                result = result[1:-1]
            if result: return result
            
    except Exception as e:
        print(f"❌ Standalone AI Error: {e}")
        
    # 3. Fallback (Mode Specific)
    fallbacks = []
    if mode == 'question':
        fallbacks = [
            "그렇군요. 혹시 조금 더 자세히 이야기해주실 수 있나요? 궁금해요.",
            "저런, 특별한 이유가 있었는지 듣고 싶어요.",
            "짧게 말씀하시니 더 깊은 속마음이 궁금해지네요. 편하게 털어놓아주세요.",
            "그 일이 내담자님께 어떤 의미였는지 조금만 더 들려주세요."
        ]
    else:
        fallbacks = [
            "말씀하신 내용에서 깊은 고민과 진심이 느껴지네요. 잘하고 계십니다.",
            "상황을 차분히 들여다보면, 그 안에서 스스로의 성장을 발견하실 수 있을 거예요.",
            "지금 느끼시는 감정은 매우 자연스러운 반응이에요. 스스로를 믿어보세요.",
            "이야기를 들어보니, 그동안 마음속에 담아두셨던 생각들이 많으셨던 것 같아 마음이 쓰이네요."
        ]
        
    return random.choice(fallbacks)

def analyze_chat_sentiment_background(user_text, ai_reaction):
    """
    Background Task: Analyze the chat turn to extract structured psychological data.
    Returns a dict with:
    - primary_emotion (str)
    - stress_level (int 1-10)
    - risk_flag (bool)
    - keywords (list)
    """
    print(f"DEBUG: Analyzing chat sentiment for: {user_text[:20]}...")
    if not user_text: return None
    
    # Sanitize
    sanitized = re.sub(r'[\w\.-]+@[\w\.-]+', '[EMAIL]', user_text)[:500]
    
    prompt_text = (
        f"분석할 발화:\n"
        f"내담자: \"{sanitized}\"\n"
        f"상담사 반응: \"{ai_reaction[:100]}...\"\n\n"
        "위 내담자의 발화를 심리학적으로 분석하여 다음 **JSON 형식**으로만 출력하시오.\n"
        "다른 말은 절대 하지 마시오.\n\n"
        "{\n"
        "  \"primary_emotion\": \"(60가지 감정 중 가장 핵심적인 감정 단어 1개, 한국어)\",\n"
        "  \"stress_level\": (1~10 사이 정수, 높을수록 스트레스 심함),\n"
        "  \"risk_flag\": (자살, 자해, 타해 위험이 감지되면 true, 아니면 false),\n"
        "  \"keywords\": [\"(핵심 키워드 1)\", \"(핵심 키워드 2)\"]\n"
        "}"
    )
    
    try:
        payload = {
            "model": "maum-on-gemma",
            "prompt": prompt_text,
            "stream": False,
            "options": {
                "temperature": 0.2, # Low temp for consistent JSON
                "num_predict": 120
            }
        }
        res = requests.post("http://localhost:11434/api/generate", json=payload, timeout=30)
        
        if res.status_code == 200:
            result_str = res.json().get('response', '').strip()
            # Extract JSON block if wrapped in code fences
            if "```json" in result_str:
                import re
                match = re.search(r"```json(.*?)```", result_str, re.DOTALL)
                if match: result_str = match.group(1)
            elif "```" in result_str:
                 match = re.search(r"```(.*?)```", result_str, re.DOTALL)
                 if match: result_str = match.group(1)

            import json
            data = json.loads(result_str)
            print(f"✅ Chat Analysis Result: {data}")
            return data
            
    except Exception as e:
        print(f"❌ Chat Analysis Error: {e}")
        return {
            "primary_emotion": "분석 실패",
            "stress_level": 0,
            "risk_flag": False,
            "keywords": []
        }
