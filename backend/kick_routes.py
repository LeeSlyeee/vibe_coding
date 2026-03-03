"""
마음온 킥(Kick) 분석 API 라우트
================================
의료진 대시보드 전용 엔드포인트.
Phase 1: 시계열 분석 (timeseries)
Phase 2: 언어 지문 분석 (linguistic)
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Diary
from kick_analysis import analyze_timeseries, analyze_all_users_timeseries
from kick_analysis.linguistic import analyze_linguistic, analyze_all_users_linguistic
from kick_analysis.relational import analyze_relational, analyze_all_users_relational

kick_bp = Blueprint('kick', __name__)

# 복호화 함수 참조 (app.py에서 설정됨)
_decrypt_func = None

def set_decrypt_func(func):
    """app.py에서 safe_decrypt 함수를 주입받는다."""
    global _decrypt_func
    _decrypt_func = func


def _require_staff(current_user_id):
    """의료진/관리자 권한 확인"""
    user = db.session.query(User).filter_by(id=current_user_id).first()
    if not user or user.role not in ('staff', 'admin', 'doctor'):
        return None
    return user


@kick_bp.route('/api/kick/timeseries/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_timeseries(user_id):
    """특정 사용자의 시계열 분석 결과 조회 (의료진 전용)"""
    current_user_id = get_jwt_identity()
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    target_user = db.session.query(User).filter_by(id=user_id).first()
    if not target_user:
        return jsonify({'error': '사용자를 찾을 수 없습니다'}), 404

    result = analyze_timeseries(user_id, db.session, Diary)
    result['username'] = target_user.username
    result['real_name'] = target_user.real_name

    return jsonify(result)


@kick_bp.route('/api/kick/timeseries/flags', methods=['GET'])
@jwt_required()
def get_all_flags():
    """전체 사용자 중 플래그 발생자 목록 조회 (의료진 대시보드용)"""
    current_user_id = get_jwt_identity()
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    result = analyze_all_users_timeseries(db.session, User, Diary)

    return jsonify(result)


@kick_bp.route('/api/kick/timeseries/summary', methods=['GET'])
@jwt_required()
def get_flags_summary():
    """플래그 요약 통계 (대시보드 상단 카드용)"""
    current_user_id = get_jwt_identity()
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    result = analyze_all_users_timeseries(db.session, User, Diary)

    # 플래그 유형별 집계
    type_counts = {}
    severity_counts = {'high': 0, 'medium': 0, 'low': 0}

    for user_data in result['flagged_users']:
        for flag in user_data['flags']:
            flag_type = flag['type']
            severity = flag['severity']
            type_counts[flag_type] = type_counts.get(flag_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

    return jsonify({
        'analysis_date': result['analysis_date'],
        'total_users': result['total_users'],
        'flagged_count': result['flagged_count'],
        'flag_rate_pct': round(
            result['flagged_count'] / max(result['total_users'], 1) * 100, 1
        ),
        'by_type': type_counts,
        'by_severity': severity_counts
    })


# ═════════════════════════════════════════════════
# Phase 2: 언어 지문 (Linguistic Fingerprint)
# ═════════════════════════════════════════════════

@kick_bp.route('/api/kick/linguistic/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_linguistic(user_id):
    """특정 사용자의 언어 지문 분석 결과 조회 (의료진 전용)"""
    current_user_id = get_jwt_identity()
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    target_user = db.session.query(User).filter_by(id=user_id).first()
    if not target_user:
        return jsonify({'error': '사용자를 찾을 수 없습니다'}), 404

    result = analyze_linguistic(
        user_id, db.session, Diary,
        crypto_decrypt=_decrypt_func
    )
    result['username'] = target_user.username
    result['real_name'] = target_user.real_name

    return jsonify(result)


@kick_bp.route('/api/kick/linguistic/flags', methods=['GET'])
@jwt_required()
def get_linguistic_flags():
    """전체 사용자 중 언어 지문 플래그 발생자 목록 (의료진 대시보드용)"""
    current_user_id = get_jwt_identity()
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    result = analyze_all_users_linguistic(
        db.session, User, Diary,
        crypto_decrypt=_decrypt_func
    )

    return jsonify(result)


@kick_bp.route('/api/kick/linguistic/summary', methods=['GET'])
@jwt_required()
def get_linguistic_summary():
    """언어 지문 플래그 요약 통계 (대시보드 상단 카드용)"""
    current_user_id = get_jwt_identity()
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    result = analyze_all_users_linguistic(
        db.session, User, Diary,
        crypto_decrypt=_decrypt_func
    )

    type_counts = {}
    severity_counts = {'high': 0, 'medium': 0, 'low': 0}

    for user_data in result['flagged_users']:
        for flag in user_data['flags']:
            flag_type = flag['type']
            severity = flag['severity']
            type_counts[flag_type] = type_counts.get(flag_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

    return jsonify({
        'analysis_date': result['analysis_date'],
        'total_users': result['total_users'],
        'flagged_count': result['flagged_count'],
        'flag_rate_pct': round(
            result['flagged_count'] / max(result['total_users'], 1) * 100, 1
        ),
        'by_type': type_counts,
        'by_severity': severity_counts
    })


# ═════════════════════════════════════════════════
# Phase 3: 관계 지형도 (Relational Topology)
# ═════════════════════════════════════════════════

@kick_bp.route('/api/kick/relational/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_relational(user_id):
    """특정 사용자의 관계 지형도 분석 결과 조회 (의료진 전용)"""
    current_user_id = get_jwt_identity()
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    target_user = db.session.query(User).filter_by(id=user_id).first()
    if not target_user:
        return jsonify({'error': '사용자를 찾을 수 없습니다'}), 404

    result = analyze_relational(
        user_id, db.session, Diary,
        crypto_decrypt=_decrypt_func
    )
    result['username'] = target_user.username
    result['real_name'] = target_user.real_name

    return jsonify(result)


@kick_bp.route('/api/kick/relational/flags', methods=['GET'])
@jwt_required()
def get_relational_flags():
    """전체 사용자 중 관계 지형도 플래그 발생자 목록 (의료진 대시보드용)"""
    current_user_id = get_jwt_identity()
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    result = analyze_all_users_relational(
        db.session, User, Diary,
        crypto_decrypt=_decrypt_func
    )

    return jsonify(result)


@kick_bp.route('/api/kick/relational/summary', methods=['GET'])
@jwt_required()
def get_relational_summary():
    """관계 지형도 플래그 요약 통계 (대시보드 상단 카드용)"""
    current_user_id = get_jwt_identity()
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    result = analyze_all_users_relational(
        db.session, User, Diary,
        crypto_decrypt=_decrypt_func
    )

    type_counts = {}
    severity_counts = {'high': 0, 'medium': 0, 'low': 0}

    for user_data in result['flagged_users']:
        for flag in user_data['flags']:
            flag_type = flag['type']
            severity = flag['severity']
            type_counts[flag_type] = type_counts.get(flag_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

    return jsonify({
        'analysis_date': result['analysis_date'],
        'total_users': result['total_users'],
        'flagged_count': result['flagged_count'],
        'flag_rate_pct': round(
            result['flagged_count'] / max(result['total_users'], 1) * 100, 1
        ),
        'by_type': type_counts,
        'by_severity': severity_counts
    })
