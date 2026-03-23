"""
마음온 킥(Kick) 분석 모듈 — 감정 흐름 지도 (Phase 4)
=====================================================
사용자 일기 속 감정의 시간적 궤적(trajectory)과
감정 전환 패턴(transition pattern)을 분석한다.

학술 근거:
  - Emotional Inertia (Kuppens et al., 2010): 감정 고착은 우울증 핵심 지표
  - Affect Dynamics (Houben et al., 2015): 감정 변동성과 정신건강 상관
  - Circumplex Model (Russell, 1980): 감정의 valence/arousal 2차원 배치

분석 항목:
  1. 일별 감정 궤적 — 날짜별 주요 감정 범주와 valence 기록
  2. 감정 전환 빈도 — 일기 간 감정 범주 전환 횟수
  3. 감정 고착도 (Emotional Inertia) — 동일 부정 감정 지속 일수
  4. 감정 회복 시간 — 부정 감정 후 긍정/중립 복귀까지 소요일
  5. 요일별 감정 분포 — 주중 vs 주말 감정 차이

LLM 사용: 없음. Kiwi + 감정어 사전 기반 순수 Python 연산.
"""

from datetime import datetime, timedelta
from collections import defaultdict, Counter
from .emotion_lexicon import match_emotions_in_text, EMOTION_CATEGORIES

# ─── 감정 valence 분류 ───
POSITIVE_EMOTIONS = {"joy", "comfort", "gratitude"}
NEGATIVE_EMOTIONS = {"sadness", "anger", "anxiety", "fatigue", "loneliness"}
# neutral: 어떤 범주에도 해당하지 않거나 긍/부정 동수


def _classify_valence(categories):
    """감정 범주 집합을 valence로 분류."""
    if not categories:
        return "neutral", 0.5
    pos = categories & POSITIVE_EMOTIONS
    neg = categories & NEGATIVE_EMOTIONS
    if len(pos) > len(neg):
        return "positive", round(len(pos) / max(len(categories), 1), 3)
    elif len(neg) > len(pos):
        return "negative", round(len(neg) / max(len(categories), 1), 3)
    else:
        return "neutral", 0.5


def _analyze_single_diary_emotion(text):
    """
    단일 일기의 감정 흐름 분석.
    Returns dict or None (텍스트 부족 시).
    """
    if not text or len(text.strip()) < 10:
        return None

    result = match_emotions_in_text(text)
    categories = result["found_categories"]
    valence, intensity = _classify_valence(categories)

    return {
        "categories": list(categories),
        "category_count": len(categories),
        "valence": valence,
        "intensity": intensity,
        "found_words": [(w, c) for w, c in result["found_words"]],
        "diversity_score": result["diversity_score"],
    }


def _compute_transitions(daily_results):
    """
    일별 감정 결과 리스트로부터 감정 전환(transition) 분석.

    Returns:
        transitions: list of (date, from_cat, to_cat)
        transition_count: int
        transition_matrix: dict of {(from, to): count}
    """
    transitions = []
    matrix = defaultdict(int)

    for i in range(1, len(daily_results)):
        prev = daily_results[i - 1]
        curr = daily_results[i]

        prev_cats = set(prev["categories"])
        curr_cats = set(curr["categories"])

        # 주요 감정 = 가장 빈번한 범주 (단순히 첫 번째 사용)
        prev_main = prev["categories"][0] if prev["categories"] else "none"
        curr_main = curr["categories"][0] if curr["categories"] else "none"

        if prev_main != curr_main:
            transitions.append({
                "date": curr["date"],
                "from": prev_main,
                "to": curr_main,
            })
            matrix[(prev_main, curr_main)] += 1

    return transitions, len(transitions), dict(
        {f"{k[0]}→{k[1]}": v for k, v in matrix.items()}
    )


