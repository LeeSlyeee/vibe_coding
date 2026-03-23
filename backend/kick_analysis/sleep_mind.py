"""
마음온 킥(Kick) 분석 모듈 — 수면-마음 상관 분석 (Phase 5)
==========================================================
수면 패턴과 감정/행동 지표를 교차 분석하여
수면-정신건강 연관성 신호를 감지한다.

학술 근거:
  - Walker (2017) "Why We Sleep": 수면 부족 → 감정 조절 편도체 60%+ 반응 증가
  - Baglioni et al. (2016): 수면 장애 → 우울증 발생 위험 2배
  - Harvey (2011): 수면 일기 기반 인지행동치료(CBT-I)

분석 항목:
  1. 수면 키워드 분석 — sleep_condition 텍스트에서 긍/부정 추출
  2. 수면 품질 점수 — 키워드 기반 0~100 환산
  3. 수면-감정 상관 — 수면 품질과 다음날 mood_level 상관계수
  4. 수면 품질 추이 — 7일 이동평균 변화
  5. 수면-감정 교차표 — 수면 좋은 날 vs 나쁜 날의 감정 차이

LLM 사용: 없음. 키워드 사전 기반 순수 Python 연산.
"""

from datetime import datetime, timedelta
from collections import defaultdict

# ─── 수면 키워드 사전 ───
# 한국어 수면 관련 표현을 긍정/부정으로 분류
SLEEP_POSITIVE_KEYWORDS = [
    "잘 잤", "숙면", "깊이 잤", "깊게 잤", "푹 잤", "개운",
    "상쾌", "기분 좋게 일어", "좋은 잠", "편히 잤", "편안하게 잤",
    "피로 풀", "충분히 잤", "잠이 잘", "꿀잠", "단잠",
    "일찍 잤", "적당히 잤", "충분한 수면", "수면 좋",
    "아침이 좋", "잘 잠", "꿈 없이", "잘 자",
]

SLEEP_NEGATIVE_KEYWORDS = [
    "못 잤", "잠을 못", "뒤척", "뒤척였", "잠이 안",
    "불면", "새벽에 깸", "자다가 깸", "잠이 깨",
    "악몽", "가위눌", "피곤", "비몽사몽", "멍하",
    "늦게 잤", "밤새", "수면 부족", "졸리", "졸림",
    "일어나기 힘", "기상이 힘", "몸이 무", "찌뿌듯",
    "목 아프", "머리 아프", "두통", "컨디션 나쁨",
    "잠이 부족", "수면 부족", "안 잤", "잠 못",
    "자다 깨", "새벽에 일어", "잠귀가 밝",
]

# 수면 상태 단순 분류 (sleep_condition이 단순 라벨인 경우 대비)
SLEEP_LABEL_SCORES = {
    "좋음": 85, "보통": 55, "나쁨": 25,
    "good": 85, "normal": 55, "bad": 25,
    "매우 좋음": 95, "매우 나쁨": 10,
}


def _score_sleep_text(text):
    """
    수면 텍스트를 분석하여 0~100 수면 품질 점수를 산출.

    Returns:
        score: int (0~100)
        positive_hits: list of str
        negative_hits: list of str
    """
    if not text or len(text.strip()) < 1:
        return None, [], []

    text_lower = text.strip()

    # 1. 단순 라벨 매칭 먼저 시도
    if text_lower in SLEEP_LABEL_SCORES:
        return SLEEP_LABEL_SCORES[text_lower], [], []

    # 2. 키워드 매칭
    pos_hits = [kw for kw in SLEEP_POSITIVE_KEYWORDS if kw in text_lower]
    neg_hits = [kw for kw in SLEEP_NEGATIVE_KEYWORDS if kw in text_lower]

    if not pos_hits and not neg_hits:
        return 50, [], []  # 판별 불가 → 중립

    # 점수 계산: 기본 50 + (긍정 히트 × 15) - (부정 히트 × 15)
    score = 50 + len(pos_hits) * 15 - len(neg_hits) * 15
    score = max(0, min(100, score))

    return score, pos_hits, neg_hits


def _compute_correlation(x_vals, y_vals):
    """
    피어슨 상관계수 (외부 라이브러리 없이 직접 계산).
    두 리스트의 길이가 같아야 함.

    Returns:
        r: float (-1 ~ 1)
    """
    n = len(x_vals)
    if n < 3:
        return None  # 데이터 부족

    mean_x = sum(x_vals) / n
    mean_y = sum(y_vals) / n

    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals))
    denom_x = sum((x - mean_x) ** 2 for x in x_vals) ** 0.5
    denom_y = sum((y - mean_y) ** 2 for y in y_vals) ** 0.5

    if denom_x == 0 or denom_y == 0:
        return 0.0

    return round(numerator / (denom_x * denom_y), 4)


