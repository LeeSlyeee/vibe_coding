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


# ═════════════════════════════════════════════════
# 온디바이스 AI용: 본인 킥 인사이트 요약 (의료진 권한 불필요)
# ═════════════════════════════════════════════════

@kick_bp.route('/api/kick/my-insights', methods=['GET'])
@jwt_required()
def get_my_kick_insights():
    """
    로그인한 사용자 본인의 킥 분석 인사이트 요약.
    온디바이스 AI가 대화 시 context로 사용.
    의료진 권한 불필요 — 본인 데이터만 반환.
    """
    user_id = get_jwt_identity()

    insights = []

    try:
        # Phase 1: 시계열
        from kick_analysis import analyze_timeseries
        ts = analyze_timeseries(user_id, db.session, Diary)
        for f in ts.get('flags', []):
            insights.append(f"[시계열] {f['message']}")

        # Phase 2: 언어 지문
        lg = analyze_linguistic(user_id, db.session, Diary, crypto_decrypt=_decrypt_func)
        if lg.get('status') == 'completed':
            dev = lg.get('linguistic', {}).get('deviation', {})
            labels = {'ttr': '어휘 다양성', 'self_focus': '자기 집중도',
                      'char_count': '일기 분량', 'negation_ratio': '부정어 비율'}
            for key, label in labels.items():
                d = dev.get(key, {})
                if d.get('change_pct') and abs(d['change_pct']) >= 20:
                    insights.append(f"[언어] {label} {d['change_pct']:+.0f}% 변화")
        for f in lg.get('flags', []):
            insights.append(f"[언어] ⚠️ {f['message']}")

        # Phase 3: 관계 지형도
        rl = analyze_relational(user_id, db.session, Diary, crypto_decrypt=_decrypt_func)
        if rl.get('status') == 'completed':
            rel = rl.get('relational', {})
            timeline = rel.get('social_density_timeline', [])
            if timeline:
                recent = timeline[-1]
                names = recent.get('people_names', [])
                if names:
                    insights.append(f"[관계] 최근 일기에 등장한 사람: {', '.join(names[:5])}")
                else:
                    insights.append("[관계] 최근 일기에 타인 등장 없음")
        for f in rl.get('flags', []):
            insights.append(f"[관계] ⚠️ {f['message']}")

    except Exception as e:
        print(f"⚠️ My Kick Insights Error: {e}")

    return jsonify({
        'user_id': user_id,
        'insights': insights,
        'insight_count': len(insights),
        'prompt_hint': '\n'.join(insights) if insights else None,
    })


# ═════════════════════════════════════════════════
# Staff 대시보드 전용: 킥 전체 요약 (JWT 인증 사용)
# ═════════════════════════════════════════════════

@kick_bp.route('/api/kick/dashboard/overview', methods=['GET'])
@jwt_required()
def get_dashboard_overview():
    """
    의료진 대시보드용 킥 전체 Phase 통합 요약.
    Phase 1(시계열) + Phase 2(언어) + Phase 3(관계)의 플래그를 한 번에 조회.
    """
    current_user_id = get_jwt_identity()
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403
    return _build_dashboard_overview()


@kick_bp.route('/api/kick/dashboard/overview-internal', methods=['GET'])
def get_dashboard_overview_internal():
    """
    Staff 대시보드 프론트엔드 전용 (Django JWT 호환 문제 우회).
    서버 내부에서만 접근 가능 (nginx에서 제한).
    """
    return _build_dashboard_overview()


def _build_dashboard_overview():
    """
    의료진 대시보드용 킥 전체 Phase 통합 요약.
    Phase 1(시계열) + Phase 2(언어) + Phase 3(관계)의 플래그를 한 번에 조회.
    """

    from kick_analysis import analyze_all_users_timeseries

    # Phase 1
    ts_result = analyze_all_users_timeseries(db.session, User, Diary)
    # Phase 2
    lg_result = analyze_all_users_linguistic(db.session, User, Diary, crypto_decrypt=_decrypt_func)
    # Phase 3
    rl_result = analyze_all_users_relational(db.session, User, Diary, crypto_decrypt=_decrypt_func)

    # 통합 플래그
    all_flags = []

    for user_data in ts_result.get('flagged_users', []):
        for flag in user_data.get('flags', []):
            all_flags.append({
                'phase': 'timeseries',
                'phase_label': '시계열',
                'username': user_data.get('username', ''),
                'real_name': user_data.get('real_name', ''),
                'user_id': user_data.get('user_id'),
                **flag
            })

    for user_data in lg_result.get('flagged_users', []):
        for flag in user_data.get('flags', []):
            all_flags.append({
                'phase': 'linguistic',
                'phase_label': '언어 지문',
                'username': user_data.get('username', ''),
                'real_name': user_data.get('real_name', ''),
                'user_id': user_data.get('user_id'),
                **flag
            })

    for user_data in rl_result.get('flagged_users', []):
        for flag in user_data.get('flags', []):
            all_flags.append({
                'phase': 'relational',
                'phase_label': '관계 지형도',
                'username': user_data.get('username', ''),
                'real_name': user_data.get('real_name', ''),
                'user_id': user_data.get('user_id'),
                **flag
            })

    # 심각도순 정렬
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    all_flags.sort(key=lambda x: severity_order.get(x.get('severity', 'low'), 3))

    # 요약 통계
    severity_counts = {'high': 0, 'medium': 0, 'low': 0}
    phase_counts = {'timeseries': 0, 'linguistic': 0, 'relational': 0}
    for f in all_flags:
        severity_counts[f.get('severity', 'low')] = severity_counts.get(f.get('severity', 'low'), 0) + 1
        phase_counts[f.get('phase', '')] = phase_counts.get(f.get('phase', ''), 0) + 1

    flagged_user_ids = set(f.get('user_id') for f in all_flags if f.get('user_id'))

    return jsonify({
        'total_users': ts_result.get('total_users', 0),
        'flagged_user_count': len(flagged_user_ids),
        'total_flags': len(all_flags),
        'by_severity': severity_counts,
        'by_phase': phase_counts,
        'flags': all_flags,
    })

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
