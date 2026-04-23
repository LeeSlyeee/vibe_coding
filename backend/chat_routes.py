from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User
import re
import ast

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/api/chat/reaction', methods=['POST'])
@jwt_required()
def chat_reaction():
    """
    AI 공감 반응 생성 API
    iOS sendChatMessage()에서 호출
    
    Request: {"text": "사용자 메시지", "mode": "reaction", "history": "이전 대화"}
    Response: {"reaction": "AI 응답 메시지"}
    """
    data = request.get_json()
    if not data or not data.get('text'):
        return jsonify({"error": "text 필드가 필요합니다."}), 400
    
    user_text = data['text']
    mode = data.get('mode', 'reaction')
    history = data.get('history', '')
    
    current_user_id = int(get_jwt_identity())
    
    try:
        from standalone_ai import generate_analysis_reaction_standalone
        result = generate_analysis_reaction_standalone(user_text, mode=mode, history=history)
        
        if result and isinstance(result, str):
            reaction_text = result
        elif result and isinstance(result, dict):
            reaction_text = result.get('reaction', result.get('response', str(result)))
        else:
            reaction_text = "지금은 제가 잘 이해하지 못했어요. 조금 더 이야기해주실 수 있을까요? 🤔"
        
        # [Optional] 채팅 로그 저장
        try:
            from models import db, ChatLog
            import uuid
            session_id = request.headers.get('X-Session-Id', str(uuid.uuid4())[:8])
            
            # 사용자 메시지 저장
            user_log = ChatLog(
                user_id=current_user_id,
                session_id=session_id,
                message=user_text[:500],
                sender='user'
            )
            # AI 응답 저장
            ai_log = ChatLog(
                user_id=current_user_id,
                session_id=session_id,
                message=reaction_text[:500],
                sender='ai'
            )
            db.session.add(user_log)
            db.session.add(ai_log)
            db.session.commit()
        except Exception as log_err:
            print(f"⚠️ [Chat] Log save failed (non-critical): {log_err}")
        
        return jsonify({"reaction": reaction_text}), 200
        
    except Exception as e:
        print(f"❌ [Chat] AI Generation Error: {e}")
        return jsonify({
            "reaction": "잠시 시스템에 문제가 있어요. 곧 돌아올게요. 🙏"
        }), 200  # 200으로 반환 (iOS가 에러 처리할 수 있도록 graceful)


