"""
마음온 킥(Kick) 분석 모듈 — 자기 서사 분석 (Phase 6)
=====================================================
사용자 일기 속 자기 인식(self-perception)과
미래 전망(future orientation) 패턴을 분석한다.

학술 근거:
  - Abramson et al. (1989): 귀인 양식과 우울증 — 내적/안정적 귀인 = 무력감
  - Beck (1967): 인지 삼각 — 자기/세계/미래에 대한 부정적 인지 도식
  - Bandura (1977): 자기 효능감(self-efficacy)과 정신건강
  - Pennebaker (2011): 언어 분석에서 시제 사용과 심리 상태

분석 항목:
  1. 자기 귀인 양식 — "내 탓"(내적) vs "상황 탓"(외적)
  2. 시제 분포 — 과거/현재/미래 표현 비율
  3. 당위 표현 비율 — "~해야 한다" 의무감 패턴
  4. 자기 효능감 — "할 수 있다" vs "못하겠다" 표현
  5. 감사 표현 빈도 — 긍정 서사 밀도

LLM 사용: 없음. Kiwi 형태소 분석 + 패턴 사전 기반.
"""

from kiwipiepy import Kiwi
from datetime import datetime, timedelta
from collections import defaultdict

# Kiwi 싱글톤
_kiwi = None

def _get_kiwi():
    global _kiwi
    if _kiwi is None:
        _kiwi = Kiwi()
    return _kiwi


# ─── 1. 자기 귀인 사전 ───
# 내적 귀인(internal attribution): 나 때문에, 내 잘못
INTERNAL_ATTRIBUTION = [
    "내 탓", "내 잘못", "내가 못해서", "내가 부족해서",
    "내 실수", "내가 잘못했", "나 때문에", "제 탓",
    "스스로 자초", "실력이 부족", "능력이 부족",
    "자격이 없", "부끄러", "창피",
    "바보같", "멍청", "한심", "못나",
]

# 외적 귀인(external attribution): 상황 때문에, 환경 탓
EXTERNAL_ATTRIBUTION = [
    "상황이", "환경이", "운이 없", "재수 없",
    "때문에 어쩔", "어쩔 수 없", "불가피",
    "남들이", "세상이", "사회가", "시스템이",
    "원래 그런", "다 그런", "할 수 없는",
]


# ─── 2. 시제 표현 사전 ───
PAST_MARKERS = [
    "었", "았", "했", "였", "지난", "예전에", "과거에",
    "그때", "당시", "돌아보면", "되돌아", "후회",
]

PRESENT_MARKERS = [
    "지금", "오늘", "현재", "요즘", "이번",
    "하고 있", "는 중", "중이",
]

FUTURE_MARKERS = [
    "겠", "할 거", "할거", "내일", "앞으로", "다음에",
    "계획", "목표", "꿈", "희망",
    "이루", "도전", "시작", "준비",
    "해보", "해볼", "가보", "가볼",
    "될 거", "될거", "좋아질",
]


# ─── 3. 당위 표현 사전 ───
OBLIGATION_PATTERNS = [
    "해야", "하여야", "해야만", "해야겠",
    "하지 않으면", "안 하면 안", "꼭 해야",
    "반드시", "의무", "책임",
    "안 되면", "못 하면 안",
    "어야 한다", "어야 해", "어야만",
]


# ─── 4. 자기 효능감 사전 ───
EFFICACY_POSITIVE = [
    "할 수 있", "할수있", "해낼 수", "해낼수",
    "가능하", "잘 할", "잘할", "자신 있",
    "해볼 만", "도전해볼", "해보자", "할 만",
    "성장", "발전", "능력", "실력이 좋",
    "잘 됐", "잘됐", "성공", "해냈",
]

EFFICACY_NEGATIVE = [
    "못하겠", "못 하겠", "할 수 없", "할수없",
    "불가능", "안 될", "안될", "못 할",
    "자신 없", "자신없", "포기", "그만두",
    "소용없", "무의미", "의미 없",
    "실패할", "망할", "안 되", "안돼",
]


# ─── 5. 감사 표현 사전 ───
GRATITUDE_PATTERNS = [
    "감사", "고마", "다행", "덕분",
    "행운", "복", "은혜", "보답",
    "감격", "고맙",
]


def _count_pattern_hits(text, patterns):
    """텍스트에서 패턴 히트 수와 매칭 단어 반환."""
    hits = []
    for p in patterns:
        if p in text:
            hits.append(p)
    return len(hits), hits


