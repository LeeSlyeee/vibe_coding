"""
마음온 킥(Kick) 분석 모듈 — 언어 지문 (Phase 2)
================================================
Phase 2: Kiwi 형태소 분석기 기반 언어 구조 분석.
LLM 사용 없음. CPU 연산만으로 처리.

학술 근거: LIWC (Pennebaker, 1993~), K-LIWC

분석 항목:
1. 어휘 다양성 (TTR) — 내용어 기반
2. 자기 집중도 — 1인칭 단수 vs 복수 대명사 비율
3. 부정어 비율 — 부정 보조용언/부사 빈도
4. 문장 길이 / 글자 수 — Baseline 대비 변화 추적
5. 감정어 다양성 — 8개 범주 중 몇 개를 사용하는가
"""

from kiwipiepy import Kiwi
from datetime import datetime, timedelta
from sqlalchemy import func
from .emotion_lexicon import match_emotions_in_text

# Kiwi 싱글톤 (서버 기동 시 1회만 로드)
_kiwi = None

def _get_kiwi():
    global _kiwi
    if _kiwi is None:
        _kiwi = Kiwi()
    return _kiwi


def _analyze_single_text(text):
    """
    단일 텍스트에 대한 언어 지문 분석.
    Returns dict or None (텍스트 부족 시).
    """
    if not text or len(text.strip()) < 10:
        return None
    
    kiwi = _get_kiwi()
    
    try:
        tokens = kiwi.tokenize(text)
        sentences = kiwi.split_into_sents(text)
    except Exception:
        return None
    
    # 1. 문장 길이 평균
    sent_lengths = [len(s.text.strip()) for s in sentences if s.text.strip()]
    avg_sent_len = sum(sent_lengths) / max(len(sent_lengths), 1)
    
    # 2. 총 글자 수 (공백 제외)
    char_count = len(text.replace('\n', '').replace(' ', ''))
    
    # 3. 어휘 다양성 (TTR) — 내용어만
    content_words = [t.form for t in tokens
                     if t.tag.startswith(('NN', 'VV', 'VA', 'MAG'))]
    ttr = (len(set(content_words)) / max(len(content_words), 1)
           if content_words else 0.0)
    
    # 4. 자기 집중도 — 1인칭 대명사 비율
    first_sg = sum(1 for t in tokens
                   if t.tag == 'NP' and t.form in ['나', '내', '저', '제'])
    first_pl = sum(1 for t in tokens
                   if t.tag == 'NP' and t.form in ['우리', '저희'])
    total_pronouns = first_sg + first_pl
    self_focus = (first_sg / max(total_pronouns, 1)
                  if total_pronouns > 0 else 0.5)
    
    # 5. 부정어 비율
    negation_count = sum(
        1 for t in tokens
        if t.form in ['않', '못', '안', '없', '말']
        and t.tag.startswith(('VX', 'MAG', 'VA'))
    )
    negation_ratio = negation_count / max(len(tokens), 1)
    
    # 6. 타인 등장 (고유명사)
    people = set(t.form for t in tokens if t.tag == 'NNP')
    
    # 7. 감정어 다양성 (8범주)
    emotion_result = match_emotions_in_text(text)
    
    return {
        'avg_sent_len': round(avg_sent_len, 1),
        'char_count': char_count,
        'ttr': round(ttr, 4),
        'self_focus': round(self_focus, 3),
        'negation_ratio': round(negation_ratio, 4),
        'people_count': len(people),
        'people_names': list(people)[:5],
        'emotion_diversity': emotion_result['diversity_score'],
        'emotion_categories': list(emotion_result['found_categories']),
        'sentence_count': len(sent_lengths),
        'word_count': len(content_words),
    }


def _compute_baseline(analyses):
    """분석 결과 리스트로부터 Baseline 평균 계산."""
    if not analyses:
        return None
    
    n = len(analyses)
    baseline = {}
    keys = ['avg_sent_len', 'char_count', 'ttr', 'self_focus',
            'negation_ratio', 'people_count', 'emotion_diversity',
            'word_count']
    
    for key in keys:
        vals = [a[key] for a in analyses if key in a and a[key] is not None]
        baseline[key] = round(sum(vals) / max(len(vals), 1), 4) if vals else 0
    
    baseline['diary_count'] = n
    return baseline


def _compute_deviation(current, baseline):
    """현재 값과 Baseline 간의 변화율 계산."""
    if not baseline:
        return {}
    
    deviations = {}
    for key in ['avg_sent_len', 'char_count', 'ttr', 'self_focus',
                'negation_ratio', 'people_count', 'emotion_diversity',
                'word_count']:
        base_val = baseline.get(key, 0)
        curr_val = current.get(key, 0)
        
        if base_val != 0:
            change_pct = round(((curr_val - base_val) / abs(base_val)) * 100, 1)
        else:
            change_pct = 0.0
        
        deviations[key] = {
            'baseline': base_val,
            'current': curr_val,
            'change_pct': change_pct,
        }
    
    return deviations