def _compute_emotional_inertia(daily_results):
    """
    감정 고착도 (Emotional Inertia) 계산.
    동일 부정 감정이 연속되는 최대 일수.

    Returns:
        max_streak: int (최대 연속 부정 감정 일수)
        current_streak: int (현재 부정 감정 연속 일수)
        stuck_emotion: str or None (고착된 감정 범주)
    """
    if not daily_results:
        return 0, 0, None

    max_streak = 0
    current_streak = 0
    current_emotion = None
    stuck_emotion = None

    for entry in daily_results:
        if entry["valence"] == "negative" and entry["categories"]:
            main_cat = entry["categories"][0]
            if main_cat == current_emotion:
                current_streak += 1
            else:
                current_streak = 1
                current_emotion = main_cat

            if current_streak > max_streak:
                max_streak = current_streak
                stuck_emotion = current_emotion
        else:
            current_streak = 0
            current_emotion = None

    # 현재 진행 중인 streak 계산
    final_streak = 0
    final_emotion = None
    for entry in reversed(daily_results):
        if entry["valence"] == "negative" and entry["categories"]:
            final_streak += 1
            if not final_emotion:
                final_emotion = entry["categories"][0]
        else:
            break

    return max_streak, final_streak, stuck_emotion


def _compute_recovery_time(daily_results):
    """
    감정 회복 시간 계산.
    부정 감정 에피소드 후 긍정/중립으로 복귀까지 일수.

    Returns:
        avg_recovery_days: float
        max_recovery_days: int
        episodes: list of {start_date, end_date, duration, emotion}
    """
    episodes = []
    in_negative = False
    neg_start = None
    neg_emotion = None

    for entry in daily_results:
        if entry["valence"] == "negative":
            if not in_negative:
                in_negative = True
                neg_start = entry["date"]
                neg_emotion = entry["categories"][0] if entry["categories"] else "unknown"
        else:
            if in_negative:
                # 회복 감지
                episodes.append({
                    "start_date": neg_start,
                    "end_date": entry["date"],
                    "duration": _date_diff(neg_start, entry["date"]),
                    "emotion": neg_emotion,
                })
                in_negative = False
                neg_start = None

    # 현재도 부정 상태 진행 중이면 미복구 에피소드로 기록
    if in_negative and neg_start and daily_results:
        episodes.append({
            "start_date": neg_start,
            "end_date": daily_results[-1]["date"],
            "duration": _date_diff(neg_start, daily_results[-1]["date"]),
            "emotion": neg_emotion,
            "ongoing": True,
        })

    durations = [e["duration"] for e in episodes if e["duration"] > 0]
    avg_recovery = round(sum(durations) / max(len(durations), 1), 1) if durations else 0
    max_recovery = max(durations) if durations else 0

    return avg_recovery, max_recovery, episodes


def _date_diff(date_str1, date_str2):
    """두 날짜 문자열 간 일수 차이 계산."""
    try:
        d1 = datetime.strptime(str(date_str1), '%Y-%m-%d').date()
        d2 = datetime.strptime(str(date_str2), '%Y-%m-%d').date()
        return abs((d2 - d1).days)
    except (ValueError, TypeError):
        return 0


def _compute_weekday_distribution(daily_results):
    """
    요일별 감정 분포.
    Returns:
        weekday_stats: dict {MON: {positive: n, negative: n, ...}, ...}
        weekend_vs_weekday: dict (주말 vs 주중 비교)
    """
    weekday_names = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    weekday_emotions = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0, "total": 0})

    for entry in daily_results:
        try:
            dt = datetime.strptime(str(entry["date"]), '%Y-%m-%d')
            day_idx = dt.weekday()  # 0=MON, 6=SUN
            day_name = weekday_names[day_idx]
            weekday_emotions[day_name][entry["valence"]] += 1
            weekday_emotions[day_name]["total"] += 1
        except (ValueError, TypeError):
            continue

    # 주중 vs 주말 비교
    weekday_neg = sum(weekday_emotions[d]["negative"] for d in ["MON", "TUE", "WED", "THU", "FRI"])
    weekday_total = sum(weekday_emotions[d]["total"] for d in ["MON", "TUE", "WED", "THU", "FRI"])
    weekend_neg = sum(weekday_emotions[d]["negative"] for d in ["SAT", "SUN"])
    weekend_total = sum(weekday_emotions[d]["total"] for d in ["SAT", "SUN"])

    weekday_neg_ratio = round(weekday_neg / max(weekday_total, 1), 3)
    weekend_neg_ratio = round(weekend_neg / max(weekend_total, 1), 3)

    return dict(weekday_emotions), {
        "weekday_negative_ratio": weekday_neg_ratio,
        "weekend_negative_ratio": weekend_neg_ratio,
        "weekend_worse": weekend_neg_ratio > weekday_neg_ratio * 1.4 and weekend_total >= 2,
    }