@chat_bp.route('/api/chat/analysis-report', methods=['POST'])
@jwt_required()
def analysis_report():
    """
    AI 분석 리포트 생성 API (RunPod -> Ollama 자동 Fallback)
    
    Request: {
        "diaries": [{"date": "...", "content": "...", "mood_level": 3, ...}],
        "mode": "short" | "long"
    }
    Response: {"report": "분석 결과 텍스트"}
    """
    data = request.get_json()
    if not data or not data.get('diaries'):
        return jsonify({"error": "diaries 필드가 필요합니다."}), 400
    
    diaries = data['diaries']
    mode = data.get('mode', 'short')
    
    # [Fix] 사용자 이름 조회 (LLM이 주변 인물을 내담자로 오인하는 버그 방지)
    current_user_id = int(get_jwt_identity())
    user_display_name = "내담자"
    try:
        user_obj = User.query.get(current_user_id)
        if user_obj:
            user_display_name = user_obj.real_name or user_obj.nickname or "내담자"
    except Exception as name_err:
        print(f"⚠️ [Analysis Report] 사용자 이름 조회 실패: {name_err}")
    
    # 일기 데이터를 텍스트로 변환
    diary_text_parts = []
    for d in diaries[:30]:
        date = d.get('date', '')
        content = d.get('content', '')
        mood = d.get('mood_level', 3)
        weather = d.get('weather', '')
        if content:
            diary_text_parts.append(f"[{date}] 기분:{mood}/5 날씨:{weather} | {content[:200]}")
    
    diary_summary = "\n".join(diary_text_parts)
    
    if mode == 'long':
        prompt = (
            "너는 다정하고 통찰력 있는 감정 케어 AI '마음온'이야.\n"
            f"현재 분석 대상 내담자(일기를 쓴 사람)의 이름은 '{user_display_name}'이야.\n"
            "일기에 등장하는 다른 사람 이름은 내담자의 '주변 인물'이지 내담자 본인이 아니야. "
            f"반드시 '{user_display_name}씨' 또는 '내담자'라고만 지칭해.\n"
            f"아래는 {user_display_name}씨의 최근 일기 기록이야:\n\n{diary_summary}\n\n"
            "### 지시사항:\n"
            "1. 장기적인 감정 패턴과 변화 추세를 분석해줘.\n"
            "2. 반복되는 감정 트리거(요일, 날씨, 사건 등)를 찾아줘.\n"
            "3. 회복탄력성이나 긍정적 변화가 보이면 칭찬해줘.\n"
            "4. 주의가 필요한 패턴이 있으면 부드럽게 알려줘.\n"
            "5. 따뜻한 해요체로 300자 내외로 작성해.\n\n"
            "장기 패턴 분석:"
        )
    else:
        prompt = (
            "너는 다정하고 통찰력 있는 감정 케어 AI '마음온'이야.\n"
            f"현재 분석 대상 내담자(일기를 쓴 사람)의 이름은 '{user_display_name}'이야.\n"
            "일기에 등장하는 다른 사람 이름은 내담자의 '주변 인물'이지 내담자 본인이 아니야. "
            f"반드시 '{user_display_name}씨' 또는 '내담자'라고만 지칭해.\n"
            f"아래는 {user_display_name}씨의 최근 일기 기록이야:\n\n{diary_summary}\n\n"
            "### 지시사항:\n"
            "1. 전반적인 감정 상태를 요약해줘.\n"
            "2. 특히 눈에 띄는 감정 변화나 사건을 짚어줘.\n"
            "3. 따뜻하게 격려하고 응원하는 말을 해줘.\n"
            "4. 따뜻한 해요체로 200자 내외로 작성해.\n\n"
            "3줄 요약 분석:"
        )
    
    try:
        from analysis_worker import call_llm_hybrid
        
        options = {"temperature": 0.7, "num_predict": 800}
        result = call_llm_hybrid(prompt, options=options)
        
        if result:
            clean_result = extract_clean_text(result)
            
            # 프롬프트 반복 제거
            for marker in ['3줄 요약 분석:', '장기 패턴 분석:', '### 지시사항']:
                if marker in clean_result:
                    clean_result = clean_result.split(marker)[-1].strip()
            
            if len(clean_result.strip()) > 5:
                return jsonify({"report": clean_result.strip(), "source": "server"}), 200
        
        return jsonify({"report": None, "error": "AI 응답이 비어있습니다."}), 500
            
    except Exception as e:
        print(f"❌ [Analysis Report] Error: {e}")
        return jsonify({"report": None, "error": str(e)}), 500


def extract_clean_text(raw):
    """
    RunPod/vLLM/Ollama 어떤 형태의 응답이든 순수 텍스트만 추출.
    """
    if raw is None:
        return ""
    
    # 1. list 타입 (RunPod vLLM 실제 응답: output이 list)
    if isinstance(raw, list):
        return _parse_vllm_structure(raw)
    
    # 2. dict 타입
    if isinstance(raw, dict):
        return _parse_vllm_structure(raw)
    
    # 3. str 타입
    if isinstance(raw, str):
        text = raw.strip()
        
        # 앞뒤 큰따옴표 제거
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        
        # vLLM 구조체 문자열인지 확인
        if "'choices'" in text or '"choices"' in text:
            # regex로 tokens 내용 추출 (가장 안전한 방법)
            extracted = _regex_extract_tokens(text)
            if extracted:
                return extracted
            
            # ast.literal_eval 시도
            try:
                parsed = ast.literal_eval(text)
                result = _parse_vllm_structure(parsed)
                if result and len(result.strip()) > 3:
                    return result
            except Exception:
                pass
        
        # vLLM 구조체가 아니면 일반 텍스트로 반환
        return text
    
    return str(raw)