def analyze_linguistic(user_id, db_session, Diary, crypto_decrypt=None, today=None):
    """
    특정 사용자의 언어 지문을 분석한다.
    
    Args:
        user_id: 사용자 ID
        db_session: SQLAlchemy session
        Diary: Diary 모델 클래스
        crypto_decrypt: 복호화 함수 (text -> plain text)
        today: 기준일 (테스트용)
    
    Returns:
        dict: 언어 지문 분석 결과 + Baseline 비교 + 플래그
    """
    if today is None:
        today = datetime.utcnow().date()
    elif isinstance(today, datetime):
        today = today.date()
    
    # ─── 전체 일기 로드 (최근 30일) ───
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
    
    # ─── 텍스트 추출 + 복호화 ───
    def extract_text(diary):
        parts = []
        for field in [diary.event, diary.emotion_desc,
                      diary.emotion_meaning, diary.self_talk]:
            if field:
                text = crypto_decrypt(field) if crypto_decrypt else field
                if text and len(text.strip()) > 2:
                    parts.append(text)
        return ' '.join(parts)
    
    # ─── Baseline: 이전 기간 (8~30일 전) ───
    baseline_diaries = [d for d in all_diaries if d.date < cutoff_7d]
    recent_diaries = [d for d in all_diaries if d.date >= cutoff_7d]
    
    # Baseline 분석
    baseline_analyses = []
    for d in baseline_diaries:
        text = extract_text(d)
        result = _analyze_single_text(text)
        if result:
            result['date'] = d.date
            baseline_analyses.append(result)
    
    baseline = _compute_baseline(baseline_analyses)
    
    # 최근 7일 분석
    recent_analyses = []
    for d in recent_diaries:
        text = extract_text(d)
        result = _analyze_single_text(text)
        if result:
            result['date'] = d.date
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
    
    recent_avg = _compute_baseline(recent_analyses)
    
    # ─── Baseline 대비 변화율 ───
    deviation = _compute_deviation(recent_avg, baseline) if baseline else {}
    
    # ─── 플래그 생성 ───
    flags = []
    
    if baseline and deviation:
        # 어휘 다양성 급감 (40% 이상 감소)
        ttr_change = deviation.get('ttr', {}).get('change_pct', 0)
        if ttr_change <= -40:
            flags.append({
                'type': 'vocab_collapse',
                'severity': 'medium',
                'message': f'어휘 다양성 {abs(ttr_change):.0f}% 감소',
                'detail': (f"Baseline TTR={deviation['ttr']['baseline']:.3f} → "
                           f"현재 {deviation['ttr']['current']:.3f}"),
            })
        
        # 자기 집중도 급증 (Baseline 대비 2배 이상)
        sf = deviation.get('self_focus', {})
        if (sf.get('current', 0.5) >= 0.8 and
                sf.get('change_pct', 0) >= 50):
            flags.append({
                'type': 'self_focus',
                'severity': 'low',
                'message': f'자기 집중도 급증 ({sf["current"]:.0%})',
                'detail': (f"Baseline {sf['baseline']:.0%} → "
                           f"현재 {sf['current']:.0%}"),
            })
        
        # 부정어 비율 급증 (100% 이상 증가)
        neg = deviation.get('negation_ratio', {})
        if neg.get('change_pct', 0) >= 100:
            flags.append({
                'type': 'negation_surge',
                'severity': 'medium',
                'message': f'부정 표현 {neg["change_pct"]:.0f}% 증가',
                'detail': (f"Baseline {neg['baseline']:.4f} → "
                           f"현재 {neg['current']:.4f}"),
            })
        
        # 글자 수 급감 (70% 이상 감소) — "침묵에 가까운 기록"
        cc = deviation.get('char_count', {})
        if cc.get('change_pct', 0) <= -70:
            flags.append({
                'type': 'silence',
                'severity': 'high',
                'message': f'일기 분량 {abs(cc["change_pct"]):.0f}% 감소',
                'detail': (f"Baseline {cc['baseline']:.0f}자 → "
                           f"현재 {cc['current']:.0f}자"),
            })
        
        # 감정어 다양성 급감 (50% 이상 감소)
        ed = deviation.get('emotion_diversity', {})
        if (ed.get('baseline', 0) >= 3 and
                ed.get('change_pct', 0) <= -50):
            flags.append({
                'type': 'emotional_flatness',
                'severity': 'medium',
                'message': f'감정 표현 다양성 {abs(ed["change_pct"]):.0f}% 감소',
                'detail': (f"Baseline {ed['baseline']:.0f}종 → "
                           f"현재 {ed['current']:.0f}종"),
            })
    
    return {
        'user_id': user_id,
        'analysis_date': today_str,
        'status': 'completed',
        'linguistic': {
            'recent_7d': recent_avg,
            'baseline': baseline,
            'deviation': deviation,
            'recent_details': recent_analyses,
        },
        'flags': flags,
        'flag_count': len(flags),
        'has_critical': any(f['severity'] == 'high' for f in flags),
    }


def analyze_all_users_linguistic(db_session, User, Diary, crypto_decrypt=None,
                                  today=None):
    """
    전체 사용자의 언어 지문 분석 수행.
    플래그가 있는 사용자만 반환 (의료진 대시보드용).
    """
    users = db_session.query(User).all()
    flagged_users = []
    
    for user in users:
        result = analyze_linguistic(
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
