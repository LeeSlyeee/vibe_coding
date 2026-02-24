import string
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Diary, ShareCode, ShareRelationship

share_bp = Blueprint('share', __name__)

CODE_LENGTH = 8
CODE_EXPIRY_MINUTES = 10


def _generate_unique_code():
    """암호학적으로 안전한 6자리 영숫자 코드 생성 (중복 방지)"""
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

    # 관계 생성
    rel = ShareRelationship(
        sharer_id=share_code.user_id,
        viewer_id=current_user_id,
        connected_at=datetime.utcnow()
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
    """조회자(Viewer)의 연결된 사용자 목록 반환"""
    current_user_id = int(get_jwt_identity())

    relationships = ShareRelationship.query.filter_by(viewer_id=current_user_id).all()

    result = []
    for rel in relationships:
        sharer = User.query.get(rel.sharer_id)
        if sharer:
            result.append({
                "sharer_id": sharer.id,
                "name": sharer.nickname or sharer.username,
                "birth_date": sharer.birth_date,
                "connected_at": rel.connected_at.isoformat() if rel.connected_at else None
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

    rel = ShareRelationship.query.filter_by(
        sharer_id=int(target_id),
        viewer_id=current_user_id
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
            "message": "아직 작성된 일기가 없습니다."
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

    return jsonify({
        "sharer_name": sharer.nickname or sharer.username if sharer else "알 수 없음",
        "total_entries": total,
        "avg_mood": avg_mood,
        "mood_trend": mood_trend,
        "recent_status": status,
        "writing_streak": _calc_streak(diaries)
    }), 200


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
