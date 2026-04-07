"""
마음온 킥(Kick) 분석 API 라우트
================================
의료진 대시보드 전용 엔드포인트.
Phase 1: 시계열 분석 (timeseries)
Phase 2: 언어 지문 분석 (linguistic)
Phase 3: 관계 지형도 분석 (relational)
Phase 4: 감정 흐름 지도 (emotion_flow)
Phase 5: 수면-마음 상관 (sleep_mind)
Phase 6: 자기 서사 분석 (self_narrative)
마음 컨디션: Phase 1~6 교차 분석 → 케어 가이드
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Diary
from kick_analysis import analyze_timeseries, analyze_all_users_timeseries
from kick_analysis.linguistic import analyze_linguistic, analyze_all_users_linguistic
from kick_analysis.relational import analyze_relational, analyze_all_users_relational
from kick_analysis.emotion_flow import analyze_emotion_flow, analyze_all_users_emotion_flow
from kick_analysis.sleep_mind import analyze_sleep_mind, analyze_all_users_sleep_mind
from kick_analysis.self_narrative import analyze_self_narrative, analyze_all_users_self_narrative
from kick_analysis.condition import generate_condition, generate_all_users_condition

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
    user_id = int(get_jwt_identity())  # [Fix] Gemini 버그 헌팅: int 캐스팅 누락

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

        # Phase 4: 감정 흐름 지도
        ef = analyze_emotion_flow(user_id, db.session, Diary, crypto_decrypt=_decrypt_func)
        if ef.get('status') == 'completed':
            flow = ef.get('emotion_flow', {})
            dom = flow.get('dominant_emotion_label')
            if dom:
                insights.append(f"[감정흐름] 최근 주된 감정: {dom}")
            inertia = flow.get('inertia', {})
            if inertia.get('current_streak', 0) >= 3:
                insights.append(f"[감정흐름] {inertia.get('stuck_emotion_label', '')} 감정 {inertia['current_streak']}일 지속 중")
        for f in ef.get('flags', []):
            insights.append(f"[감정흐름] ⚠️ {f['message']}")

        # Phase 5: 수면-마음 상관
        sm = analyze_sleep_mind(user_id, db.session, Diary, crypto_decrypt=_decrypt_func)
        if sm.get('status') in ('completed', 'limited_data'):
            sleep_data = sm.get('sleep_mind', {})
            recent_7d = sleep_data.get('recent_7d', {})
            avg_score = recent_7d.get('avg_score')
            if avg_score is not None:
                insights.append(f"[수면] 최근 7일 수면 품질: {avg_score:.0f}점")
            corr = sleep_data.get('correlation', {}).get('pearson_r')
            if corr is not None:
                insights.append(f"[수면] 수면-감정 상관: {corr:.2f} ({sleep_data.get('correlation', {}).get('interpretation', '')})")
        for f in sm.get('flags', []):
            insights.append(f"[수면] ⚠️ {f['message']}")

        # Phase 6: 자기 서사 분석
        sn = analyze_self_narrative(user_id, db.session, Diary, crypto_decrypt=_decrypt_func)
        if sn.get('status') == 'completed':
            narr = sn.get('narrative', {}).get('recent_7d', {})
            if narr:
                eff = narr.get('efficacy_score')
                if eff is not None and eff <= 0.3:
                    insights.append(f"[서사] 자기 효능감 낮음 ({eff:.0%})")
                fut = narr.get('future_ratio')
                if fut is not None and fut < 0.1:
                    insights.append("[서사] 미래 지향적 표현이 매우 적음")
        for f in sn.get('flags', []):
            insights.append(f"[서사] ⚠️ {f['message']}")

    except Exception as e:
        print(f"⚠️ My Kick Insights Error: {e}")

    return jsonify({
        'user_id': user_id,
        'insights': insights,
        'insight_count': len(insights),
        'prompt_hint': '\n'.join(insights) if insights else None,
    })


# ═════════════════════════════════════════════════
# 본인용: 마음 컨디션 (Mind Condition)
# ═════════════════════════════════════════════════

@kick_bp.route('/api/kick/my-condition', methods=['GET'])
@jwt_required()
def get_my_condition():
    """
    로그인한 사용자 본인의 마음 컨디션 조회.
    Phase 1~3 교차 분석 → 컨디션 등급 + 케어 가이드.
    의료진 권한 불필요.
    """
    user_id = int(get_jwt_identity())

    try:
        result = generate_condition(
            user_id, db.session, Diary,
            crypto_decrypt=_decrypt_func,
            skip_phase3=True  # LLM NER은 Ollama 타임아웃으로 2분+ 소요 → 앱 타임아웃 방지
        )
        return jsonify(result)
    except Exception as e:
        print(f"⚠️ My Condition Error: {e}")
        # 에러 시에도 기본 응답 (사용자 경험 파괴 방지)
        return jsonify({
            'user_id': user_id,
            'condition': {
                'score': 100,
                'grade': 'sunny',
                'icon': '☀️',
                'label': '활기',
                'message': '오늘도 일기를 쓰고 있는 것만으로 충분히 잘하고 있어요 ✨',
                'care_tip': '좋아하는 음악과 함께 여유로운 시간을 보내보세요 🎵',
            },
            'breakdown': {},
            'signals': ['분석 데이터 준비 중'],
            'signal_count': 0,
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
    current_user_id = int(get_jwt_identity())  # [Fix] Gemini 버그 헌팅: int 캐스팅 누락
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


import threading

_condition_lock = threading.Lock()
_condition_computing = False

@kick_bp.route('/api/kick/dashboard/condition-overview', methods=['GET'])
def get_condition_overview_internal():
    """
    전체 사용자의 마음 컨디션 분포 + 관심 필요 사용자 목록.
    의료진 대시보드 프론트엔드 전용.
    
    [성능] 동시 호출 방지 — 이미 계산 중이면 캐시 또는 202 반환.
    """
    global _condition_computing
    
    from kick_analysis.condition import _condition_cache, _CACHE_TTL_SECONDS
    import time
    
    # 1) 캐시가 유효하면 즉시 반환
    now = time.time()
    if (_condition_cache['data'] is not None
            and _condition_cache['timestamp'] is not None
            and (now - _condition_cache['timestamp']) < _CACHE_TTL_SECONDS):
        return jsonify(_condition_cache['data'])
    
    # 2) 이미 다른 요청이 계산 중이면 즉시 202 반환
    if _condition_computing:
        return jsonify({
            'status': 'computing',
            'message': '컨디션 분석 중입니다. 잠시 후 다시 시도해주세요.'
        }), 202
    
    # 3) 계산 시작
    acquired = _condition_lock.acquire(blocking=False)
    if not acquired:
        return jsonify({
            'status': 'computing',
            'message': '컨디션 분석 중입니다.'
        }), 202
    
    try:
        _condition_computing = True
        result = generate_all_users_condition(
            db.session, User, Diary,
            crypto_decrypt=_decrypt_func
        )
        return jsonify(result)
    except Exception as e:
        print(f"⚠️ Condition Overview Error: {e}")
        return jsonify({
            'error': '컨디션 분석 중 오류 발생',
            'detail': str(e)
        }), 500
    finally:
        _condition_computing = False
        _condition_lock.release()


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
    # Phase 4
    ef_result = analyze_all_users_emotion_flow(db.session, User, Diary, crypto_decrypt=_decrypt_func)
    # Phase 5
    sm_result = analyze_all_users_sleep_mind(db.session, User, Diary, crypto_decrypt=_decrypt_func)
    # Phase 6
    sn_result = analyze_all_users_self_narrative(db.session, User, Diary, crypto_decrypt=_decrypt_func)

    # 통합 플래그
    all_flags = []

    phase_sources = [
        (ts_result, 'timeseries', '시계열'),
        (lg_result, 'linguistic', '언어 지문'),
        (rl_result, 'relational', '관계 지형도'),
        (ef_result, 'emotion_flow', '감정 흐름'),
        (sm_result, 'sleep_mind', '수면-마음'),
        (sn_result, 'self_narrative', '자기 서사'),
    ]

    for phase_result, phase_key, phase_label in phase_sources:
        for user_data in phase_result.get('flagged_users', []):
            for flag in user_data.get('flags', []):
                all_flags.append({
                    'phase': phase_key,
                    'phase_label': phase_label,
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
    phase_counts = {
        'timeseries': 0, 'linguistic': 0, 'relational': 0,
        'emotion_flow': 0, 'sleep_mind': 0, 'self_narrative': 0,
    }
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
    current_user_id = int(get_jwt_identity())  # [Fix] Gemini 버그 헌팅: int 캐스팅 누락
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
    current_user_id = int(get_jwt_identity())  # [Fix] Gemini 버그 헌팅: int 캐스팅 누락
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    result = analyze_all_users_timeseries(db.session, User, Diary)

    return jsonify(result)


@kick_bp.route('/api/kick/timeseries/summary', methods=['GET'])
@jwt_required()
def get_flags_summary():
    """플래그 요약 통계 (대시보드 상단 카드용)"""
    current_user_id = int(get_jwt_identity())  # [Fix] Gemini 버그 헌팅: int 캐스팅 누락
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
    current_user_id = int(get_jwt_identity())  # [Fix] Gemini 버그 헌팅: int 캐스팅 누락
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
    current_user_id = int(get_jwt_identity())  # [Fix] Gemini 버그 헌팅: int 캐스팅 누락
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
    current_user_id = int(get_jwt_identity())  # [Fix] Gemini 버그 헌팅: int 캐스팅 누락
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
    current_user_id = int(get_jwt_identity())  # [Fix] Gemini 버그 헌팅: int 캐스팅 누락
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
    current_user_id = int(get_jwt_identity())  # [Fix] Gemini 버그 헌팅: int 캐스팅 누락
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
    current_user_id = int(get_jwt_identity())  # [Fix] Gemini 버그 헌팅: int 캐스팅 누락
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


# ═════════════════════════════════════════════════
# [앱 사용자용] 주간 편지 및 관계 지형도 조회 (킥 확장)
# ═════════════════════════════════════════════════
from models import WeeklyLetter

@kick_bp.route('/api/kick/my-weekly-letters', methods=['GET'])
@jwt_required()
def get_my_weekly_letters():
    """로그인한 사용자의 주간 편지 목록 조회 (봉투 목록 뷰)"""
    user_id = int(get_jwt_identity())
    
    letters = db.session.query(WeeklyLetter).filter_by(user_id=user_id).order_by(WeeklyLetter.created_at.desc()).all()
    
    result = []
    for l in letters:
        result.append({
            'id': l.id,
            'title': l.title,
            'start_date': l.start_date,
            'end_date': l.end_date,
            'is_read': l.is_read,
            'created_at': l.created_at.isoformat() if l.created_at else None
        })
        
    return jsonify(result), 200

@kick_bp.route('/api/kick/my-weekly-letters/<int:letter_id>', methods=['GET'])
@jwt_required()
def get_my_weekly_letter_detail(letter_id):
    """주간 편지 개봉 (내용 조회 및 읽음 처리)"""
    user_id = int(get_jwt_identity())
    
    letter = db.session.query(WeeklyLetter).filter_by(id=letter_id, user_id=user_id).first()
    if not letter:
        return jsonify({'error': '편지를 찾을 수 없습니다.'}), 404
        
    # 첫 열람 시 읽음 처리
    if not letter.is_read:
        letter.is_read = True
        db.session.commit()
        
    return jsonify({
        'id': letter.id,
        'title': letter.title,
        'content': letter.content,
        'start_date': letter.start_date,
        'end_date': letter.end_date,
        'is_read': letter.is_read,
        'created_at': letter.created_at.isoformat() if letter.created_at else None
    }), 200

@kick_bp.route('/api/kick/relational/my-map', methods=['GET'])
@jwt_required()
def get_my_relational_map():
    """사용자 본인의 관계 지형도 데이터(UI 렌더링용 JSON)
    
    iOS RelationalNode 모델에 맞춰 다음 필드를 포함:
    - id, group, size, color
    - mention_count: 30일간 전체 일기에서 등장 횟수
    - last_seen: 마지막으로 언급된 날짜
    - summary: 감정 기반 한 줄 요약
    """
    user_id = int(get_jwt_identity())
    
    # 사용자 본인 이름 조회 (자기 자신을 별자리에서 제외하기 위함)
    user = User.query.get(user_id)
    self_names = set()
    if user:
        if user.username:
            self_names.add(user.username)
        if user.real_name:
            self_names.add(user.real_name)
            # 이름의 부분도 추가 (예: "이성희" → "성희"도 필터링)
            if len(user.real_name) >= 3:
                self_names.add(user.real_name[1:])  # 성 제외한 이름
    
    # 30일 간의 데이터 분석 (LLM NER 스킵 → 호칭사전 + Kiwi NNP + 패턴 매칭)
    result = analyze_relational(user_id, db.session, Diary, crypto_decrypt=_decrypt_func, skip_llm_ner=True)
    
    if result.get('status') != 'completed':
        return jsonify({'nodes': [], 'links': []}), 200
        
    rel = result.get('relational', {})
    timeline = rel.get('social_density_timeline', [])
    daily_analyses = rel.get('daily_analyses', [])
    
    if not timeline:
        return jsonify({'nodes': [], 'links': []}), 200
    
    # ─── 인물별 통계 집계 (전체 30일 데이터 기반) ───
    from collections import defaultdict
    
    person_mention_count = defaultdict(int)   # 총 등장 횟수
    person_last_seen = {}                      # 마지막 언급일
    person_emotions_all = defaultdict(set)     # 전체 감정
    person_group = {}                          # 관계 그룹
    
    # daily_analyses에서 인물별 등장 횟수 + 마지막 등장일 계산
    for day in daily_analyses:
        date_str = day.get('date', '')
        for person_name in day.get('people', []):
            # 사용자 본인 이름은 별자리에서 제외
            if person_name in self_names:
                continue
            person_mention_count[person_name] += 1
            # 날짜 비교: 더 최근 날짜로 갱신
            if person_name not in person_last_seen or date_str > person_last_seen[person_name]:
                person_last_seen[person_name] = date_str
    
    # timeline에서 인물별 감정 + 그룹 정보 수집
    for week_data in timeline:
        people_emotions = week_data.get('people_emotions', {})
        for person, emo_info in people_emotions.items():
            person_emotions_all[person].update(emo_info.get('emotions', []))
    
    # 호칭사전에서 그룹 매핑
    from kick_analysis.relational import KINSHIP_DICT
    for person_name in person_mention_count:
        if person_name in KINSHIP_DICT:
            person_group[person_name] = KINSHIP_DICT[person_name]
    
    # ─── 색상 팔레트 (그룹별 / 감정별) ───
    GROUP_COLORS = {
        "가족": "#FF6B9D",    # 핑크
        "연인": "#FF4757",    # 로즈
        "친구": "#45B7D1",    # 스카이블루
        "직장": "#FFEAA7",    # 옐로우
        "직장/학교": "#DDA0DD",  # 플럼
        "학교": "#96CEB4",    # 민트
        "의료": "#74B9FF",    # 소프트블루
        "사회": "#A29BFE",    # 라벤더
    }
    VALENCE_COLORS = {
        "positive": "#22C55E",  # 그린
        "negative": "#A855F7",  # 퍼플
        "neutral": "#9CA3AF",   # 그레이
    }
    
    # ─── 감정 기반 요약 생성 ───
    EMOTION_KR = {
        "joy": "기쁨", "comfort": "편안함", "gratitude": "감사",
        "sadness": "슬픔", "anger": "분노", "anxiety": "불안",
        "fatigue": "피로", "loneliness": "외로움",
    }
    
    def _build_summary(person_name, emotions, valence, mention_count, last_seen_date):
        """인물별 한 줄 요약 생성"""
        emotion_labels = [EMOTION_KR.get(e, e) for e in emotions if e in EMOTION_KR]
        
        # 감정이 없으면 기본 메시지
        if not emotion_labels:
            if mention_count >= 5:
                return f"최근 일기에서 자주 등장하는 사람이에요."
            else:
                return f"일기에 {mention_count}번 등장했어요."
        
        emotion_str = ", ".join(emotion_labels[:3])
        
        if valence == "positive":
            if mention_count >= 5:
                return f"자주 떠올리는 소중한 사람이에요. 주로 {emotion_str}의 감정이 함께해요. ✨"
            else:
                return f"{emotion_str}의 감정과 함께 등장했어요. 좋은 에너지를 주는 관계네요."
        elif valence == "negative":
            if mention_count >= 5:
                return f"자주 언급되지만 {emotion_str}의 감정이 동반돼요. 마음의 짐이 될 수 있어요."
            else:
                return f"{emotion_str}의 감정과 연결되어 있어요. 마음을 돌봐주세요."
        else:
            return f"일기에 {mention_count}번 등장했어요. {emotion_str}의 감정이 섞여 있어요."
    
    # ─── 노드 & 링크 구성 ───
    nodes = []
    links = []
    
    # 전체 인물 중 언급 횟수 순으로 정렬 (상위 N명만 표시)
    MAX_NODES = 8  # 너무 많으면 UI가 복잡해지므로 제한
    sorted_people = sorted(person_mention_count.items(), key=lambda x: -x[1])
    top_people = sorted_people[:MAX_NODES]
    
    if not top_people:
        return jsonify({'nodes': [], 'links': []}), 200
    
    # 최대 언급 횟수 (노드 크기 정규화용)
    max_mentions = max(count for _, count in top_people) if top_people else 1
    
    # 중심 노드 (나)
    total_people_count = len(person_mention_count)
    me_summary = f"당신은 이 별자리의 중심이에요. {total_people_count}명의 소중한 사람들이 주변을 밝히고 있어요. 💛" if total_people_count > 0 else "아직 별자리가 형성되고 있어요. 일기에 주변 사람 이야기를 적어보세요. ✨"
    nodes.append({
        "id": "Me",
        "group": 0,
        "size": 35,
        "color": "FFD700",
        "mention_count": None,
        "last_seen": None,
        "summary": me_summary,
    })
    
    # 그룹 인덱스 매핑
    GROUP_INDEX = {"가족": 1, "연인": 1, "친구": 2, "직장": 3, "직장/학교": 3, "학교": 3, "의료": 4, "사회": 4}
    
    for person_name, mention_count in top_people:
        # 감정 valence 계산
        emotions = person_emotions_all.get(person_name, set())
        pos = emotions & {"joy", "comfort", "gratitude"}
        neg = emotions & {"sadness", "anger", "anxiety", "fatigue", "loneliness"}
        valence = "positive" if len(pos) > len(neg) else "negative" if len(neg) > len(pos) else "neutral"
        
        # 색상: 그룹 우선, 없으면 감정 기반
        group = person_group.get(person_name)
        color = GROUP_COLORS.get(group, VALENCE_COLORS.get(valence, "#9CA3AF"))
        # '#' 제거 (iOS에서 Color(hexString:)이 '#' 없이 받을 수 있으므로)
        color = color.lstrip('#')
        
        # 노드 크기: 언급 횟수 비례 (16 ~ 28)
        size = int(16 + (mention_count / max(max_mentions, 1)) * 12)
        
        # 그룹 인덱스
        group_idx = GROUP_INDEX.get(group, 2)
        
        # 마지막 언급일
        last_seen = person_last_seen.get(person_name)
        
        # 요약
        summary = _build_summary(person_name, emotions, valence, mention_count, last_seen)
        
        nodes.append({
            "id": person_name,
            "group": group_idx,
            "size": size,
            "color": color,
            "mention_count": mention_count,
            "last_seen": last_seen,
            "summary": summary,
        })
        
        links.append({
            "source": "Me",
            "target": person_name,
            "value": mention_count,
        })
    
    return jsonify({'nodes': nodes, 'links': links}), 200


# ═════════════════════════════════════════════════
# Phase 4: 감정 흐름 지도 (Emotion Flow Map)
# ═════════════════════════════════════════════════

@kick_bp.route('/api/kick/emotion-flow/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_emotion_flow(user_id):
    """특정 사용자의 감정 흐름 분석 결과 조회 (의료진 전용)"""
    current_user_id = int(get_jwt_identity())
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    target_user = db.session.query(User).filter_by(id=user_id).first()
    if not target_user:
        return jsonify({'error': '사용자를 찾을 수 없습니다'}), 404

    result = analyze_emotion_flow(
        user_id, db.session, Diary,
        crypto_decrypt=_decrypt_func
    )
    result['username'] = target_user.username
    result['real_name'] = target_user.real_name

    return jsonify(result)


@kick_bp.route('/api/kick/emotion-flow/flags', methods=['GET'])
@jwt_required()
def get_emotion_flow_flags():
    """전체 사용자 중 감정 흐름 플래그 발생자 목록 (의료진 대시보드용)"""
    current_user_id = int(get_jwt_identity())
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    result = analyze_all_users_emotion_flow(
        db.session, User, Diary,
        crypto_decrypt=_decrypt_func
    )

    return jsonify(result)


@kick_bp.route('/api/kick/emotion-flow/summary', methods=['GET'])
@jwt_required()
def get_emotion_flow_summary():
    """감정 흐름 플래그 요약 통계 (대시보드 상단 카드용)"""
    current_user_id = int(get_jwt_identity())
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    result = analyze_all_users_emotion_flow(
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
# Phase 5: 수면-마음 상관 분석 (Sleep-Mind Correlation)
# ═════════════════════════════════════════════════

@kick_bp.route('/api/kick/sleep-mind/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_sleep_mind(user_id):
    """특정 사용자의 수면-마음 상관 분석 결과 조회 (의료진 전용)"""
    current_user_id = int(get_jwt_identity())
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    target_user = db.session.query(User).filter_by(id=user_id).first()
    if not target_user:
        return jsonify({'error': '사용자를 찾을 수 없습니다'}), 404

    result = analyze_sleep_mind(
        user_id, db.session, Diary,
        crypto_decrypt=_decrypt_func
    )
    result['username'] = target_user.username
    result['real_name'] = target_user.real_name

    return jsonify(result)


@kick_bp.route('/api/kick/sleep-mind/flags', methods=['GET'])
@jwt_required()
def get_sleep_mind_flags():
    """전체 사용자 중 수면-마음 플래그 발생자 목록 (의료진 대시보드용)"""
    current_user_id = int(get_jwt_identity())
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    result = analyze_all_users_sleep_mind(
        db.session, User, Diary,
        crypto_decrypt=_decrypt_func
    )

    return jsonify(result)


@kick_bp.route('/api/kick/sleep-mind/summary', methods=['GET'])
@jwt_required()
def get_sleep_mind_summary():
    """수면-마음 플래그 요약 통계 (대시보드 상단 카드용)"""
    current_user_id = int(get_jwt_identity())
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    result = analyze_all_users_sleep_mind(
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
# Phase 6: 자기 서사 분석 (Self-Narrative Analysis)
# ═════════════════════════════════════════════════

@kick_bp.route('/api/kick/self-narrative/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_self_narrative(user_id):
    """특정 사용자의 자기 서사 분석 결과 조회 (의료진 전용)"""
    current_user_id = int(get_jwt_identity())
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    target_user = db.session.query(User).filter_by(id=user_id).first()
    if not target_user:
        return jsonify({'error': '사용자를 찾을 수 없습니다'}), 404

    result = analyze_self_narrative(
        user_id, db.session, Diary,
        crypto_decrypt=_decrypt_func
    )
    result['username'] = target_user.username
    result['real_name'] = target_user.real_name

    return jsonify(result)


@kick_bp.route('/api/kick/self-narrative/flags', methods=['GET'])
@jwt_required()
def get_self_narrative_flags():
    """전체 사용자 중 자기 서사 플래그 발생자 목록 (의료진 대시보드용)"""
    current_user_id = int(get_jwt_identity())
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    result = analyze_all_users_self_narrative(
        db.session, User, Diary,
        crypto_decrypt=_decrypt_func
    )

    return jsonify(result)


@kick_bp.route('/api/kick/self-narrative/summary', methods=['GET'])
@jwt_required()
def get_self_narrative_summary():
    """자기 서사 플래그 요약 통계 (대시보드 상단 카드용)"""
    current_user_id = int(get_jwt_identity())
    staff = _require_staff(current_user_id)
    if not staff:
        return jsonify({'error': '의료진 권한이 필요합니다'}), 403

    result = analyze_all_users_self_narrative(
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
# CBT 인지 왜곡 패턴 분석
# ═════════════════════════════════════════════════

@kick_bp.route('/api/kick/my-cbt-patterns', methods=['GET'])
@jwt_required()
def get_my_cbt_patterns():
    """
    로그인한 사용자 본인의 CBT 인지 왜곡 패턴 분석.
    최근 30일 일기에서 12가지 인지 왜곡 패턴을 감지한다.
    의료진 권한 불필요.
    """
    user_id = int(get_jwt_identity())

    from kick_analysis.cbt_patterns import analyze_cbt_patterns
    result = analyze_cbt_patterns(
        user_id, db.session, Diary,
        crypto_decrypt=_decrypt_func,
    )

    return jsonify(result)


@kick_bp.route('/api/kick/cbt-patterns/<int:user_id>', methods=['GET'])
@jwt_required()
def get_cbt_patterns_for_user(user_id):
    """
    [의료진 전용] 특정 사용자의 CBT 인지 왜곡 패턴 분석.
    """
    current_user_id = int(get_jwt_identity())
    current_user = User.query.filter_by(id=current_user_id).first()

    if not current_user or current_user.role not in ('doctor', 'admin', 'staff', 'therapist'):
        return jsonify({'error': '의료진 권한이 필요합니다.'}), 403

    target_user = User.query.filter_by(id=user_id).first()
    if not target_user:
        return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404

    from kick_analysis.cbt_patterns import analyze_cbt_patterns
    result = analyze_cbt_patterns(
        user_id, db.session, Diary,
        crypto_decrypt=_decrypt_func,
    )

    # 의료진용: 사용자 이름 추가
    result['username'] = target_user.username
    result['real_name'] = target_user.real_name

    return jsonify(result)

