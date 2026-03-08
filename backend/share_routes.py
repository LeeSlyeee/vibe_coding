import string
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Diary, ShareCode, ShareRelationship

share_bp = Blueprint('share', __name__)

CODE_LENGTH = 6
CODE_EXPIRY_MINUTES = 10


def _generate_unique_code():
    """암호학적으로 안전한 6자리 영숫자 코드 생성 (중복 방지, CODE_LENGTH 기준)"""
    chars = string.ascii_uppercase + string.digits
    for _ in range(20):  # 최대 20회 시도
        code = ''.join(secrets.choice(chars) for _ in range(CODE_LENGTH))
        existing = ShareCode.query.filter_by(code=code, used=False).first()
        if not existing:
            return code
    raise RuntimeError("코드 생성 실패: 고유 코드를 만들 수 없습니다.")


@share_bp.route('/api/share/code', methods=['POST'])
@jwt_required()
def create_share_code():
    """내담자(Sharer)가 공유 코드를 생성"""
    current_user_id = int(get_jwt_identity())

    # 기존 미사용 코드 만료 처리
    ShareCode.query.filter(
        ShareCode.user_id == current_user_id,
        ShareCode.used == False
    ).update({'used': True})
    db.session.commit()

    # 새 코드 생성
    code = _generate_unique_code()
    now = datetime.utcnow()
    new_code = ShareCode(
        user_id=current_user_id,
        code=code,
        created_at=now,
        expires_at=now + timedelta(minutes=CODE_EXPIRY_MINUTES),
        used=False
    )
    db.session.add(new_code)
    db.session.commit()

    return jsonify({
        "code": code,
        "expires_in": CODE_EXPIRY_MINUTES * 60,
        "message": f"공유 코드가 생성되었습니다. {CODE_EXPIRY_MINUTES}분간 유효합니다."
    }), 200


