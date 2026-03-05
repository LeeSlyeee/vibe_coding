"""
마음온 킥(Kick) 분석 모듈 — 마음 컨디션 (Mind Condition)
========================================================
Phase 1(시계열) + Phase 2(언어 지문) + Phase 3(관계 지형도)를
교차 분석하여 0~100 컨디션 점수를 산출하고,
사용자에게 맞춤 케어 가이드를 제공한다.

원칙:
  - 미래를 예측하지 않는다. 현재 패턴을 읽고 행동을 제안한다.
  - 부정적 예측 대신 긍정적 행동 유도만 한다.
  - 틀려도 사용자에게 해가 없는 메시지만 사용한다.

LLM 사용: 없음. 순수 Python 연산.
"""

import random
from datetime import datetime


# ═══ 컨디션 등급 정의 ═══

CONDITION_GRADES = {
    'sunny': {
        'icon': '☀️',
        'label': '활기',
        'min_score': 80,
        'messages': [
            "지금 흐름이 좋아요! 새로운 활동을 시도해볼 타이밍이에요 ✨",
            "당신의 마음이 활기차 보여요! 이 에너지를 즐겨보세요 🌟",
            "좋은 리듬을 타고 있어요. 오늘 하고 싶었던 일을 해보는 건 어떨까요?",
        ],
        'care_tips': [
            "이 좋은 에너지를 기록해두면, 나중에 힘들 때 꺼내볼 수 있어요 📝",
            "지금 기분을 누군가와 나눠보세요. 좋은 감정은 나누면 더 커져요 💬",
            "새로운 취미나 도전을 시작하기 좋은 시기에요 🚀",
        ],
    },
    'mostly_sunny': {
        'icon': '🌤️',
        'label': '안정',
        'min_score': 60,
        'messages': [
            "안정적인 리듬이에요. 이 루틴을 유지하면 좋겠어요 😊",
            "꾸준히 잘 하고 있어요. 당신의 노력이 느껴져요 💪",
            "마음이 편안한 상태예요. 지금의 페이스를 유지해보세요 🍃",
        ],
        'care_tips': [
            "오늘도 일기를 쓰고 있는 것만으로 충분히 잘하고 있어요 ✨",
            "좋아하는 음악과 함께 여유로운 시간을 보내보세요 🎵",
            "가까운 사람에게 안부 한 마디 전해보는 건 어떨까요? 📱",
        ],
    },
    'partly_cloudy': {
        'icon': '🌥️',
        'label': '전환기',
        'min_score': 40,
        'messages': [
            "조금 쉬어가도 좋은 시기예요. 좋아하는 음악 한 곡 어떨까요? 🎵",
            "마음이 살짝 분주한 것 같아요. 잠깐 멈추고 숨을 고르는 건 어때요?",
            "변화의 시기에는 작은 루틴이 큰 힘이 돼요. 오늘 하나만 지켜보세요 ☕",
        ],
        'care_tips': [
            "5분만 눈을 감고 깊게 호흡해보세요. 작은 쉼표가 큰 차이를 만들어요 🧘",
            "따뜻한 차 한 잔과 함께 오늘 하루를 정리해보세요 ☕",
            "좋아하는 산책로를 걸어보는 건 어떨까요? 발걸음이 마음을 편하게 해줄 거예요 🌿",
        ],
    },
    'cloudy': {
        'icon': '☁️',
        'label': '충전 필요',
        'min_score': 20,
        'messages': [
            "충전이 필요한 시기에요. 가벼운 산책 어때요? 🌿",
            "마음이 조금 지쳐 보여요. 오늘은 무리하지 말고 쉬어도 괜찮아요 💛",
            "지금은 조금 쉬어가는 시간이에요. 당신의 마음도 쉼이 필요해요 🛋️",
        ],
        'care_tips': [
            "오늘은 해야 할 일 대신, 하고 싶은 일 하나만 해보세요 🌸",
            "좋아하는 사람과 짧은 통화 한 번이 큰 위로가 될 수 있어요 📞",
            "일찍 잠자리에 들어보세요. 충분한 수면이 마음의 배터리를 채워줘요 🌙",
        ],
    },
    'rainy': {
        'icon': '🌧️',
        'label': '관심 필요',
        'min_score': 0,
        'messages': [
            "당신의 마음이 좀 지쳐 보여요. 가까운 사람에게 안부를 전해보세요 💛",
            "혼자 감당하지 않아도 돼요. 주변에 이야기해보는 것도 큰 용기에요 🤝",
            "힘든 시간도 지나가요. 오늘 하루만 잘 버텨보아요 🌈",
        ],
        'care_tips': [
            "전문 상담을 받아보는 것도 좋은 방법이에요. 도움을 요청하는 건 약함이 아니에요 💙",
            "지금 당장 할 수 있는 가장 작은 한 걸음부터 시작해보세요 👣",
            "따뜻한 물로 샤워하고, 편한 옷을 입고, 좋아하는 것을 해보세요 🛀",
        ],
    },
}


