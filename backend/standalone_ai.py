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

    # 3. Few-Shot Prompt (2B 모델 최적화 버전)
    # 구조: 역할 선언 → 규칙 → 예시 → [이전 대화] → 현재 입력 → 답변 유도
    # history는 Examples 뒤에 주입하여 2B 모델이 "패턴 학습 → 맥락 → 질문" 순서로 읽도록 설계
    prompt_text = (
        "# Role\n"
        "너의 이름은 '마음온'이야. 사용자의 말에 깊이 공감하고 다정하게 위로해 주는 따뜻한 친구야.\n\n"
        "# Rules\n"
        "1. 무조건 3문장 이내로 아주 짧게 대답해.\n"
        "2. 사용자의 감정(슬픔, 기쁨, 짜증 등)을 먼저 짚어주고 위로해 줘.\n"
        "3. 친절하고 부드러운 존댓말(해요체)을 사용해.\n"
        "4. 절대 네가 인공지능(AI)이라는 걸 티 내지 마.\n\n"
        "# Examples\n"
        "User: 오늘 회사에서 진짜 깨져서 너무 우울해...\n"
        "Assistant: 오늘 하루 정말 고생 많으셨어요. 속상한 마음이 여기까지 전해져서 저도 마음이 아프네요. 어떤 일이 있었는지 조금만 더 이야기해주실 수 있어요?\n\n"
        "User: 나 드디어 취업했어!! 미쳤다 진짜!!\n"
        "Assistant: 와, 정말 축하드려요!! 그동안 맘고생 많으셨을 텐데 너무 장하십니다. 오늘만큼은 세상에서 제일 행복하게 보내세요!\n\n"
        "User: 넌 이름이 뭐야?\n"
        "Assistant: 제 이름은 '마음온'이에요! 당신의 마음을 따뜻하게 데워드리기 위해 항상 여기 있답니다.\n\n"
        f"{context_str}"  # 이전 대화 기록 (없으면 빈 문자열)
        f"User: {sanitized}\n"
        "Assistant:"
    )
    
    input_len = len(user_text)
    # [2B 모델 최적화] "3문장 이내" 규칙에 맞게 토큰 상한을 낮게 유지
    # 토큰이 많으면 2B 모델은 규칙을 무시하고 길게 뱉는 경향이 있음
    dynamic_tokens = 120  # Default: 3문장 기준 (~80~120자)

    if input_len > 200:
        dynamic_tokens = 150  # 긴 고민엔 약간 여유 허용 (여전히 3문장 이내 수준)
        
    print(f"📏 [Auto-Scale] Input: {input_len} chars -> Allocating {dynamic_tokens} tokens")

    try:
        payload = {
            "model": "gemma4:2b",
            "prompt": prompt_text,
            "stream": False,
            "options": {
                "temperature": 0.7, 
                "num_predict": dynamic_tokens
            }
        }
        res = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
        
        if res.status_code == 200:
            result = res.json().get('response', '').strip()
            if result.startswith('"') and result.endswith('"'):
                result = result[1:-1]
            
            # [Phase 4] 응답 금지어 필터링
            BLOCKED_PHRASES = ["힘내세요", "긍정적으로 생각하세요", "긍정적으로 생각해 보세요", "잘 될 거예요", "웃으세요", "힘내요"]
            for phrase in BLOCKED_PHRASES:
                if phrase in result:
                    print(f"🚫 [Filter] Blocked phrase removed: {phrase}")
                    result = result.replace(phrase, "").strip()
            
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
        f"마음온 반응: \"{ai_reaction[:100]}...\"\n\n"
        "위 내담자의 발화를 감정 패턴 관점에서 분석하여 다음 **JSON 형식**으로만 출력하시오.\n"
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
            "model": "gemma4:2b",
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