@share_bp.route('/api/share/connect', methods=['POST'])
@jwt_required()
def connect_share():
    """보호자(Viewer)가 코드를 입력하여 연결"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    code_input = (data.get('code') or '').strip().upper()

    if not code_input or len(code_input) != CODE_LENGTH:
        return jsonify({"message": "6자리 코드를 정확히 입력해주세요."}), 400

    # 코드 검증
    share_code = ShareCode.query.filter_by(code=code_input, used=False).first()
    if not share_code:
        return jsonify({"message": "유효하지 않거나 이미 사용된 코드입니다."}), 404

    # 만료 확인
    if datetime.utcnow() > share_code.expires_at:
        share_code.used = True
        db.session.commit()
        return jsonify({"message": "코드가 만료되었습니다. 새 코드를 요청해주세요."}), 410

    # 자기 자신 연결 방지
    if share_code.user_id == current_user_id:
        return jsonify({"message": "자신의 코드로는 연결할 수 없습니다."}), 400

    # 중복 연결 방지
    existing = ShareRelationship.query.filter_by(
        sharer_id=share_code.user_id,
        viewer_id=current_user_id
    ).first()
    if existing:
        return jsonify({"message": "이미 연결된 사용자입니다."}), 409

    # 관계 생성 (role 지정 가능)
    requested_role = data.get('role', 'viewer')  # 'guardian' or 'viewer'
    if requested_role not in ('guardian', 'viewer'):
        requested_role = 'viewer'
    
    rel = ShareRelationship(
        sharer_id=share_code.user_id,
        viewer_id=current_user_id,
        connected_at=datetime.utcnow(),
        role=requested_role
    )
    db.session.add(rel)

    # 코드 사용 처리
    share_code.used = True
    db.session.commit()

    sharer = User.query.get(share_code.user_id)
    sharer_name = sharer.nickname or sharer.username if sharer else "알 수 없음"

    return jsonify({
        "message": f"'{sharer_name}'님과 연결되었습니다.",
        "sharer_id": share_code.user_id
    }), 200


@share_bp.route('/api/share/list', methods=['GET'])
@jwt_required()
def get_shared_list():
    """role에 따라 연결된 사용자 목록 반환"""
    current_user_id = int(get_jwt_identity())
    role = request.args.get('role', 'viewer')

    result = []
    
    if role == 'sharer':
        # 내담자(sharer)가 자신에게 연결된 보호자 목록 조회
        relationships = ShareRelationship.query.filter_by(sharer_id=current_user_id).all()
        for rel in relationships:
            viewer = User.query.get(rel.viewer_id)
            if viewer:
                result.append({
                    "id": str(viewer.id),
                    "name": viewer.nickname or viewer.username,
                    "role": rel.role or 'viewer',
                    "birth_date": viewer.birth_date,
                    "connected_at": rel.connected_at.isoformat() if rel.connected_at else None,
                    "share_mood": rel.share_mood if rel.share_mood is not None else True,
                    "share_report": rel.share_report if rel.share_report is not None else False,
                    "share_crisis": rel.share_crisis if rel.share_crisis is not None else True
                })
    else:
        # 보호자(viewer)가 연결된 내담자 목록 조회
        relationships = ShareRelationship.query.filter_by(viewer_id=current_user_id).all()
        for rel in relationships:
            sharer = User.query.get(rel.sharer_id)
            if sharer:
                result.append({
                    "id": str(sharer.id),
                    "name": sharer.nickname or sharer.username,
                    "role": rel.role or 'viewer',
                    "birth_date": sharer.birth_date,
                    "connected_at": rel.connected_at.isoformat() if rel.connected_at else None,
                    "alert_mood_drop": rel.alert_mood_drop if rel.alert_mood_drop is not None else True,
                    "alert_crisis": rel.alert_crisis if rel.alert_crisis is not None else True,
                    "alert_inactivity": rel.alert_inactivity if rel.alert_inactivity is not None else True
                })

    return jsonify(result), 200


@share_bp.route('/api/share/disconnect', methods=['POST'])
@jwt_required()
def disconnect_share():
    """연결 해제"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    target_id = data.get('sharer_id') or data.get('target_id')

    if not target_id:
        return jsonify({"message": "대상 ID가 필요합니다."}), 400

    # 내담자(sharer)가 보호자(viewer)를 끊거나, 반대이거나 쌍방향 모두 가능해야 함
    rel = ShareRelationship.query.filter(
        db.or_(
            db.and_(ShareRelationship.sharer_id == int(target_id), ShareRelationship.viewer_id == current_user_id),
            db.and_(ShareRelationship.sharer_id == current_user_id, ShareRelationship.viewer_id == int(target_id))
        )
    ).first()

    if not rel:
        return jsonify({"message": "연결된 관계를 찾을 수 없습니다."}), 404

    db.session.delete(rel)
    db.session.commit()

    return jsonify({"message": "연결이 해제되었습니다."}), 200