def _analyze_single_diary_narrative(text):
    """
    단일 일기의 자기 서사 분석.
    Returns dict or None.
    """
    if not text or len(text.strip()) < 10:
        return None

    kiwi = _get_kiwi()

    try:
        tokens = kiwi.tokenize(text)
    except Exception:
        return None

    total_tokens = len(tokens)
    if total_tokens < 3:
        return None

    # 1. 귀인 양식 분석
    internal_count, internal_hits = _count_pattern_hits(text, INTERNAL_ATTRIBUTION)
    external_count, external_hits = _count_pattern_hits(text, EXTERNAL_ATTRIBUTION)
    total_attribution = internal_count + external_count

    if total_attribution > 0:
        internal_ratio = round(internal_count / total_attribution, 3)
    else:
        internal_ratio = 0.5  # 귀인 표현 없으면 중립

    # 2. 시제 분포 분석
    past_count, _ = _count_pattern_hits(text, PAST_MARKERS)
    present_count, _ = _count_pattern_hits(text, PRESENT_MARKERS)
    future_count, _ = _count_pattern_hits(text, FUTURE_MARKERS)
    total_tense = past_count + present_count + future_count

    if total_tense > 0:
        tense_distribution = {
            "past": round(past_count / total_tense, 3),
            "present": round(present_count / total_tense, 3),
            "future": round(future_count / total_tense, 3),
        }
    else:
        tense_distribution = {"past": 0.33, "present": 0.33, "future": 0.33}

    # 3. 당위 표현 분석
    obligation_count, obligation_hits = _count_pattern_hits(text, OBLIGATION_PATTERNS)
    obligation_ratio = round(obligation_count / max(total_tokens, 1) * 100, 3)

    # 4. 자기 효능감 분석
    pos_efficacy_count, pos_efficacy_hits = _count_pattern_hits(text, EFFICACY_POSITIVE)
    neg_efficacy_count, neg_efficacy_hits = _count_pattern_hits(text, EFFICACY_NEGATIVE)
    total_efficacy = pos_efficacy_count + neg_efficacy_count

    if total_efficacy > 0:
        efficacy_score = round(pos_efficacy_count / total_efficacy, 3)
    else:
        efficacy_score = 0.5  # 효능감 표현 없으면 중립

    # 5. 감사 표현 분석
    gratitude_count, gratitude_hits = _count_pattern_hits(text, GRATITUDE_PATTERNS)

    char_count = len(text.replace(' ', '').replace('\n', ''))

    return {
        "attribution": {
            "internal_count": internal_count,
            "external_count": external_count,
            "internal_ratio": internal_ratio,
            "internal_hits": internal_hits[:3],
        },
        "tense": {
            "past": past_count,
            "present": present_count,
            "future": future_count,
            "distribution": tense_distribution,
        },
        "obligation": {
            "count": obligation_count,
            "ratio": obligation_ratio,
            "hits": obligation_hits[:3],
        },
        "efficacy": {
            "positive": pos_efficacy_count,
            "negative": neg_efficacy_count,
            "score": efficacy_score,
        },
        "gratitude": {
            "count": gratitude_count,
            "hits": gratitude_hits[:3],
        },
        "char_count": char_count,
    }


def _compute_narrative_baseline(analyses):
    """분석 결과 리스트로부터 Baseline 평균 계산."""
    if not analyses:
        return None

    n = len(analyses)
    baseline = {
        "internal_ratio": 0,
        "future_ratio": 0,
        "obligation_ratio": 0,
        "efficacy_score": 0,
        "gratitude_per_diary": 0,
        "diary_count": n,
    }

    for a in analyses:
        baseline["internal_ratio"] += a["attribution"]["internal_ratio"]
        baseline["future_ratio"] += a["tense"]["distribution"]["future"]
        baseline["obligation_ratio"] += a["obligation"]["ratio"]
        baseline["efficacy_score"] += a["efficacy"]["score"]
        baseline["gratitude_per_diary"] += a["gratitude"]["count"]

    for key in ["internal_ratio", "future_ratio", "obligation_ratio",
                "efficacy_score", "gratitude_per_diary"]:
        baseline[key] = round(baseline[key] / n, 4)

    return baseline


# ═══ 메인 분석 함수 ═══