# ═══ Phase별 점수 산출 ═══

def _compute_ts_score(ts_result):
    """
    Phase 1 (시계열) 결과 → 0~100 점수.
    각 위험 신호가 있으면 감점.
    """
    if not ts_result or ts_result.get('status') == 'no_data':
        return 100, []  # 데이터 없으면 기본 만점 (감점 근거 없음)

    score = 100
    ts = ts_result.get('timeseries', {})
    signals = []

    # 미기록 감지
    if ts.get('inactivity_flag'):
        days = ts.get('days_since_last_entry', 0)
        if days >= 14:
            score -= 35
            signals.append(f'{days}일간 미기록 (심각)')
        elif days >= 7:
            score -= 25
            signals.append(f'{days}일간 미기록')

    # 기록 빈도 급감
    if ts.get('frequency_drop_flag'):
        change = abs(ts.get('frequency_change_pct', 0))
        score -= 20
        signals.append(f'기록 빈도 {change:.0f}% 감소')

    # 마음 온도 연속 하락
    mood = ts.get('mood_trend', {})
    decline_days = mood.get('consecutive_decline_days', 0)
    if mood.get('decline_flag'):
        score -= 25
        signals.append(f'마음 온도 {decline_days}일 연속 하락')
    elif decline_days >= 2:
        score -= 10
        signals.append(f'마음 온도 {decline_days}일 하락 추세')

    # 새벽 기록
    night = ts.get('night_recording', {})
    if night.get('night_flag'):
        score -= 15
        signals.append(f'새벽 기록 비율 {int(night.get("night_ratio", 0) * 100)}%')

    return max(0, score), signals


def _compute_lg_score(lg_result):
    """
    Phase 2 (언어 지문) 결과 → 0~100 점수.
    Baseline 대비 변화가 클수록 감점.
    """
    if not lg_result or lg_result.get('status') != 'completed':
        return 100, []  # 데이터 부족 시 감점 근거 없음

    score = 100
    signals = []
    dev = lg_result.get('linguistic', {}).get('deviation', {})

    if not dev:
        return 100, []  # Baseline 없으면 비교 불가

    # TTR (어휘 다양성) 감소
    ttr = dev.get('ttr', {})
    ttr_change = ttr.get('change_pct', 0)
    if ttr_change <= -40:
        score -= 25
        signals.append(f'어휘 다양성 {abs(ttr_change):.0f}% 감소')
    elif ttr_change <= -25:
        score -= 12
        signals.append(f'어휘 다양성 소폭 감소')

    # 부정어 비율 증가
    neg = dev.get('negation_ratio', {})
    neg_change = neg.get('change_pct', 0)
    if neg_change >= 100:
        score -= 25
        signals.append(f'부정 표현 {neg_change:.0f}% 증가')
    elif neg_change >= 50:
        score -= 12
        signals.append(f'부정 표현 소폭 증가')

    # 자기 집중도 급증
    sf = dev.get('self_focus', {})
    if sf.get('current', 0.5) >= 0.8 and sf.get('change_pct', 0) >= 50:
        score -= 15
        signals.append(f'자기 집중도 급증 ({sf["current"]:.0%})')

    # 글자 수 급감
    cc = dev.get('char_count', {})
    cc_change = cc.get('change_pct', 0)
    if cc_change <= -70:
        score -= 20
        signals.append(f'일기 분량 {abs(cc_change):.0f}% 감소')
    elif cc_change <= -40:
        score -= 10
        signals.append(f'일기 분량 소폭 감소')

    # 감정 다양성 급감
    ed = dev.get('emotion_diversity', {})
    if ed.get('baseline', 0) >= 3 and ed.get('change_pct', 0) <= -50:
        score -= 15
        signals.append(f'감정 표현 단순화')

    return max(0, score), signals