# ═══ 메인 분석 함수 ═══

def analyze_emotion_flow(user_id, db_session, Diary, crypto_decrypt=None, today=None):
    """
    특정 사용자의 감정 흐름을 분석한다.

    Args:
        user_id: 사용자 ID
        db_session: SQLAlchemy session
        Diary: Diary 모델 클래스
        crypto_decrypt: 복호화 함수
        today: 기준일 (테스트용)

    Returns:
        dict: 감정 흐름 분석 결과 + 플래그
    """
    if today is None:
        today = datetime.utcnow().date()
    elif isinstance(today, datetime):
        today = today.date()

    cutoff_30d = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    today_str = today.strftime('%Y-%m-%d')

    all_diaries = (
        db_session.query(Diary)
        .filter(
            Diary.user_id == user_id,
            Diary.date >= cutoff_30d,
            Diary.date <= today_str
        )
        .order_by(Diary.date.asc())
        .all()
    )

    if not all_diaries:
        return {
            'user_id': user_id,
            'analysis_date': today_str,
            'status': 'no_data',
            'message': '분석할 일기 데이터가 없습니다.',
            'flags': [],
            'flag_count': 0,
            'has_critical': False,
        }

    # 텍스트 추출 + 복호화
    def extract_text(diary):
        parts = []
        for field in [diary.event, diary.emotion_desc,
                      diary.emotion_meaning, diary.self_talk]:
            if field:
                text = crypto_decrypt(field) if crypto_decrypt else field
                if text and len(text.strip()) > 2:
                    parts.append(text)
        return ' '.join(parts)

    # ─── 일별 감정 분석 ───
    daily_results = []
    for diary in all_diaries:
        text = extract_text(diary)
        result = _analyze_single_diary_emotion(text)
        if result:
            result["date"] = str(diary.date)
            result["mood_level"] = diary.mood_level
            daily_results.append(result)

    if not daily_results:
        return {
            'user_id': user_id,
            'analysis_date': today_str,
            'status': 'insufficient_data',
            'message': '감정 분석에 충분한 텍스트가 없습니다.',
            'flags': [],
            'flag_count': 0,
            'has_critical': False,
        }

    # ─── 감정 전환 분석 ───
    transitions, transition_count, transition_matrix = _compute_transitions(daily_results)

    # ─── 감정 고착도 ───
    max_inertia, current_inertia, stuck_emotion = _compute_emotional_inertia(daily_results)

    # ─── 감정 회복 시간 ───
    avg_recovery, max_recovery, recovery_episodes = _compute_recovery_time(daily_results)

    # ─── 요일별 분포 ───
    weekday_stats, weekend_comparison = _compute_weekday_distribution(daily_results)

    # ─── 전체 감정 분포 ───
    all_categories = []
    for dr in daily_results:
        all_categories.extend(dr["categories"])
    emotion_distribution = dict(Counter(all_categories))
    dominant_emotion = max(emotion_distribution, key=emotion_distribution.get) if emotion_distribution else None

    # ─── 플래그 생성 ───
    flags = []

    # 1) 감정 고착 (5일+ 동일 부정 감정)
    if max_inertia >= 5:
        emotion_label = EMOTION_CATEGORIES.get(stuck_emotion, {}).get("label", stuck_emotion or "")
        flags.append({
            'type': 'emotional_stagnation',
            'severity': 'high',
            'message': f'"{emotion_label}" 감정에 {max_inertia}일 연속 고착',
            'detail': f'{stuck_emotion} 감정이 {max_inertia}일간 지속됨. Emotional Inertia 지표 경고.',
        })
    elif max_inertia >= 3:
        emotion_label = EMOTION_CATEGORIES.get(stuck_emotion, {}).get("label", stuck_emotion or "")
        flags.append({
            'type': 'emotional_stagnation',
            'severity': 'medium',
            'message': f'"{emotion_label}" 감정이 {max_inertia}일 연속',
            'detail': f'{stuck_emotion} 감정이 {max_inertia}일간 지속 중. 추세 주시 필요.',
        })

    # 2) 감정 급변 (최근 7일 중 전환 5회+)
    recent_transitions = [t for t in transitions
                          if t["date"] >= (today - timedelta(days=6)).strftime('%Y-%m-%d')]
    if len(recent_transitions) >= 5:
        flags.append({
            'type': 'rapid_oscillation',
            'severity': 'medium',
            'message': f'최근 7일간 감정 전환 {len(recent_transitions)}회 (평소 이상)',
            'detail': f'감정 변동성(Affect Variability) 높음. 최근 전환: '
                       + ', '.join(f'{t["from"]}→{t["to"]}' for t in recent_transitions[:3]),
        })

    # 3) 감정 회복 지연 (7일+)
    if max_recovery >= 7:
        flags.append({
            'type': 'recovery_delay',
            'severity': 'medium',
            'message': f'부정 감정 회복에 최대 {max_recovery}일 소요',
            'detail': f'평균 회복 시간 {avg_recovery}일, 최대 {max_recovery}일.',
        })

    # 4) 주말 우울 (weekend depression)
    if weekend_comparison.get("weekend_worse"):
        flags.append({
            'type': 'weekend_depression',
            'severity': 'low',
            'message': '주말 감정이 주중보다 현저히 부정적',
            'detail': (f'주중 부정 비율 {weekend_comparison["weekday_negative_ratio"]:.0%} '
                       f'vs 주말 {weekend_comparison["weekend_negative_ratio"]:.0%}'),
        })

    return {
        'user_id': user_id,
        'analysis_date': today_str,
        'status': 'completed',
        'emotion_flow': {
            'daily_timeline': daily_results,
            'dominant_emotion': dominant_emotion,
            'dominant_emotion_label': EMOTION_CATEGORIES.get(dominant_emotion, {}).get("label", ""),
            'emotion_distribution': emotion_distribution,
            'transitions': {
                'list': transitions[-10:],  # 최근 10건
                'total_count': transition_count,
                'matrix': transition_matrix,
            },
            'inertia': {
                'max_streak': max_inertia,
                'current_streak': current_inertia,
                'stuck_emotion': stuck_emotion,
                'stuck_emotion_label': EMOTION_CATEGORIES.get(stuck_emotion, {}).get("label", ""),
            },
            'recovery': {
                'avg_days': avg_recovery,
                'max_days': max_recovery,
                'episodes': recovery_episodes[-5:],  # 최근 5건
            },
            'weekday_distribution': weekday_stats,
            'weekend_comparison': weekend_comparison,
        },
        'flags': flags,
        'flag_count': len(flags),
        'has_critical': any(f['severity'] == 'high' for f in flags),
    }


def analyze_all_users_emotion_flow(db_session, User, Diary, crypto_decrypt=None, today=None):
    """전체 사용자의 감정 흐름 분석. 플래그 있는 사용자만 반환."""
    users = db_session.query(User).all()
    flagged_users = []

    for user in users:
        result = analyze_emotion_flow(
            user.id, db_session, Diary,
            crypto_decrypt=crypto_decrypt, today=today
        )
        if result.get('flag_count', 0) > 0:
            result['username'] = user.username
            result['real_name'] = user.real_name
            flagged_users.append(result)

    flagged_users.sort(
        key=lambda x: (-int(x.get('has_critical', False)), -x['flag_count'])
    )

    return {
        'analysis_date': (today or datetime.utcnow().date()).strftime('%Y-%m-%d'),
        'total_users': len(users),
        'flagged_count': len(flagged_users),
        'flagged_users': flagged_users,
    }