def analyze_self_narrative(user_id, db_session, Diary, crypto_decrypt=None, today=None):
    """
    특정 사용자의 자기 서사 패턴을 분석한다.

    Args:
        user_id: 사용자 ID
        db_session: SQLAlchemy session
        Diary: Diary 모델 클래스
        crypto_decrypt: 복호화 함수
        today: 기준일 (테스트용)

    Returns:
        dict: 자기 서사 분석 결과 + Baseline 비교 + 플래그
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

    # ─── Baseline (8~30일 전) vs 최근 7일 ───
    baseline_diaries = [d for d in all_diaries if d.date < cutoff_7d]
    recent_diaries = [d for d in all_diaries if d.date >= cutoff_7d]

    # Baseline 분석
    baseline_analyses = []
    for d in baseline_diaries:
        text = extract_text(d)
        result = _analyze_single_diary_narrative(text)
        if result:
            result["date"] = str(d.date)
            baseline_analyses.append(result)

    baseline = _compute_narrative_baseline(baseline_analyses)

    # 최근 7일 분석
    recent_analyses = []
    for d in recent_diaries:
        text = extract_text(d)
        result = _analyze_single_diary_narrative(text)
        if result:
            result["date"] = str(d.date)
            recent_analyses.append(result)

    if not recent_analyses:
        return {
            'user_id': user_id,
            'analysis_date': today_str,
            'status': 'insufficient_recent',
            'message': '최근 7일 일기가 부족합니다.',
            'baseline': baseline,
            'flags': [],
            'flag_count': 0,
            'has_critical': False,
        }

    recent_avg = _compute_narrative_baseline(recent_analyses)

    # ─── 플래그 생성 ───
    flags = []

    # 1) 자기 비난 급증 (internal_ratio 80%+)
    if recent_avg and recent_avg["internal_ratio"] >= 0.8:
        severity = 'high' if recent_avg["internal_ratio"] >= 0.9 else 'medium'
        flags.append({
            'type': 'self_blame_surge',
            'severity': severity,
            'message': f'자기 비난 표현 비율 {recent_avg["internal_ratio"]:.0%}',
            'detail': (f'Baseline {baseline["internal_ratio"]:.0%} → '
                       f'현재 {recent_avg["internal_ratio"]:.0%}. '
                       '내적 귀인 과다는 무력감 지표.') if baseline else
                      f'내적 귀인 비율 {recent_avg["internal_ratio"]:.0%}',
        })

    # 2) 미래 표현 소멸 (최근 7일 미래 시제 = 0)
    total_future = sum(a["tense"]["future"] for a in recent_analyses)
    if total_future == 0 and len(recent_analyses) >= 3:
        flags.append({
            'type': 'future_absence',
            'severity': 'high',
            'message': '최근 일기에 미래 시제 표현이 전혀 없음',
            'detail': ('미래를 언급하지 않는 것은 희망감 저하의 신호. '
                       f'분석 대상 {len(recent_analyses)}건 일기에서 미래 표현 0회.'),
        })
    elif baseline and recent_avg:
        # 미래 표현 큰 폭 감소
        if (baseline["future_ratio"] > 0 and
                recent_avg["future_ratio"] < baseline["future_ratio"] * 0.3):
            flags.append({
                'type': 'future_absence',
                'severity': 'medium',
                'message': '미래 표현이 baseline 대비 크게 감소',
                'detail': (f'Baseline 미래 비율 {baseline["future_ratio"]:.0%} → '
                           f'현재 {recent_avg["future_ratio"]:.0%}'),
            })

    # 3) 당위 표현 과부하
    if baseline and recent_avg and baseline["obligation_ratio"] > 0:
        obligation_change = ((recent_avg["obligation_ratio"] - baseline["obligation_ratio"])
                              / baseline["obligation_ratio"]) * 100
        if obligation_change >= 200:
            flags.append({
                'type': 'obligation_overload',
                'severity': 'medium',
                'message': f'의무감 표현 {obligation_change:.0f}% 증가',
                'detail': (f'Baseline {baseline["obligation_ratio"]:.3f}% → '
                           f'현재 {recent_avg["obligation_ratio"]:.3f}%. '
                           '"해야 한다" 표현 급증은 심리적 압박감 신호.'),
            })

    # 4) 자기 효능감 붕괴
    if recent_avg and recent_avg["efficacy_score"] <= 0.2 and len(recent_analyses) >= 3:
        severity = 'high'
        flags.append({
            'type': 'efficacy_collapse',
            'severity': severity,
            'message': f'자기 효능감 극히 낮음 ({recent_avg["efficacy_score"]:.0%})',
            'detail': ('"못하겠다" 계열 표현이 "할 수 있다" 표현을 압도. '
                       '자기 효능감 붕괴는 우울증 핵심 인지 지표.'),
        })
    elif (baseline and recent_avg and baseline["efficacy_score"] > 0 and
            recent_avg["efficacy_score"] < baseline["efficacy_score"] * 0.3):
        flags.append({
            'type': 'efficacy_collapse',
            'severity': 'medium',
            'message': '자기 효능감 baseline 대비 급감',
            'detail': (f'Baseline {baseline["efficacy_score"]:.0%} → '
                       f'현재 {recent_avg["efficacy_score"]:.0%}'),
        })

    return {
        'user_id': user_id,
        'analysis_date': today_str,
        'status': 'completed',
        'narrative': {
            'recent_7d': recent_avg,
            'baseline': baseline,
            'recent_details': [
                {
                    "date": a["date"],
                    "internal_ratio": a["attribution"]["internal_ratio"],
                    "future_ratio": a["tense"]["distribution"]["future"],
                    "obligation_ratio": a["obligation"]["ratio"],
                    "efficacy_score": a["efficacy"]["score"],
                    "gratitude_count": a["gratitude"]["count"],
                }
                for a in recent_analyses
            ],
        },
        'flags': flags,
        'flag_count': len(flags),
        'has_critical': any(f['severity'] == 'high' for f in flags),
    }


def analyze_all_users_self_narrative(db_session, User, Diary, crypto_decrypt=None, today=None):
    """전체 사용자의 자기 서사 분석. 플래그 있는 사용자만 반환."""
    users = db_session.query(User).all()
    flagged_users = []

    for user in users:
        result = analyze_self_narrative(
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
