"""
마음온 킥(Kick) 분석 모듈 — 관계 지형도 (Phase 3)
===================================================
사용자 일기에서 등장 인물을 추출하고, 인물별 감정을 태깅하며,
사회적 밀도(등장 인물 수)의 시계열 변화를 추적한다.

학술 근거:
  - 사회적 위축(Social Withdrawal)은 우울증의 핵심 행동 지표
  - 일기에서 타인이 서서히 사라지는 현상 = 고립 진행
  - Stirman & Pennebaker (2001): 1인칭 단수 증가 + 타인 언급 감소

분석 항목:
1. 인물 추출 — Kiwi NNP + 호칭 사전
2. 인물별 감정 매핑 — 문장 단위 인물-감정 연결
3. 등장 인물 수 추이 — 주간 unique 인물 카운팅
4. 사회적 밀도 변화 — Baseline 대비 플래그

LLM 사용: 없음. Kiwi + 사전 매칭.
"""

from kiwipiepy import Kiwi
from datetime import datetime, timedelta
from collections import defaultdict
from .emotion_lexicon import match_emotions_in_text, EMOTION_CATEGORIES, ALL_STEMS

# Kiwi 싱글톤 (linguistic.py와 공유)
_kiwi = None

def _get_kiwi():
    global _kiwi
    if _kiwi is None:
        _kiwi = Kiwi()
    return _kiwi


# ─── 호칭 사전 ───
# 한국어 일기에서 고유명사(NNP)가 아닌 일반명사/호칭으로 등장하는 인물 표현
KINSHIP_DICT = {
    # 가족
    "엄마": "가족", "아빠": "가족", "어머니": "가족", "아버지": "가족",
    "할머니": "가족", "할아버지": "가족", "언니": "가족", "오빠": "가족",
    "누나": "가족", "형": "가족", "동생": "가족", "여동생": "가족",
    "남동생": "가족", "이모": "가족", "삼촌": "가족", "고모": "가족",
    "사촌": "가족", "조카": "가족", "며느리": "가족", "시어머니": "가족",
    "시아버지": "가족", "장인": "가족", "장모": "가족",
    "남편": "가족", "아내": "가족", "와이프": "가족", "남친": "연인",
    "여친": "연인", "애인": "연인",
    
    # 직장/학교
    "팀장": "직장", "부장": "직장", "과장": "직장", "대리": "직장",
    "사장": "직장", "사수": "직장", "부사수": "직장", "상사": "직장",
    "동료": "직장", "후배": "직장", "선배": "직장/학교",
    "선생님": "학교", "교수님": "학교", "교수": "학교", "담임": "학교",
    
    # 사회적 관계
    "친구": "친구", "절친": "친구", "베프": "친구",
    "룸메이트": "친구", "룸메": "친구",
    "이웃": "사회", "의사": "의료", "상담사": "의료",
    "선생": "학교", "코치": "학교",
}


# ─── 비인물 고유명사 차단 목록 ───
# Kiwi가 NNP로 태깅하지만 사람이 아닌 것들
# (오탐 발견 시 여기에 추가)
NNP_STOPLIST = {
    # 앱/프로젝트/서비스
    "마음온", "마은", "마음", "리부트", "그래비티", "인사이트",
    "카카오", "네이버", "구글", "애플", "삼성", "인스타", "유튜브",
    # 학교/기관
    "연세대", "연대", "서울대", "고려대", "한양대", "성균관",
    "이화여대", "중앙대", "경희대", "건국대", "동국대",
    # 지역/장소
    "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
    "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
    "강남", "홍대", "신촌", "이태원", "명동", "종로", "잠실",
    # 일반 명사가 NNP로 잡히는 경우
    "오늘", "내일", "어제", "요즘", "최근", "매일",
}

def _extract_people_from_text(text):
    """
    텍스트에서 인물을 추출한다.
    Kiwi NNP (고유명사) + 호칭 사전 매칭.
    
    Returns:
        list of dict: [{"name": "민수", "type": "고유명사", "group": None}, ...]
    """
    kiwi = _get_kiwi()
    tokens = kiwi.tokenize(text)
    
    people = []
    seen = set()
    
    # 1. Kiwi NNP (고유명사) — 사람 이름
    for t in tokens:
        if t.tag == 'NNP' and t.form not in seen:
            # 비인물 고유명사 차단
            if t.form in NNP_STOPLIST:
                continue
            # 장소명, 브랜드명 제외 (간단한 휴리스틱)
            if len(t.form) <= 4 and not any(x in t.form for x in ['시', '구', '동', '점', '역', '대학', '대']):
                people.append({
                    "name": t.form,
                    "type": "고유명사",
                    "group": None,
                })
                seen.add(t.form)
    
    # 2. 호칭 사전 매칭
    for kinship, group in KINSHIP_DICT.items():
        if kinship in text and kinship not in seen:
            people.append({
                "name": kinship,
                "type": "호칭",
                "group": group,
            })
            seen.add(kinship)
    
    return people