@share_bp.route('/api/share/insights/<int:target_id>', methods=['GET'])
@jwt_required()
def get_shared_insights(target_id):
    """보호자가 내담자의 감정 통계를 조회"""
    current_user_id = int(get_jwt_identity())

    # 권한 확인: 연결된 관계가 있는지
    rel = ShareRelationship.query.filter_by(
        sharer_id=target_id,
        viewer_id=current_user_id
    ).first()

    if not rel:
        return jsonify({"message": "접근 권한이 없습니다."}), 403

    # 최근 30일 일기 통계
    cutoff = datetime.utcnow() - timedelta(days=30)
    diaries = Diary.query.filter(
        Diary.user_id == target_id,
        Diary.created_at >= cutoff
    ).order_by(Diary.date.desc()).all()

    sharer = User.query.get(target_id)

    # 감정 통계 계산
    total = len(diaries)
    if total == 0:
        return jsonify({
            "sharer_name": sharer.nickname or sharer.username if sharer else "알 수 없음",
            "total_entries": 0,
            "avg_mood": None,
            "mood_trend": [],
            "recent_status": "데이터 없음",
            "message": "아직 기록이 없어요."
        }), 200

    moods = [d.mood_level or 3 for d in diaries]
    avg_mood = round(sum(moods) / len(moods), 1)

    # 최근 7일 추세
    recent_7 = diaries[:7]
    mood_trend = [
        {"date": d.date, "mood": d.mood_level or 3}
        for d in reversed(recent_7)
    ]

    # 상태 판단
    has_safety = any(
        getattr(d, 'safety_flag', None) in ['need_help', 'danger', True]
        for d in diaries[:7]
    )
    if has_safety or avg_mood <= 2:
        status = "주의 필요 ⚠️"
    elif avg_mood <= 3:
        status = "보통 😐"
    elif avg_mood <= 4:
        status = "양호 🙂"
    else:
        status = "좋음 😊"

    # [Phase 6] 공유 범위 필터링
    response_data = {
        "sharer_name": sharer.nickname or sharer.username if sharer else "알 수 없음",
        "total_entries": total,
        "recent_status": status,
        "writing_streak": _calc_streak(diaries)
    }
    
    # 마음 온도 공유 허용 시에만 포함
    share_mood = getattr(rel, 'share_mood', True)
    if share_mood is None or share_mood:
        response_data["avg_mood"] = avg_mood
        response_data["mood_trend"] = mood_trend
    else:
        response_data["avg_mood"] = None
        response_data["mood_trend"] = []
        response_data["mood_restricted"] = True
    
    # 위기 신호 공유 허용 시에만 포함
    share_crisis = getattr(rel, 'share_crisis', True)
    if share_crisis is None or share_crisis:
        response_data["has_safety_concern"] = has_safety
    
    # === 문장 형태 감정 요약 보고서 ===
    share_report = getattr(rel, 'share_report', False)
    if share_report:
        narrative = _build_narrative_summary(diaries, sharer, avg_mood, has_safety, share_mood, share_crisis)
        response_data["narrative_summary"] = narrative
    else:
        response_data["narrative_summary"] = ["🔒 내담자의 프라이버시 설정('주간 리포트 공유 비활성화')에 의해 상세 감정 보고서가 블라인드 처리되었습니다."]
    
    return jsonify(response_data), 200