def _compute_rl_score(rl_result):
    """
    Phase 3 (관계 지형도) 결과 → 0~100 점수.
    사회적 밀도 감소, 인물 소멸 시 감점.
    """
    if not rl_result or rl_result.get('status') != 'completed':
        return 100, []  # 데이터 부족 시 감점 근거 없음

    score = 100
    signals = []
    flags = rl_result.get('flags', [])

    for flag in flags:
        flag_type = flag.get('type', '')

        if flag_type == 'social_withdrawal':
            score -= 30
            signals.append('사회적 관계 위축')
        elif flag_type == 'social_isolation':
            score -= 25
            signals.append('타인 언급 없음')
        elif flag_type == 'people_disappearing':
            score -= 20
            signals.append('등장 인물 감소')
        elif flag_type == 'negative_relationship':
            score -= 15
            signals.append('부정적 관계 패턴')

    # 관계 밀도 자체도 고려 (플래그 없어도)
    rel_data = rl_result.get('relational', {})
    total_people = rel_data.get('total_unique_people', 0)
    timeline = rel_data.get('social_density_timeline', [])

    # 30일간 등장 인물이 0명이면 추가 감점
    if total_people == 0 and not any('타인 언급' in s for s in signals):
        score -= 15
        signals.append('30일간 타인 언급 없음')

    return max(0, score), signals


# ═══ 컨디션 종합 산출 ═══

def _score_to_grade(score):
    """점수를 등급 키로 변환."""
    for grade_key, grade_info in CONDITION_GRADES.items():
        if score >= grade_info['min_score']:
            return grade_key
    return 'rainy'  # fallback


def generate_condition(user_id, db_session, Diary, crypto_decrypt=None, today=None, skip_phase3=False):
    """
    특정 사용자의 마음 컨디션을 산출한다.

    Phase 1~3의 결과를 교차 분석하여 0~100 점수를 생성하고,
    등급에 맞는 케어 가이드를 선택한다.

    Args:
        user_id: 사용자 ID
        db_session: SQLAlchemy db.session
        Diary: Diary 모델 클래스
        crypto_decrypt: 복호화 함수
        today: 기준일 (테스트용)

    Returns:
        dict: 컨디션 결과 (점수, 등급, 메시지, 케어 팁, Phase별 상세)
    """
    from kick_analysis import analyze_timeseries
    from kick_analysis.linguistic import analyze_linguistic
    from kick_analysis.relational import analyze_relational

    # ─── Phase별 분석 실행 ───
    ts_result = None
    lg_result = None
    rl_result = None

    try:
        ts_result = analyze_timeseries(user_id, db_session, Diary, today=today)
    except Exception as e:
        print(f"⚠️ Condition: Phase 1 실패: {e}")

    try:
        lg_result = analyze_linguistic(
            user_id, db_session, Diary,
            crypto_decrypt=crypto_decrypt, today=today
        )
    except Exception as e:
        print(f"⚠️ Condition: Phase 2 실패: {e}")

    if not skip_phase3:
        try:
            rl_result = analyze_relational(
                user_id, db_session, Diary,
                crypto_decrypt=crypto_decrypt, today=today
            )
        except Exception as e:
            print(f"⚠️ Condition: Phase 3 실패: {e}")

    # ─── Phase별 점수 산출 ───
    ts_score, ts_signals = _compute_ts_score(ts_result)
    lg_score, lg_signals = _compute_lg_score(lg_result)
    rl_score, rl_signals = _compute_rl_score(rl_result)

    # ─── 가중 합산 ───
    if skip_phase3:
        # Phase 1(53%) + Phase 2(47%) 비율로 재조정
        composite_score = round(
            ts_score * 0.53 +
            lg_score * 0.47,
            1
        )
    else:
        # 기록 패턴(40%) + 언어 변화(35%) + 관계 변화(25%)
        composite_score = round(
            ts_score * 0.40 +
            lg_score * 0.35 +
            rl_score * 0.25,
            1
        )

    # ─── 등급 & 메시지 선택 ───
    grade_key = _score_to_grade(composite_score)
    grade = CONDITION_GRADES[grade_key]

    message = random.choice(grade['messages'])
    care_tip = random.choice(grade['care_tips'])

    # ─── 분석 근거 요약 (signals 중 상위 3개) ───
    all_signals = ts_signals + lg_signals + rl_signals
    top_signals = all_signals[:3] if all_signals else ['현재 특이사항 없음']

    analysis_date = today or datetime.utcnow().date()
    if isinstance(analysis_date, datetime):
        analysis_date = analysis_date.date()

    return {
        'user_id': user_id,
        'analysis_date': analysis_date.strftime('%Y-%m-%d'),
        'condition': {
            'score': composite_score,
            'grade': grade_key,
            'icon': grade['icon'],
            'label': grade['label'],
            'message': message,
            'care_tip': care_tip,
        },
        'breakdown': {
            'timeseries': {
                'score': ts_score,
                'weight': 0.40,
                'signals': ts_signals,
            },
            'linguistic': {
                'score': lg_score,
                'weight': 0.35,
                'signals': lg_signals,
            },
            'relational': {
                'score': rl_score,
                'weight': 0.25,
                'signals': rl_signals,
            },
        },
        'signals': top_signals,
        'signal_count': len(all_signals),
    }


