"""
마음온 킥(Kick) 분석 — CBT 인지 왜곡 패턴 분석
=================================================
12가지 CBT(인지행동치료) 인지 왜곡 패턴을 일기 텍스트에서 감지한다.

원칙:
  - LLM 사용 없음. 순수 Python 키워드/정규식 패턴 매칭.
  - 틀려도 사용자에게 해가 없는 메시지만 사용.
  - 진단/예측 금지. 패턴 관찰만 제공.
"""

import re
from collections import Counter
from datetime import datetime, timedelta


# ═══ 12가지 CBT 인지 왜곡 패턴 정의 ═══

CBT_PATTERNS = {
    'all_or_nothing': {
        'name_ko': '흑백사고',
        'name_en': 'All-or-Nothing Thinking',
        'description': '상황을 양극단으로만 바라보는 경향',
        'keywords': [
            '항상', '절대', '완전히', '전혀', '무조건', '반드시',
            '언제나', '영원히', '100%', '0%', '전부', '하나도',
            '완벽', '최악', '최고', '다 망했', '다 끝났', '아무것도',
        ],
        'icon': '⬛⬜',
        'care_tip': '세상에는 회색 지대도 있어요. "조금은", "어느 정도는"이란 표현을 시도해보세요.',
    },
    'overgeneralization': {
        'name_ko': '과잉일반화',
        'name_en': 'Overgeneralization',
        'description': '한 번의 경험을 모든 상황에 적용하는 경향',
        'keywords': [
            '맨날', '매번', '늘', '항상 그래', '또 그러네',
            '매번 이러', '늘 이렇게', '한 번도', '아무도',
            '누구나', '어디서나', '모든 사람', '다들',
        ],
        'icon': '🔄',
        'care_tip': '"이번에는"이라고 범위를 좁혀보면 마음이 조금 가벼워질 수 있어요.',
    },
    'mental_filter': {
        'name_ko': '정신적 필터',
        'name_en': 'Mental Filter',
        'description': '부정적인 면만 골라서 집중하는 경향',
        'keywords': [
            '그것만 생각', '다 좋은데 하나가', '하나 빼고',
            '그거 때문에', '그것만', '나쁜 것만',
            '안 좋은 것만', '부정적', '단점만',
        ],
        'icon': '🔍',
        'care_tip': '오늘 하루에서 작은 좋은 점 하나를 찾아보는 연습을 해볼까요?',
    },
    'disqualifying_positive': {
        'name_ko': '긍정 격하',
        'name_en': 'Disqualifying the Positive',
        'description': '긍정적인 경험을 무시하거나 격하하는 경향',
        'keywords': [
            '그건 별거 아니', '운이 좋았', '어쩌다',
            '그건 당연', '누구나 하는', '그냥 그런',
            '대단한 거 아니', '아무나', '그까짓',
        ],
        'icon': '🚫✨',
        'care_tip': '스스로의 노력을 인정하는 것도 큰 용기예요. 오늘 잘한 것 하나를 적어볼까요?',
    },
    'mind_reading': {
        'name_ko': '독심술',
        'name_en': 'Mind Reading',
        'description': '상대방의 생각을 확인 없이 단정하는 경향',
        'keywords': [
            '분명 나를', '틀림없이', '그 사람은 나를',
            '날 싫어', '날 무시', '나를 이상하게',
            '뒤에서 나를', '분명히 생각', '속으로 비웃',
        ],
        'icon': '🧠❓',
        'care_tip': '상대의 마음은 직접 물어보기 전까지 알 수 없어요. 혹시 확인해볼 수 있을까요?',
    },
    'fortune_telling': {
        'name_ko': '점쟁이 오류',
        'name_en': 'Fortune Telling',
        'description': '미래의 결과를 부정적으로 단정하는 경향',
        'keywords': [
            '어차피', '결국엔', '분명 안 될', '틀림없이 망할',
            '될 리가 없', '앞으로도 계속', '나아질 리',
            '소용없', '해봐야', '변하지 않을',
        ],
        'icon': '🔮',
        'care_tip': '미래는 아직 열려 있어요. "만약 잘 된다면?"이라고 한번 생각해보는 건 어떨까요?',
    },
    'catastrophizing': {
        'name_ko': '파국화',
        'name_en': 'Catastrophizing',
        'description': '상황의 심각성을 과장하는 경향',
        'keywords': [
            '끝장', '파멸', '재앙', '대참사', '완전히 망했',
            '인생 끝', '살 수 없', '돌이킬 수 없',
            '최악의 상황', '모든 게 무너', '나락',
        ],
        'icon': '🌋',
        'care_tip': '1년 뒤에도 이 일이 중요할까요? 시간이 지나면 다르게 보일 수 있어요.',
    },
    'minimization': {
        'name_ko': '축소화',
        'name_en': 'Minimization',
        'description': '자신의 장점이나 성취를 축소하는 경향',
        'keywords': [
            '별거 아닌', '아무것도 아닌', '대단할 것 없',
            '하찮은', '그게 뭐', '의미 없', '쓸모없',
            '나 따위', '보잘것없',
        ],
        'icon': '🔎⬇️',
        'care_tip': '작은 성취도 충분히 값져요. 오늘의 작은 승리를 기록해보세요.',
    },
    'emotional_reasoning': {
        'name_ko': '감정적 추론',
        'name_en': 'Emotional Reasoning',
        'description': '감정을 사실의 근거로 삼는 경향',
        'keywords': [
            '느끼니까 사실', '불안하니까 뭔가',
            '기분이 그러니까', '느낌이 그러니',
            '마음이 그러니', '감이', '직감으로',
        ],
        'icon': '💭➡️📋',
        'care_tip': '감정은 중요한 신호이지만, 사실과 같지 않을 수 있어요. 증거를 한번 찾아볼까요?',
    },
    'should_statements': {
        'name_ko': '당위적 사고',
        'name_en': 'Should Statements',
        'description': '"~해야 한다"는 규칙에 자신을 가두는 경향',
        'keywords': [
            '해야 하는데', '했어야', '해야만', '안 하면 안 되',
            '당연히', '마땅히', '의무', '꼭', '반드시',
            '이래야', '저래야', '이렇게 해야',
        ],
        'icon': '📏',
        'care_tip': '"~하면 좋겠다"로 바꿔 말해보면 마음의 짐이 가벼워질 수 있어요.',
    },
    'labeling': {
        'name_ko': '낙인찍기',
        'name_en': 'Labeling',
        'description': '자신이나 타인에게 부정적 딱지를 붙이는 경향',
        'keywords': [
            '나는 바보', '나는 무능', '나는 실패자',
            '멍청이', '쓸모없는 인간', '무가치',
            '나쁜 사람', '한심한', '못난', '패배자',
        ],
        'icon': '🏷️',
        'care_tip': '행동과 사람은 달라요. "이번에 실수했다"와 "나는 바보다"는 완전히 다른 말이에요.',
    },
    'personalization': {
        'name_ko': '개인화',
        'name_en': 'Personalization',
        'description': '외부 사건의 원인을 자신에게로 돌리는 경향',
        'keywords': [
            '내 탓', '내가 잘못해서', '나 때문에',
            '내가 없었으면', '다 나 때문', '내 책임',
            '나만 아니었으면', '내가 그래서',
        ],
        'icon': '👤🎯',
        'care_tip': '모든 일의 원인이 나 하나에게만 있는 경우는 거의 없어요. 다른 요인도 생각해보세요.',
    },
}


