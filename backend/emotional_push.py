"""
감성 푸시 알림 (Emotional Push Notification)
=============================================
LLM을 활용하여 사용자 맥락(최근 일기, 컨디션)에 맞는
개인화된 따뜻한 넛지 메시지를 생성하고 푸시 알림으로 전송한다.

원칙:
  - 기존 push_service.py의 send_push()를 재사용
  - LLM 실패 시 condition.py의 등급별 메시지를 fallback으로 사용
  - 기존 코드 무변경: 이 파일은 완전히 독립적인 신규 모듈
"""

import random
import logging
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

logger = logging.getLogger(__name__)

emotional_push_bp = Blueprint('emotional_push', __name__)


def _generate_nudge_message(user_id, db_session, Diary, safe_decrypt=None):
    """
    사용자 맥락 기반 LLM 넛지 메시지 생성.
    
    Returns:
        tuple: (message_str, source_str)
            source: 'llm' | 'condition' | 'fallback'
    """
    from kick_analysis.condition import generate_condition, CONDITION_GRADES

    # 1. 컨디션 계산
    condition_grade = 'mostly_sunny'
    condition_label = '안정'
    try:
        cond = generate_condition(
            user_id, db_session, Diary,
            crypto_decrypt=safe_decrypt,
            skip_phase3=True
        )
        condition_grade = cond.get('condition', {}).get('grade', 'mostly_sunny')
        condition_label = cond.get('condition', {}).get('label', '안정')
    except Exception as e:
        logger.warning(f"⚠️ [Nudge] Condition failed: {e}")

    # 2. 최근 일기 스니펫 수집
    diary_snippet = ""
    try:
        recent = db_session.query(Diary).filter(
            Diary.user_id == user_id,
            Diary.created_at >= datetime.utcnow() - timedelta(days=3)
        ).order_by(Diary.date.desc()).limit(2).all()

        for d in recent:
            content = safe_decrypt(d.event) if safe_decrypt and d.event else ""
            if content:
                diary_snippet += f"- {d.date}: \"{content[:60]}\"\n"
    except Exception as e:
        logger.warning(f"⚠️ [Nudge] Diary fetch failed: {e}")

    # 3. LLM 호출 시도
    if diary_snippet.strip():
        try:
            import requests as req
            import re

            prompt = (
                "# 역할\n"
                "너는 '마음온' 앱이야. 사용자에게 따뜻한 알림을 보내려고 해.\n\n"
                "# 맥락\n"
                f"사용자의 현재 마음 상태: {condition_label} ({condition_grade})\n"
                f"최근 일기:\n{diary_snippet}\n"
                "# 규칙\n"
                "1. 1~2문장으로 짧고 따뜻하게\n"
                "2. 이모지 1개만 사용\n"
                "3. 조언/판단 금지, 공감과 응원만\n"
                "4. 존댓말(해요체)\n"
                "5. 메시지만 출력 (다른 말 금지)\n\n"
                "메시지:"
            )

            payload = {
                "model": "maumON-gemma",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.8, "num_predict": 80}
            }
            res = req.post("http://localhost:11434/api/generate", json=payload, timeout=15)

            if res.status_code == 200:
                result = res.json().get('response', '').strip()
                if result and len(result) >= 5:
                    # 따옴표 제거
                    if result.startswith('"') and result.endswith('"'):
                        result = result[1:-1]
                    return result, 'llm'

        except Exception as e:
            logger.warning(f"⚠️ [Nudge] LLM failed: {e}")

    # 4. Fallback: condition.py의 등급별 care_tip 사용
    grade_info = CONDITION_GRADES.get(condition_grade, CONDITION_GRADES['mostly_sunny'])
    message = random.choice(grade_info['care_tips'])
    return message, 'condition'


@emotional_push_bp.route('/api/push/emotional-nudge', methods=['POST'])
@jwt_required()
def send_emotional_nudge():
    """
    감성 넛지 푸시 알림 전송 API.
    
    사용자 본인에게 LLM 개인화 메시지를 푸시 알림으로 보낸다.
    (스케줄러 또는 수동 트리거)
    
    Response:
        {
            "status": "sent" | "no_token" | "push_disabled",
            "message": "생성된 메시지 내용",
            "source": "llm" | "condition"
        }
    """
    user_id = int(get_jwt_identity())

    from models import db, User, Diary

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404

    # 푸시 토큰 확인
    fcm_token = user.fcm_token
    apns_token = user.apns_token
    if not fcm_token and not apns_token:
        return jsonify({
            'status': 'no_token',
            'message': '등록된 푸시 토큰이 없습니다.',
        }), 200

    # safe_decrypt 가져오기
    safe_decrypt = None
    try:
        from app import safe_decrypt as sd
        safe_decrypt = sd
    except Exception:
        pass

    # 넛지 메시지 생성
    nudge_message, source = _generate_nudge_message(
        user_id, db.session, Diary, safe_decrypt=safe_decrypt
    )

    # 푸시 발송
    try:
        from push_service import send_push, is_push_available
        if not is_push_available() and not apns_token:
            return jsonify({
                'status': 'push_disabled',
                'message': nudge_message,
                'source': source,
            }), 200

        success = send_push(
            fcm_token=fcm_token or '',
            title='💌 마음온이 전하는 한 마디',
            body=nudge_message,
            data={'type': 'emotional_nudge', 'source': source},
            apns_token=apns_token,
        )

        status = 'sent' if success else 'send_failed'

    except Exception as e:
        logger.error(f"❌ [Nudge] Push send error: {e}")
        status = 'send_failed'

    return jsonify({
        'status': status,
        'message': nudge_message,
        'source': source,
    }), 200