def _analyze_sentence_emotions(sentence_text):
    """문장 하나에서 감정 범주를 추출."""
    found_categories = set()
    for stem, category in ALL_STEMS.items():
        if stem in sentence_text:
            found_categories.add(category)
    return found_categories


def _map_people_emotions(text):
    """
    인물-감정 매핑: 각 문장에서 인물과 감정어를 동시에 추출하여 연결.
    
    Returns:
        dict: {"민수": {"joy", "sadness"}, "팀장": {"anger"}, ...}
    """
    kiwi = _get_kiwi()
    sentences = kiwi.split_into_sents(text)
    
    all_people = _extract_people_from_text(text)
    people_names = {p["name"] for p in all_people}
    
    # 인물별 감정 집합
    person_emotions = defaultdict(set)
    
    for sent in sentences:
        sent_text = sent.text
        
        # 이 문장에 등장하는 인물 찾기
        people_in_sent = [name for name in people_names if name in sent_text]
        
        if not people_in_sent:
            continue
        
        # 이 문장의 감정 추출
        emotions = _analyze_sentence_emotions(sent_text)
        
        # 문장에 등장한 모든 인물에 감정 연결
        for person in people_in_sent:
            person_emotions[person].update(emotions)
    
    return dict(person_emotions)


def _analyze_single_diary_relational(text):
    """
    단일 일기의 관계 분석.
    Returns dict or None.
    """
    if not text or len(text.strip()) < 10:
        return None
    
    people = _extract_people_from_text(text)
    person_emotions = _map_people_emotions(text)
    
    # 인물별 감정 정보 통합
    people_detail = []
    for p in people:
        name = p["name"]
        emotions = person_emotions.get(name, set())
        
        # 감정을 긍정/부정으로 분류
        positive_emotions = emotions & {"joy", "comfort", "gratitude"}
        negative_emotions = emotions & {"sadness", "anger", "anxiety", "fatigue", "loneliness"}
        
        people_detail.append({
            "name": name,
            "type": p["type"],
            "group": p["group"],
            "emotions": list(emotions),
            "positive_count": len(positive_emotions),
            "negative_count": len(negative_emotions),
            "valence": ("positive" if len(positive_emotions) > len(negative_emotions)
                       else "negative" if len(negative_emotions) > len(positive_emotions)
                       else "neutral"),
        })
    
    return {
        "people_count": len(people),
        "people": people_detail,
        "unique_names": [p["name"] for p in people],
        "has_family": any(p.get("group") == "가족" for p in people),
        "has_friends": any(p.get("group") == "친구" or p.get("type") == "고유명사" for p in people),
    }