def _moving_average(values, window=7):
    """이동평균 계산. 윈도우보다 짧으면 가용 범위로."""
    result = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        window_vals = values[start:i + 1]
        result.append(round(sum(window_vals) / len(window_vals), 1))
    return result


# ═══ 메인 분석 함수 ═══

def analyze_sleep_mind(user_id, db_session, Diary, crypto_decrypt=None, today=None):
    """
    특정 사용자의 수면-마음 상관관계를 분석한다.

    Args:
        user_id: 사용자 ID
        db_session: SQLAlchemy session
        Diary: Diary 모델 클래스
        crypto_decrypt: 복호화 함수
        today: 기준일 (테스트용)

    Returns:
        dict: 수면-마음 상관 분석 결과 + 플래그
    """
    if today is None:
        today = datetime.utcnow().date()
    elif isinstance(today, datetime):
        today = today.date()

    cutoff_30d = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    cutoff_7d = (today - timedelta(days=6)).strftime('%Y-%m-%d')
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

    # ─── 일별 수면 분석 ───
    daily_records = []
    for diary in all_diaries:
        sleep_text = diary.sleep_condition
        if crypto_decrypt and sleep_text:
            try:
                sleep_text = crypto_decrypt(sleep_text)
            except Exception:
                pass

        sleep_score, pos_hits, neg_hits = _score_sleep_text(sleep_text)

        daily_records.append({
            "date": str(diary.date),
            "sleep_score": sleep_score,  # None이면 수면 기록 없음
            "sleep_positive": pos_hits,
            "sleep_negative": neg_hits,
            "mood_level": diary.mood_level,
            "mood_100": diary.mood_level * 20 if diary.mood_level else None,
            "has_sleep_data": sleep_score is not None,
        })

    # ─── 수면 품질 추이 ───
    sleep_scores = [r["sleep_score"] for r in daily_records if r["sleep_score"] is not None]
    mood_scores = [r["mood_100"] for r in daily_records if r["mood_100"] is not None]

    sleep_ma = _moving_average(sleep_scores) if len(sleep_scores) >= 3 else sleep_scores

    # 수면 데이터가 충분한지 확인
    has_sufficient_sleep = len(sleep_scores) >= 5

    # ─── 수면-감정 상관계수 ───
    # 같은 날의 수면과 감정을 페어링
    paired_data = [
        (r["sleep_score"], r["mood_100"])
        for r in daily_records
        if r["sleep_score"] is not None and r["mood_100"] is not None
    ]

    sleep_vals = [p[0] for p in paired_data]
    mood_vals = [p[1] for p in paired_data]
    correlation = _compute_correlation(sleep_vals, mood_vals)

    # ─── 수면-감정 교차표 ───
    good_sleep_moods = [r["mood_100"] for r in daily_records
                        if r["sleep_score"] is not None and r["sleep_score"] >= 65
                        and r["mood_100"] is not None]
    poor_sleep_moods = [r["mood_100"] for r in daily_records
                        if r["sleep_score"] is not None and r["sleep_score"] <= 35
                        and r["mood_100"] is not None]

    avg_mood_good_sleep = round(sum(good_sleep_moods) / max(len(good_sleep_moods), 1), 1) if good_sleep_moods else None
    avg_mood_poor_sleep = round(sum(poor_sleep_moods) / max(len(poor_sleep_moods), 1), 1) if poor_sleep_moods else None

    # ─── 최근 7일 수면 분석 ───
    recent_records = [r for r in daily_records if r["date"] >= cutoff_7d]
    recent_sleep_scores = [r["sleep_score"] for r in recent_records if r["sleep_score"] is not None]

    # 연속 악화 계산
    consecutive_deterioration = 0
    if len(recent_sleep_scores) >= 2:
        for i in range(len(recent_sleep_scores) - 1, 0, -1):
            if recent_sleep_scores[i] < recent_sleep_scores[i - 1]:
                consecutive_deterioration += 1
            else:
                break

    # 부정 수면 비율
    poor_sleep_days = sum(1 for s in recent_sleep_scores if s <= 35)
    poor_sleep_ratio = round(poor_sleep_days / max(len(recent_sleep_scores), 1), 3)

    # ─── 수면-감정 불일치 감지 ───
    # 수면 좋은데 감정 나쁜 경우 = 내면 이슈 시그널
    disconnect_days = [
        r for r in recent_records
        if r["sleep_score"] is not None and r["sleep_score"] >= 65
        and r["mood_100"] is not None and r["mood_100"] <= 40
    ]

    # ─── 플래그 생성 ───
    flags = []

    # 1) 수면 품질 연속 악화 (3일+)
    if consecutive_deterioration >= 3:
        flags.append({
            'type': 'sleep_deterioration',
            'severity': 'medium',
            'message': f'수면 품질 {consecutive_deterioration}일 연속 악화',
            'detail': f'수면 점수 추이: {" → ".join(str(s)+"점" for s in recent_sleep_scores[-5:])}',
        })

    # 2) 만성 수면 불량 (7일 중 5일+ 부정)
    if has_sufficient_sleep and len(recent_sleep_scores) >= 5 and poor_sleep_days >= 5:
        flags.append({
            'type': 'chronic_poor_sleep',
            'severity': 'high',
            'message': f'최근 7일 중 {poor_sleep_days}일 수면 불량',
            'detail': f'수면 부족 비율 {poor_sleep_ratio:.0%}. 만성 수면 부족 우려.',
        })

    # 3) 수면-감정 불일치 (내면 이슈)
    if len(disconnect_days) >= 2:
        flags.append({
            'type': 'sleep_mood_disconnect',
            'severity': 'medium',
            'message': f'수면은 양호하나 감정 저하 {len(disconnect_days)}일',
            'detail': '수면과 무관한 내면 스트레스 가능성. 상관관계 붕괴 주시.',
        })

    # 4) 수면 패턴 급변 (Baseline 대비)
    if has_sufficient_sleep and len(sleep_scores) >= 10:
        baseline_avg = round(sum(sleep_scores[:len(sleep_scores)//2]) /
                              max(len(sleep_scores[:len(sleep_scores)//2]), 1), 1)
        recent_avg = round(sum(sleep_scores[len(sleep_scores)//2:]) /
                            max(len(sleep_scores[len(sleep_scores)//2:]), 1), 1)

        if baseline_avg > 0:
            change_pct = round(((recent_avg - baseline_avg) / baseline_avg) * 100, 1)
            if change_pct <= -30:
                flags.append({
                    'type': 'sleep_pattern_shift',
                    'severity': 'low',
                    'message': f'수면 품질 {abs(change_pct):.0f}% 하락',
                    'detail': f'초기 평균 {baseline_avg}점 → 최근 평균 {recent_avg}점',
                })

    return {
        'user_id': user_id,
        'analysis_date': today_str,
        'status': 'completed' if has_sufficient_sleep else 'limited_data',
        'sleep_mind': {
            'daily_records': daily_records,
            'sleep_scores': sleep_scores,
            'sleep_moving_avg': sleep_ma,
            'mood_scores': mood_scores,
            'correlation': {
                'pearson_r': correlation,
                'interpretation': (
                    '강한 양의 상관' if correlation and correlation >= 0.6
                    else '보통 양의 상관' if correlation and correlation >= 0.3
                    else '약한 상관' if correlation and correlation >= 0
                    else '역 상관' if correlation and correlation < 0
                    else '데이터 부족'
                ),
                'paired_count': len(paired_data),
            },
            'cross_table': {
                'avg_mood_good_sleep': avg_mood_good_sleep,
                'avg_mood_poor_sleep': avg_mood_poor_sleep,
                'good_sleep_count': len(good_sleep_moods),
                'poor_sleep_count': len(poor_sleep_moods),
            },
            'recent_7d': {
                'sleep_scores': recent_sleep_scores,
                'avg_score': round(sum(recent_sleep_scores) / max(len(recent_sleep_scores), 1), 1) if recent_sleep_scores else None,
                'consecutive_deterioration': consecutive_deterioration,
                'poor_sleep_days': poor_sleep_days,
                'poor_sleep_ratio': poor_sleep_ratio,
            },
            'disconnect_days': len(disconnect_days),
        },
        'flags': flags,
        'flag_count': len(flags),
        'has_critical': any(f['severity'] == 'high' for f in flags),
    }


def analyze_all_users_sleep_mind(db_session, User, Diary, crypto_decrypt=None, today=None):
    """전체 사용자의 수면-마음 상관 분석. 플래그 있는 사용자만 반환."""
    users = db_session.query(User).all()
    flagged_users = []

    for user in users:
        result = analyze_sleep_mind(
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