# ═══ 캐싱 ═══

_condition_cache = {
    'data': None,
    'timestamp': None,
}
_CACHE_TTL_SECONDS = 300  # 5분


def generate_all_users_condition(db_session, User, Diary,
                                  crypto_decrypt=None, today=None):
    """
    전체 사용자의 마음 컨디션 조회. 의료진 대시보드용.
    관심 필요(cloudy/rainy) 등급 사용자를 우선 표시.
    
    [성능] 5분간 캐시된 결과를 반환하여 Ollama 과부하 방지.
    """
    import time
    now = time.time()
    
    # 캐시가 유효하면 즉시 반환
    if (_condition_cache['data'] is not None
            and _condition_cache['timestamp'] is not None
            and (now - _condition_cache['timestamp']) < _CACHE_TTL_SECONDS):
        print(f"✅ [Condition] 캐시 사용 (남은 {int(_CACHE_TTL_SECONDS - (now - _condition_cache['timestamp']))}초)")
        return _condition_cache['data']
    
    print("🔄 [Condition] 전체 사용자 컨디션 계산 시작...")
    
    users = db_session.query(User).all()
    results = []

    for user in users:
        try:
            cond = generate_condition(
                user.id, db_session, Diary,
                crypto_decrypt=crypto_decrypt, today=today,
                skip_phase3=True  # 대시보드용: LLM NER 건너뛰어 속도 확보
            )
            cond['username'] = user.username
            cond['real_name'] = getattr(user, 'real_name', None)
            results.append(cond)
        except Exception as e:
            print(f"⚠️ Condition: user={user.id} 실패: {e}")

    # 점수 낮은 순(관심 필요 우선)으로 정렬
    results.sort(key=lambda x: x['condition']['score'])

    # 등급별 분포 집계
    grade_distribution = {}
    for grade_key in CONDITION_GRADES:
        grade_distribution[grade_key] = sum(
            1 for r in results if r['condition']['grade'] == grade_key
        )

    analysis_date = today or datetime.utcnow().date()
    if isinstance(analysis_date, datetime):
        analysis_date = analysis_date.date()

    # 관심 필요 사용자 (cloudy + rainy)
    attention_needed = [
        r for r in results
        if r['condition']['grade'] in ('cloudy', 'rainy')
    ]

    result = {
        'analysis_date': analysis_date.strftime('%Y-%m-%d'),
        'total_users': len(users),
        'grade_distribution': grade_distribution,
        'attention_count': len(attention_needed),
        'attention_users': attention_needed,
        'all_users': results,
    }
    
    # 캐시 저장
    _condition_cache['data'] = result
    _condition_cache['timestamp'] = now
    print(f"✅ [Condition] 계산 완료. {len(users)}명. 5분간 캐시 유지.")
    
    return result