def _build_narrative_summary(diaries, sharer, avg_mood, has_safety, share_mood=True, share_crisis=True):
    """최근 일기 데이터를 바탕으로 보호자용 문장 형태 감정 보고서를 생성"""
    name = sharer.nickname or sharer.username if sharer else "내담자"
    recent = diaries[:7]  # 최근 7개 일기
    
    paragraphs = []
    
    # 1. 전체 개요 (기분 온도 비공개 설정 시 수치 노출 방지)
    if share_mood:
        mood_label = "매우 낮은" if avg_mood <= 1.5 else "낮은" if avg_mood <= 2.5 else "보통 수준의" if avg_mood <= 3.5 else "양호한" if avg_mood <= 4.5 else "좋은"
        paragraphs.append(f"📋 {name}님은 최근 30일간 총 {len(diaries)}회 일기를 작성했으며, 평균 마음 온도는 {avg_mood}점({mood_label} 상태)입니다.")
    else:
        paragraphs.append(f"📋 {name}님은 최근 30일간 총 {len(diaries)}회 일기를 작성했습니다. (마음 온도 수치는 비공개 상태입니다)")
    
    # 2. 위기 신호 (위기 신호 비공개 설정 시 노출 방지)
    if has_safety and share_crisis:
        paragraphs.append(f"🚨 최근 기록에서 위기 신호가 감지되었습니다. {name}님의 안부를 직접 확인해주시길 권합니다.")
    
    # 3. 최근 감정 서술 요약 (감정 키워드 추출)
    emotions = []
    for d in recent:
        try:
            from crypto_utils import crypto_manager
            raw = d.emotion_desc or ""
            # [Fix#10] crypto_manager가 None일 수 있으므로 검증
            if raw.startswith('gAAAA') and crypto_manager is not None:
                raw = crypto_manager.decrypt(raw)
            if raw and len(raw.strip()) > 0 and not raw.startswith('gAAAA'):
                emotions.append(raw.strip())
        except Exception:
            if d.emotion_desc and not d.emotion_desc.startswith('gAAAA'):
                emotions.append(d.emotion_desc.strip())
    
    if emotions:
        emotion_text = ', '.join(emotions[:3])
        paragraphs.append(f"💭 최근 표현한 감정: {emotion_text}")
    
    # 4. 자기 대화 (내면의 목소리) 요약
    self_talks = []
    for d in recent:
        try:
            from crypto_utils import crypto_manager
            raw = d.self_talk or ""
            # [Fix#10] crypto_manager None 검증
            if raw.startswith('gAAAA') and crypto_manager is not None:
                raw = crypto_manager.decrypt(raw)
            if raw and len(raw.strip()) > 0 and not raw.startswith('gAAAA'):
                self_talks.append(raw.strip())
        except Exception:
            if d.self_talk and not d.self_talk.startswith('gAAAA'):
                self_talks.append(d.self_talk.strip())
    
    if self_talks:
        paragraphs.append(f"🗣️ 내면의 자기 대화: \"{self_talks[0]}\"")
    
    # 5. AI 코멘트 요약
    ai_comments = []
    for d in recent:
        try:
            from crypto_utils import crypto_manager
            raw = d.ai_comment or ""
            # [Fix#10] crypto_manager None 검증
            if raw.startswith('gAAAA') and crypto_manager is not None:
                raw = crypto_manager.decrypt(raw)
            if raw and len(raw.strip()) > 0 and not raw.startswith('gAAAA'):
                ai_comments.append(raw.strip())
        except Exception:
            if d.ai_comment and not d.ai_comment.startswith('gAAAA'):
                ai_comments.append(d.ai_comment.strip())
    
    if ai_comments:
        # AI 코멘트가 JSON 형태일 수 있으므로 파싱 시도
        comment_text = ai_comments[0]
        try:
            import json
            # "예)\n{...}\n```" 와 같이 앞뒤 휴지심 텍스트 제거 - 첫 '{' 부터 마지막 '}' 까지만 추출
            json_start = comment_text.find('{')
            json_end = comment_text.rfind('}')
            
            if json_start >= 0 and json_end > json_start:
                json_str = comment_text[json_start:json_end+1]
                parsed = json.loads(json_str)
                if isinstance(parsed, dict):
                    # comment 필드 추출 (다양한 키 변형 대비 포함)
                    readable = parsed.get('comment', '') or parsed.get('ai_comment', '') or parsed.get('analysis', '') or parsed.get('message', '')
                    emotion = parsed.get('emotion', '') or parsed.get('ai_emotion', '') or parsed.get('prediction', '')
                    if readable:
                        if emotion:
                            comment_text = f"감정: {emotion} — {readable}"
                        else:
                            comment_text = readable
        except (json.JSONDecodeError, Exception):
            pass  # 파싱 실패 시 원본 그대로 사용
        
        paragraphs.append(f"🤖 AI 분석 의견: {comment_text}")
    
    # 6. 기분 추세 해석 (마음 온도 공유 시에만)
    if share_mood and len(recent) >= 2:
        recent_moods = [d.mood_level or 3 for d in recent]
        first_half = recent_moods[len(recent_moods)//2:]
        second_half = recent_moods[:len(recent_moods)//2]
        avg_first = sum(first_half) / max(len(first_half), 1)
        avg_second = sum(second_half) / max(len(second_half), 1)
        
        if avg_second - avg_first >= 1:
            paragraphs.append("📈 기분 추세: 최근 마음 온도가 호전되고 있는 추세입니다.")
        elif avg_first - avg_second >= 1:
            paragraphs.append("📉 기분 추세: 최근 마음 온도가 하락하고 있는 추세입니다. 관심이 필요합니다.")
        else:
            paragraphs.append("➡️ 기분 추세: 기분 변동이 비교적 안정적입니다.")
    
    # 7. 마무리
    if avg_mood <= 2:
        paragraphs.append("💡 지금 따뜻한 한마디와 관심이 큰 힘이 될 수 있습니다.")
    elif avg_mood <= 3:
        paragraphs.append("💡 꾸준한 관심과 대화가 도움이 됩니다.")
    
    return paragraphs


def _calc_streak(diaries):
    """연속 작성일 계산"""
    if not diaries:
        return 0
    dates = sorted(set(d.date for d in diaries), reverse=True)
    streak = 1
    for i in range(1, len(dates)):
        try:
            d1 = datetime.strptime(dates[i - 1], '%Y-%m-%d')
            d2 = datetime.strptime(dates[i], '%Y-%m-%d')
            if (d1 - d2).days == 1:
                streak += 1
            else:
                break
        except ValueError:
            break
    return streak


# ========================================
# [Phase 5] 보호자 알림 관련 API
# ========================================

@share_bp.route('/api/share/role', methods=['PUT'])
@jwt_required()
def update_role():
    """보호자의 역할 변경 (guardian ↔ viewer)"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    sharer_id = data.get('sharer_id')
    new_role = data.get('role', 'viewer')
    
    if new_role not in ('guardian', 'viewer'):
        return jsonify({"message": "역할은 'guardian' 또는 'viewer'만 가능합니다."}), 400
    
    rel = ShareRelationship.query.filter_by(
        sharer_id=int(sharer_id),
        viewer_id=current_user_id
    ).first()
    
    if not rel:
        return jsonify({"message": "연결된 관계를 찾을 수 없습니다."}), 404
    
    rel.role = new_role
    db.session.commit()
    
    return jsonify({"message": f"역할이 '{new_role}'로 변경되었습니다."}), 200


@share_bp.route('/api/share/alert-settings', methods=['PUT'])
@jwt_required()
def update_alert_settings():
    """보호자의 알림 설정 변경"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    sharer_id = data.get('sharer_id')
    
    rel = ShareRelationship.query.filter_by(
        sharer_id=int(sharer_id),
        viewer_id=current_user_id
    ).first()
    
    if not rel:
        return jsonify({"message": "연결된 관계를 찾을 수 없습니다."}), 404
    
    if 'alert_mood_drop' in data:
        rel.alert_mood_drop = bool(data['alert_mood_drop'])
    if 'alert_crisis' in data:
        rel.alert_crisis = bool(data['alert_crisis'])
    if 'alert_inactivity' in data:
        rel.alert_inactivity = bool(data['alert_inactivity'])
    
    db.session.commit()
    
    return jsonify({"message": "알림 설정이 업데이트되었습니다."}), 200


@share_bp.route('/api/share/share-scope', methods=['PUT'])
@jwt_required()
def update_share_scope():
    """[Phase 6] 내담자가 보호자에게 공유할 데이터 범위 설정"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    viewer_id = data.get('viewer_id')
    
    # 내담자(sharer) 본인만 설정 가능
    rel = ShareRelationship.query.filter_by(
        sharer_id=current_user_id,
        viewer_id=int(viewer_id)
    ).first()
    
    if not rel:
        return jsonify({"message": "연결된 관계를 찾을 수 없습니다."}), 404
    
    if 'share_mood' in data:
        rel.share_mood = bool(data['share_mood'])
    if 'share_report' in data:
        rel.share_report = bool(data['share_report'])
    if 'share_crisis' in data:
        rel.share_crisis = bool(data['share_crisis'])
    
    db.session.commit()
    
    return jsonify({"message": "공유 범위가 업데이트되었습니다."}), 200


@share_bp.route('/api/share/guardians', methods=['GET'])
@jwt_required()
def get_my_guardians():
    """내담자(sharer)가 자신에게 연결된 보호자/조회자 목록 확인"""
    current_user_id = int(get_jwt_identity())
    
    relationships = ShareRelationship.query.filter_by(sharer_id=current_user_id).all()
    
    result = []
    for rel in relationships:
        viewer = User.query.get(rel.viewer_id)
        if viewer:
            result.append({
                "viewer_id": viewer.id,
                "name": viewer.nickname or viewer.username,
                "role": rel.role or 'viewer',
                "connected_at": rel.connected_at.isoformat() if rel.connected_at else None,
                "share_mood": rel.share_mood if rel.share_mood is not None else True,
                "share_report": rel.share_report if rel.share_report is not None else False,
                "share_crisis": rel.share_crisis if rel.share_crisis is not None else True
            })
    
    return jsonify(result), 200


@share_bp.route('/api/share/guardian-alerts', methods=['GET'])
@jwt_required()
def get_guardian_alerts():
    """보호자가 확인해야 할 알림 목록 조회 (위기 신호 + 미기록)"""
    current_user_id = int(get_jwt_identity())
    
    # 보호자로 연결된 관계만 조회
    relationships = ShareRelationship.query.filter_by(
        viewer_id=current_user_id,
        role='guardian'
    ).all()
    
    alerts = []
    now = datetime.utcnow()
    
    for rel in relationships:
        sharer = User.query.get(rel.sharer_id)
        if not sharer:
            continue
        
        sharer_name = sharer.nickname or sharer.username
        
        # 최근 7일 일기 조회
        cutoff_7d = now - timedelta(days=7)
        recent_diaries = Diary.query.filter(
            Diary.user_id == rel.sharer_id,
            Diary.created_at >= cutoff_7d
        ).order_by(Diary.created_at.desc()).all()
        
        # 1. 위기 신호 알림 (alert_crisis 설정 시)
        if rel.alert_crisis is not False:
            share_crisis = getattr(rel, 'share_crisis', True)
            if share_crisis is not False:
                has_crisis = any(
                    getattr(d, 'safety_flag', None) in ['need_help', 'danger', True]
                    for d in recent_diaries
                )
                if has_crisis:
                    alerts.append({
                        "type": "crisis",
                        "sharer_id": rel.sharer_id,
                        "sharer_name": sharer_name,
                        "message": f"{sharer_name}님에게 위기 신호가 감지되었습니다.",
                        "severity": "high",
                        "icon": "🚨",
                        "action_guide": [
                            "1. 침착하게 전화 또는 문자로 안부를 확인해 주세요.",
                            "2. 연락이 되지 않으면 가까운 경찰서(112)에 안전 확인을 요청하세요.",
                            "3. 자살예방상담전화 1393에서 보호자 상담도 가능합니다."
                        ]
                    })
        
        # 2. 마음 온도 급락 알림 (alert_mood_drop 설정 시)
        if rel.alert_mood_drop is not False and len(recent_diaries) >= 2:
            share_mood = getattr(rel, 'share_mood', True)
            if share_mood is not False:
                moods = [d.mood_level or 3 for d in recent_diaries[:3]]
                avg_recent = sum(moods) / len(moods)
                if avg_recent <= 2.0:
                    alerts.append({
                        "type": "mood_drop",
                        "sharer_id": rel.sharer_id,
                        "sharer_name": sharer_name,
                        "message": f"{sharer_name}님의 마음 온도가 낮은 상태입니다.",
                        "severity": "medium",
                        "icon": "💙",
                        "avg_mood": round(avg_recent, 1),
                        "action_guide": [
                            "1. 자연스러운 대화로 안부를 물어봐 주세요.",
                            "2. '힘내'보다는 '네 곁에 있어'라는 메시지가 좋습니다.",
                            "3. 상태가 지속되면 전문 상담을 권유해 주세요."
                        ]
                    })
        
        # 3. 장기 미기록 알림 (alert_inactivity 설정 시)
        if rel.alert_inactivity is not False:
            if len(recent_diaries) == 0:
                alerts.append({
                    "type": "inactivity",
                    "sharer_id": rel.sharer_id,
                    "sharer_name": sharer_name,
                    "message": f"{sharer_name}님이 7일 이상 기록을 남기지 않았습니다.",
                    "severity": "low",
                    "icon": "📝",
                    "action_guide": [
                        "1. 가볍게 안부 연락을 해보세요.",
                        "2. 기록하지 않은 것 자체가 문제는 아닙니다.",
                        "3. 편안할 때 다시 사용하면 된다고 알려주세요."
                    ]
                })
    
    return jsonify({
        "alerts": alerts,
        "total": len(alerts)
    }), 200