def _regex_extract_tokens(text):
    """regex로 tokens 또는 text 값을 추출 (ast 파싱 불가능한 경우의 안전장치)"""
    # 패턴 1: 'tokens': ['내용'] - 작은따옴표
    m = re.search(r"'tokens'\s*:\s*\[(['\"])(.*?)\1\]", text, re.DOTALL)
    if m:
        content = m.group(2)
        # 이스케이프 시퀀스 복원
        content = content.replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"')
        if len(content.strip()) > 3:
            return content.strip()
    
    # 패턴 2: "tokens": ["내용"] - 큰따옴표
    m = re.search(r'"tokens"\s*:\s*\[(["\'])(.*?)\1\]', text, re.DOTALL)
    if m:
        content = m.group(2)
        content = content.replace("\\n", "\n").replace('\\"', '"')
        if len(content.strip()) > 3:
            return content.strip()
    
    # 패턴 3: 'text': '내용'
    m = re.search(r"'text'\s*:\s*'(.*?)'", text, re.DOTALL)
    if m:
        content = m.group(1)
        content = content.replace("\\n", "\n").replace("\\'", "'")
        if len(content.strip()) > 3:
            return content.strip()
    
    # 패턴 4: "text": "내용"
    m = re.search(r'"text"\s*:\s*"(.*?)"', text, re.DOTALL)
    if m:
        content = m.group(1)
        content = content.replace("\\n", "\n").replace('\\"', '"')
        if len(content.strip()) > 3:
            return content.strip()
    
    return None


def _parse_vllm_structure(data):
    """파싱된 list/dict에서 텍스트를 추출"""
    
    # list: [{'choices': [{'tokens': ['텍스트']}], 'usage': {...}}]
    if isinstance(data, list) and len(data) > 0:
        first = data[0]
        if isinstance(first, dict):
            if 'choices' in first:
                return _extract_from_choices(first['choices'])
            if 'text' in first:
                return str(first['text'])
            if 'response' in first:
                return str(first['response'])
        return str(data)
    
    # dict: {'choices': [...]} or {'text': '...'}
    if isinstance(data, dict):
        if 'choices' in data:
            return _extract_from_choices(data['choices'])
        if 'text' in data:
            return str(data['text'])
        if 'response' in data:
            return str(data['response'])
        if 'reaction' in data:
            return str(data['reaction'])
    
    return str(data)


def _extract_from_choices(choices):
    """choices 배열에서 텍스트 추출"""
    if not isinstance(choices, list) or len(choices) == 0:
        return ""
    
    choice = choices[0]
    if not isinstance(choice, dict):
        return str(choice)
    
    # tokens 우선 (RunPod vLLM 형태)
    if 'tokens' in choice:
        tokens = choice['tokens']
        if isinstance(tokens, list):
            return ''.join(str(t) for t in tokens)
        return str(tokens)
    
    # text
    if 'text' in choice:
        return str(choice['text'])
    
    # message (OpenAI format)
    if 'message' in choice and isinstance(choice['message'], dict):
        return str(choice['message'].get('content', ''))
    
    return str(choice)


# ═════════════════════════════════════════════════
# [Feature] 가이디드 저널링 — 맥락 기반 선질문 생성
# ═════════════════════════════════════════════════

import random

# 컨디션 등급별 Fallback 질문 세트 (LLM 실패 시 사용)
_GUIDED_FALLBACKS = {
    'sunny': [
        "오늘 가장 즐거웠던 순간은 언제였나요?",
        "지금 이 기분을 누군가에게 말해준다면 어떤 말을 하고 싶나요?",
        "오늘 새롭게 시도해본 것이 있나요?",
    ],
    'mostly_sunny': [
        "오늘 하루 중 가장 편안했던 시간은 언제였나요?",
        "요즘 나를 안정시켜주는 루틴이 있나요?",
        "오늘 감사했던 작은 것 하나를 떠올려볼까요?",
    ],
    'partly_cloudy': [
        "오늘 마음 한 켠에 걸리는 것이 있다면 무엇인가요?",
        "지금 내 기분을 날씨로 표현한다면 어떤 날씨일까요?",
        "오늘 하루 중 가장 힘들었던 순간은 언제였나요?",
    ],
    'cloudy': [
        "요즘 자주 떠오르는 생각이 있나요?",
        "오늘 몸과 마음의 에너지를 0~10으로 표현하면 몇일까요?",
        "지금 가장 필요한 것이 뭔지 떠올려볼 수 있을까요?",
    ],
    'rainy': [
        "오늘 하루 어떻게 보내셨나요?",
        "지금 이 순간 어떤 감정이 가장 크게 느껴지나요?",
        "나에게 한 마디 해줄 수 있다면 어떤 말을 해주고 싶나요?",
    ],
    'default': [
        "오늘 하루 어떠셨나요?",
        "지금 떠오르는 생각이 있나요?",
        "오늘 내 마음에 가장 가까운 이모지를 하나 고른다면?",
    ],
}