def analyze_relational(user_id, db_session, Diary, crypto_decrypt=None, today=None):
    """
    특정 사용자의 관계 지형도를 분석한다.
    
    Returns:
        dict: 관계 분석 결과 + 사회적 밀도 추이 + 플래그
    """
    if today is None:
        today = datetime.utcnow().date()
    elif isinstance(today, datetime):
        today = today.date()
    
    # 최근 30일 일기 로드
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
    
    # ─── 주차별 분석 ───
    weekly_data = defaultdict(lambda: {
        "people": set(),
        "people_detail": [],
        "diary_count": 0,
        "all_emotions_by_person": defaultdict(set),
    })
    
    all_people_ever = set()
    daily_analyses = []
    
    for diary in all_diaries:
        text = extract_text(diary)
        result = _analyze_single_diary_relational(text)
        
        if not result:
            continue
        
        diary_date = diary.date if hasattr(diary.date, 'isocalendar') else datetime.strptime(str(diary.date), '%Y-%m-%d').date()
        week_key = f"{diary_date.isocalendar()[0]}-W{diary_date.isocalendar()[1]:02d}"
        
        weekly_data[week_key]["people"].update(result["unique_names"])
        weekly_data[week_key]["diary_count"] += 1
        
        for p in result["people"]:
            weekly_data[week_key]["all_emotions_by_person"][p["name"]].update(p["emotions"])
        
        all_people_ever.update(result["unique_names"])
        
        daily_analyses.append({
            "date": str(diary.date),
            "people_count": result["people_count"],
            "people": result["unique_names"],
        })
    
    # ─── 주차별 사회적 밀도 ───
    weeks_sorted = sorted(weekly_data.keys())
    social_density_timeline = []
    
    for week in weeks_sorted:
        wd = weekly_data[week]
        
        # 인물별 감정 요약
        people_emotions = {}
        for person, emotions in wd["all_emotions_by_person"].items():
            pos = emotions & {"joy", "comfort", "gratitude"}
            neg = emotions & {"sadness", "anger", "anxiety", "fatigue", "loneliness"}
            people_emotions[person] = {
                "emotions": list(emotions),
                "valence": ("positive" if len(pos) > len(neg)
                           else "negative" if len(neg) > len(pos)
                           else "neutral"),
            }
        
        social_density_timeline.append({
            "week": week,
            "unique_people": len(wd["people"]),
            "people_names": list(wd["people"]),
            "diary_count": wd["diary_count"],
            "people_emotions": people_emotions,
        })
    
    # ─── 플래그 생성 ───
    flags = []
    
    if len(social_density_timeline) >= 2:
        first_half = social_density_timeline[:len(social_density_timeline)//2]
        second_half = social_density_timeline[len(social_density_timeline)//2:]
        
        avg_first = sum(w["unique_people"] for w in first_half) / max(len(first_half), 1)
        avg_second = sum(w["unique_people"] for w in second_half) / max(len(second_half), 1)
        
        # 사회적 위축: 등장 인물 수 50% 이상 감소
        if avg_first >= 2 and avg_second <= avg_first * 0.5:
            flags.append({
                'type': 'social_withdrawal',
                'severity': 'high',
                'message': f'등장 인물 수 급감 ({avg_first:.1f}명 → {avg_second:.1f}명)',
                'detail': f'사회적 위축 가능성. 초기 평균 {avg_first:.1f}명 → 최근 {avg_second:.1f}명',
            })
        
        # 사회적 고립: 최근 주에 인물 0명
        if social_density_timeline[-1]["unique_people"] == 0:
            recent_diaries = social_density_timeline[-1]["diary_count"]
            if recent_diaries >= 2:
                flags.append({
                    'type': 'social_isolation',
                    'severity': 'high',
                    'message': f'최근 주 일기 {recent_diaries}건에 타인 등장 0명',
                    'detail': '일기를 쓰고 있으나 타인이 전혀 언급되지 않음 = 고립 가능성',
                })
    
    # 부정 관계 집중: 특정 인물이 3회 이상 부정 감정과 연결
    negative_person_counts = defaultdict(int)
    for week_data in social_density_timeline:
        for person, emo_info in week_data.get("people_emotions", {}).items():
            if emo_info["valence"] == "negative":
                negative_person_counts[person] += 1
    
    for person, neg_count in negative_person_counts.items():
        if neg_count >= 3:
            flags.append({
                'type': 'negative_relationship',
                'severity': 'medium',
                'message': f'"{person}"과(와)의 관계에서 지속적 부정 감정 ({neg_count}주)',
                'detail': f'{person}이(가) {neg_count}주 연속 부정 감정과 연결됨',
            })
    
    # 등장 인물 소멸: 이전에 등장했던 사람이 최근 2주 사라짐
    if len(weeks_sorted) >= 3:
        early_people = set()
        for w in social_density_timeline[:-2]:
            early_people.update(w["people_names"])
        
        recent_people = set()
        for w in social_density_timeline[-2:]:
            recent_people.update(w["people_names"])
        
        disappeared = early_people - recent_people
        if len(disappeared) >= 2:
            flags.append({
                'type': 'people_disappearing',
                'severity': 'medium',
                'message': f'{len(disappeared)}명이 최근 일기에서 사라짐',
                'detail': f'사라진 인물: {", ".join(list(disappeared)[:5])}',
            })
    
    return {
        'user_id': user_id,
        'analysis_date': today_str,
        'status': 'completed',
        'relational': {
            'all_people_ever': list(all_people_ever),
            'total_unique_people': len(all_people_ever),
            'social_density_timeline': social_density_timeline,
            'daily_analyses': daily_analyses,
        },
        'flags': flags,
        'flag_count': len(flags),
        'has_critical': any(f['severity'] == 'high' for f in flags),
    }


def analyze_all_users_relational(db_session, User, Diary, crypto_decrypt=None,
                                  today=None):
    """전체 사용자의 관계 지형도 분석. 플래그 있는 사용자만 반환."""
    users = db_session.query(User).all()
    flagged_users = []
    
    for user in users:
        result = analyze_relational(
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
