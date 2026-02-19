from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

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
            "reaction": "잠시 상담 시스템에 문제가 있어요. 곧 돌아올게요. 🙏"
        }), 200  # 200으로 반환 (iOS가 에러 처리할 수 있도록 graceful)