@chat_bp.route('/api/chat/guided-start', methods=['POST'])
@jwt_required()
def guided_start():
    """
    가이디드 저널링 시작 질문 생성 API.
    사용자의 최근 일기/컨디션 맥락을 기반으로 맞춤 선질문 3개를 반환한다.
    iOS에서 질문 터치 → 기존 /api/chat/reaction으로 이어지는 구조.

    Response:
        {
            "questions": ["Q1", "Q2", "Q3"],
            "context_grade": "mostly_sunny",
            "source": "llm" | "fallback"
        }
    """
    user_id = int(get_jwt_identity())

    # ─── 1. 컨텍스트 수집 ───
    from models import db, Diary
    from datetime import datetime, timedelta

    recent_cutoff = datetime.utcnow() - timedelta(days=3)
    recent_diaries = Diary.query.filter(
        Diary.user_id == user_id,
        Diary.created_at >= recent_cutoff
    ).order_by(Diary.date.desc()).limit(3).all()

    # 컨디션 등급 조회 (가벼운 호출: skip_phase3=True)
    condition_grade = 'default'
    try:
        from kick_analysis.condition import generate_condition
        cond = generate_condition(
            user_id, db.session, Diary,
            skip_phase3=True
        )
        condition_grade = cond.get('condition', {}).get('grade', 'default')
    except Exception as e:
        print(f"⚠️ [Guided] Condition fetch failed: {e}")

    # 최근 일기 요약 (LLM 컨텍스트용)
    diary_context = ""
    try:
        from app import safe_decrypt
        for d in recent_diaries[:2]:
            mood = d.mood_level or '?'
            content_text = safe_decrypt(d.event) if d.event else ""
            snippet = content_text[:80] if content_text else "(내용 없음)"
            diary_context += f"- {d.date}: 기분{mood}/5, \"{snippet}\"\n"
    except Exception as e:
        print(f"⚠️ [Guided] Diary context build failed: {e}")

    # ─── 2. LLM 호출 ───
    questions = None
    source = 'fallback'

    if diary_context.strip():
        try:
            import requests as req
            import json

            # 요일/시간대 컨텍스트
            now = datetime.utcnow() + timedelta(hours=9)  # KST
            day_names = ['월', '화', '수', '목', '금', '토', '일']
            day_of_week = day_names[now.weekday()]
            hour = now.hour
            time_label = '아침' if hour < 12 else '오후' if hour < 18 else '밤'

            prompt = (
                "# 역할\n"
                "너는 따뜻한 심리 상담사 '마음온'이야.\n\n"
                "# 임무\n"
                f"오늘은 {day_of_week}요일 {time_label}이야.\n"
                f"사용자의 최근 일기 기록:\n{diary_context}\n"
                f"현재 마음 컨디션: {condition_grade}\n\n"
                "위 맥락을 바탕으로, 사용자가 오늘 일기를 시작할 때\n"
                "편하게 대답할 수 있는 따뜻한 질문 3개를 만들어줘.\n\n"
                "# 규칙\n"
                "1. 각 질문은 20자 이내로 짧게\n"
                "2. 존댓말(해요체) 사용\n"
                "3. 판단이나 조언 금지, 순수한 질문만\n"
                "4. JSON 배열로만 답변: [\"Q1\", \"Q2\", \"Q3\"]\n"
                "5. 다른 말 절대 하지 마\n\n"
                "답변:"
            )

            payload = {
                "model": "gemma4:2b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.8, "num_predict": 100}
            }
            res = req.post("http://localhost:11434/api/generate", json=payload, timeout=15)

            if res.status_code == 200:
                raw = res.json().get('response', '').strip()
                # JSON 배열 추출 시도
                import re as re_mod
                match = re_mod.search(r'\[.*?\]', raw, re_mod.DOTALL)
                if match:
                    parsed = json.loads(match.group())
                    if isinstance(parsed, list) and len(parsed) >= 2:
                        questions = [str(q).strip() for q in parsed[:3]]
                        source = 'llm'

        except Exception as e:
            print(f"⚠️ [Guided] LLM call failed: {e}")

    # ─── 3. Fallback ───
    if not questions:
        fallback_pool = _GUIDED_FALLBACKS.get(condition_grade, _GUIDED_FALLBACKS['default'])
        questions = list(fallback_pool)  # 복사본
        random.shuffle(questions)
        questions = questions[:3]

    return jsonify({
        'questions': questions,
        'context_grade': condition_grade,
        'source': source,
    }), 200