def _detect_patterns_in_text(text):
    """
    텍스트에서 CBT 패턴 키워드를 탐지한다.
    
    Returns:
        dict: {pattern_key: match_count, ...}
    """
    if not text or len(text.strip()) < 5:
        return {}

    detected = {}
    text_lower = text.lower()

    for pattern_key, pattern_info in CBT_PATTERNS.items():
        count = 0
        for keyword in pattern_info['keywords']:
            if keyword in text_lower:
                count += 1
        if count > 0:
            detected[pattern_key] = count

    return detected


def analyze_cbt_patterns(user_id, db_session, Diary,
                         crypto_decrypt=None, today=None, days=30):
    """
    사용자의 최근 N일 일기에서 CBT 인지 왜곡 패턴을 분석한다.
    
    Args:
        user_id: 사용자 ID
        db_session: SQLAlchemy session
        Diary: Diary 모델
        crypto_decrypt: 복호화 함수
        today: 기준일
        days: 분석 기간 (기본 30일)
    
    Returns:
        dict: CBT 분석 결과
    """
    base_date = today or datetime.utcnow().date()
    if isinstance(base_date, datetime):
        base_date = base_date.date()

    start_date = base_date - timedelta(days=days)
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = base_date.strftime('%Y-%m-%d')

    # 일기 조회
    diaries = db_session.query(Diary).filter(
        Diary.user_id == user_id,
        Diary.date >= start_str,
        Diary.date <= end_str,
    ).order_by(Diary.date.asc()).all()

    if not diaries:
        return {
            'status': 'no_data',
            'user_id': user_id,
            'period': {'start': start_str, 'end': end_str, 'days': days},
            'message': '분석할 일기 데이터가 없습니다.',
        }

    # 전체 텍스트 누적 분석 + 일별 상세
    total_counts = Counter()
    daily_details = []
    diary_count = 0

    for d in diaries:
        # 복호화
        text = ""
        try:
            if crypto_decrypt and d.event:
                text = crypto_decrypt(d.event) or ""
            elif d.event:
                text = d.event
        except Exception:
            text = d.event or ""

        # emotion_desc, self_talk도 포함
        extras = []
        for field in ['emotion_desc', 'self_talk']:
            raw = getattr(d, field, None) or ''
            if crypto_decrypt and raw:
                try:
                    raw = crypto_decrypt(raw) or raw
                except Exception:
                    pass
            if raw:
                extras.append(raw)

        combined = f"{text} {' '.join(extras)}".strip()
        if not combined:
            continue

        diary_count += 1
        detected = _detect_patterns_in_text(combined)

        if detected:
            for pk, cnt in detected.items():
                total_counts[pk] += cnt

            daily_details.append({
                'date': d.date,
                'mood_level': d.mood_level,
                'patterns': detected,
            })

    # 결과 정리: 빈도순 정렬
    ranked = total_counts.most_common()

    patterns_result = []
    for pattern_key, count in ranked:
        info = CBT_PATTERNS[pattern_key]
        patterns_result.append({
            'key': pattern_key,
            'name_ko': info['name_ko'],
            'name_en': info['name_en'],
            'description': info['description'],
            'icon': info['icon'],
            'count': count,
            'care_tip': info['care_tip'],
        })

    # 주요 패턴 (상위 3개)
    top_patterns = patterns_result[:3]

    return {
        'status': 'completed',
        'user_id': user_id,
        'period': {'start': start_str, 'end': end_str, 'days': days},
        'diary_count': diary_count,
        'total_pattern_hits': sum(total_counts.values()),
        'unique_patterns': len(total_counts),
        'top_patterns': top_patterns,
        'all_patterns': patterns_result,
        'daily_details': daily_details[-10:],  # 최근 10일만 상세 반환
    }
