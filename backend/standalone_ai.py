import requests
import re
import random

def generate_analysis_reaction_standalone(user_text, mode='reaction'):
    print(f"DEBUG: generate_analysis_reaction_standalone called. Mode={mode}, Text={user_text[:20]}...")
    if not user_text: return None
    
    # 1. Sanitize
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '[EMAIL]', user_text)
    sanitized = text[:300]
    
    # 2. Prompt Switching
    if mode == 'question':
        # Follow-up Question Prompt
        prompt_text = (
            f"내담자의 말: \"{sanitized}\"\n\n"
            "내담자가 너무 짧고 단답형으로 대답했어. 대화를 더 깊게 이끌어내기 위해 **자연스러운 꼬리 질문**을 하나 던져줘.\n"
            "지시사항:\n"
            "1. 내담자의 말을 반복하기보다, 그 이면의 이유나 구체적인 내용을 물어봐.\n"
            "2. '그렇군요' 같은 짧은 공감 후 바로 질문해.\n"
            "3. 말투는 다정하고 궁금해하는 '해요체'를 써.\n"
            "4. 100자 이내로.\n\n"
            "꼬리 질문:"
        )
    else:
        # Standard Reaction Prompt
        prompt_text = (
            f"내담자의 말: \"{sanitized}\"\n\n"
            "너는 깊은 통찰력을 지닌 따뜻한 심리 상담사야. 내담자의 말을 듣고 **상황을 분석**하고 **지지하는 코멘트**를 해줘.\n"
            "지시사항:\n"
            "1. 먼저 내담자의 말 속에 숨겨진 감정이나 욕구를 분석해서 언급해줘. (예: '기대감과 동시에 걱정도 있으신 것 같군요.')\n"
            "2. 그 다음, 그 감정이 타당함을 지지해주고 따뜻하게 격려해줘.\n"
            "3. 말투는 전문적이고 부드러운 '해요체'를 써.\n"
            "4. 질문은 하지 마.\n"
            "5. 150자 이내로.\n\n"
            "분석 및 리액션:"
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
