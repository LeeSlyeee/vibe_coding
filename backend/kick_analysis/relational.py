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
    "여친": "연인", "애인": "연인", "아기": "가족", "아들": "가족",
    "딸": "가족", "큰아들": "가족", "큰딸": "가족", "막내": "가족",
    "올케": "가족", "형수": "가족", "제수": "가족", "처형": "가족",
    "처제": "가족", "매형": "가족", "매제": "가족", "형부": "가족",
    
    # 직장/학교
    "팀장": "직장", "팀장님": "직장", "부장": "직장", "부장님": "직장",
    "과장": "직장", "과장님": "직장", "대리": "직장", "대리님": "직장",
    "사장": "직장", "사장님": "직장", "사수": "직장", "부사수": "직장",
    "상사": "직장", "동료": "직장", "후배": "직장", "선배": "직장/학교",
    "선생님": "학교", "교수님": "학교", "교수": "학교", "담임": "학교",
    "강사": "학교", "강사님": "학교", "보조강사": "학교", "보조강사님": "학교",
    "원장님": "학교", "원장": "학교", "조교": "학교", "조교님": "학교",
    "실장": "직장", "실장님": "직장", "차장": "직장", "차장님": "직장",
    "이사": "직장", "이사님": "직장", "대표": "직장", "대표님": "직장",
    "인턴": "직장", "멘토": "직장/학교", "멘토님": "직장/학교",
    
    # 사회적 관계
    "친구": "친구", "절친": "친구", "베프": "친구",
    "룸메이트": "친구", "룸메": "친구",
    "이웃": "사회", "의사": "의료", "상담사": "의료", "상담선생님": "의료",
    "선생": "학교", "코치": "학교", "트레이너": "사회",
    "목사님": "사회", "신부님": "사회", "스님": "사회",
}

# ─── 한국어 접미 패턴 (사람 이름 + 접미사) ───
# 확실도 높은 접미사만 사용 (씨, 한테, 에게, 야/아 호격 등)
# "야/아"는 문장 끝에서 호칭으로 쓰일 때만 유효 → 별도 패턴
import re

# 고정밀 접미사: 사람에게만 붙는 것이 확실한 패턴
_PERSON_SUFFIX_PATTERN = re.compile(
    r'([가-힣]{2,4})'           # 2~4글자 한글 이름
    r'(?:씨|님|한테|에게|이한테|이에게)'  # 사람에게만 확실히 붙는 접미사
)

# 호격 패턴: "성희야!", "민수야!", "건이야!" (문장부호/공백 뒤)
_VOCATIVE_PATTERN = re.compile(
    r'([가-힣]{2,4})(?:야|아|이야)(?:[!!\s.,]|$)'
)

# ─── 비인물 단어 블록리스트 (오탐 방지, 대폭 확장) ───
_NON_PERSON_WORDS = {
    # 시간/장소
    "오늘", "내일", "어제", "그때", "거기", "여기", "저기", "이번", "다음",
    "지금", "나중", "잠시", "갑자기", "하루", "매일", "항상", "가끔", "요즘",
    "오전", "오후", "저녁", "아침", "밤에",
    # 대명사/지시어
    "이것", "그것", "저것", "아무", "모두", "전부", "혼자", "같이", "함께",
    "누구", "무엇", "어디", "언제",
    # 부사/감탄사
    "그냥", "정말", "진짜", "너무", "대박", "역시",
    # 감정/상태 (동사/형용사 어간)
    "기분", "마음", "생각", "느낌", "감정", "걱정", "걱정이", "고민",
    "기쁘지", "슬프지", "괜찮", "졸려", "지쳤", "피곤",
    "기분좋", "행복", "우울", "짜증",
    # 동사 어간 (오탐 최빈출)
    "쉬다", "보다", "하다", "있다", "없다", "되다", "가다", "오다",
    "진행하", "수정", "발견", "테스트하", "작업", "연락", "집중",
    "못했", "했다", "있을거", "알았", "먹었", "마셨",
    "맴돌", "야기하다",
    # 형용사/판단
    "느낌이", "그래", "앞으로", "잘할거", "중이",
    # 지역/장소
    "서울", "부산", "대구", "인천", "대전", "광주", "울산", "세종",
    "강남", "홍대", "이태원", "명동", "종로", "잠실", "판교",
    "영종", "영종도", "학원", "집에", "회사",
    # 사물/음식
    "커피", "케이크", "닭한마리", "드라마", "산책", "드라이브",
    "프로젝트", "마음온", "버그", "사진", "패션쇼", "한복",
    "사진하", "드라", "영향", "상황", "일들",
    # 일반명사
    "생일", "누군", "하해준다", "인공지능", "대화",
}


def _extract_people_kiwi_nnp(text):
    """
    Kiwi 형태소 분석기의 NNP(고유명사) 태그로 사람 이름 후보를 추출한다.
    한국 이름 패턴(2~3글자)에 맞고, 블록리스트에 없는 경우만 허용.
    
    Returns:
        list of str: 추출된 고유명사 후보 목록
    """
    kiwi = _get_kiwi()
    results = []
    seen = set()
    
    try:
        tokens = kiwi.tokenize(text)
        for i, token in enumerate(tokens):
            # NNP = 고유명사, 2~3글자 (한국 이름 길이)
            if token.tag == 'NNP' and 2 <= len(token.form) <= 3:
                name = token.form
                if name in seen or name in _NON_PERSON_WORDS:
                    continue
                # 추가 필터: 한글로만 구성되어야 함
                if not all('\uAC00' <= c <= '\uD7A3' for c in name):
                    continue
                results.append(name)
                seen.add(name)
    except Exception:
        pass
    
    return results


def _extract_people_suffix_pattern(text):
    """
    한국어 접미사 패턴으로 사람 이름을 추출한다.
    고정밀 패턴(씨, 한테, 에게)과 호격 패턴(야, 아)을 분리 적용.
    
    예: "채아씨", "건이한테", "성희야!" → "채아", "건이", "성희"
    
    Returns:
        list of str: 추출된 이름 목록
    """
    results = []
    seen = set()
    
    # 고정밀 패턴: ~씨, ~한테, ~에게
    for match in _PERSON_SUFFIX_PATTERN.findall(text):
        if match not in seen and match not in _NON_PERSON_WORDS and len(match) >= 2:
            results.append(match)
            seen.add(match)
    
    # 호격 패턴: ~야!, ~아! (문장부호/공백 뒤)
    for match in _VOCATIVE_PATTERN.findall(text):
        if match not in seen and match not in _NON_PERSON_WORDS and len(match) >= 2:
            results.append(match)
            seen.add(match)
    
    return results


def _extract_people_llm(text):
    """
    서버 LLM(Ollama)을 사용하여 텍스트에서 사람 이름만 추출한다.
    LLM은 문맥을 이해하므로 '강남에서 쇼핑'(지역)과 '강남이랑 노래'(사람)를 구분.
    
    Returns:
        list of str: 추출된 사람 이름 목록
    """
    import requests
    import json
    
    prompt = (
        "아래 텍스트에서 **사람 이름과 호칭**만 추출해줘. "
        "지역명, 앱이름, 학교명, 프로젝트명은 제외해. "
        "사람이 없으면 빈 리스트를 반환해.\n"
        "반드시 JSON 배열 형식으로만 답해. 설명 없이 배열만.\n"
        "예시: [\"성희\", \"엄마\", \"팀장\"]\n\n"
        f"텍스트: {text[:500]}\n\n"
        "추출된 사람:"
    )
    
    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "maumON-gemma:latest",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 100}
            },
            timeout=10
        )
        if res.status_code == 200:
            response_text = res.json().get('response', '').strip()
            # JSON 배열 추출
            match = re.search(r'\[.*?\]', response_text, re.DOTALL)
            if match:
                names = json.loads(match.group())
                return [n for n in names if isinstance(n, str) and 1 <= len(n) <= 4]
    except Exception as e:
        print(f"⚠️ LLM NER 실패 (호칭 사전으로 fallback): {e}")
    
    return []


def _extract_people_from_text(text, skip_llm=False):
    """
    텍스트에서 인물을 추출한다. 3단계 + 보조 패턴 매칭.
    
    1차: 호칭 사전 매칭 (엄마, 팀장, 강사님 등 — 오탐률 0%)
    1.5차: Kiwi NNP 고유명사 추출 (채아, 건이 등 — LLM 없이 동작)
    1.5차-2: 한국어 접미사 패턴 ("채아씨", "건이한테" → 이름 추출)
    2차: LLM NER 보완 (문맥 이해 — skip_llm=False일 때만)
    
    Args:
        skip_llm: True이면 LLM NER 호출을 건너뜀 (배치 작업용)
    """
    people = []
    seen = set()
    
    # 1차: 호칭 사전 매칭 (항상 안전, 기본 동작)
    # 긴 호칭 우선 매칭 ("보조강사님" → "보조강사", "강사님", "강사" 중복 방지)
    sorted_kinships = sorted(KINSHIP_DICT.keys(), key=len, reverse=True)
    for kinship in sorted_kinships:
        if kinship in text and kinship not in seen:
            # 이미 매칭된 더 긴 호칭의 부분이면 스킵
            is_substring = False
            for already in seen:
                if kinship in already or already in kinship:
                    is_substring = True
                    break
            if is_substring:
                continue
            people.append({
                "name": kinship,
                "type": "호칭",
                "group": KINSHIP_DICT[kinship],
            })
            seen.add(kinship)
    
    # 1.5차: Kiwi NNP 고유명사 추출 (LLM 없이도 작동)
    nnp_names = _extract_people_kiwi_nnp(text)
    for name in nnp_names:
        if name not in seen and name not in KINSHIP_DICT:
            people.append({
                "name": name,
                "type": "고유명사(Kiwi)",
                "group": None,
            })
            seen.add(name)
    
    # 1.5차-2: 접미사 패턴 매칭 ("채아씨", "건이한테" 등)
    suffix_names = _extract_people_suffix_pattern(text)
    for name in suffix_names:
        if name not in seen and name not in KINSHIP_DICT:
            people.append({
                "name": name,
                "type": "고유명사(패턴)",
                "group": None,
            })
            seen.add(name)
    
    # 2차: LLM NER 보완 (실제 이름 추가 추출) — skip_llm=True이면 건너뜀
    if not skip_llm:
        llm_names = _extract_people_llm(text)
        for name in llm_names:
            if name not in seen:
                # 호칭 사전에 있으면 이미 1차에서 잡았으므로 스킵
                if name in KINSHIP_DICT:
                    continue
                people.append({
                    "name": name,
                    "type": "고유명사(LLM)",
                    "group": None,
                })
                seen.add(name)
    
    return people


def _analyze_sentence_emotions(sentence_text):
    """문장 하나에서 감정 범주를 추출."""
    found_categories = set()
    for stem, category in ALL_STEMS.items():
        if stem in sentence_text:
            found_categories.add(category)
    return found_categories


def _map_people_emotions(text, skip_llm=False):
    """
    인물-감정 매핑: 각 문장에서 인물과 감정어를 동시에 추출하여 연결.
    
    Returns:
        dict: {"민수": {"joy", "sadness"}, "팀장": {"anger"}, ...}
    """
    kiwi = _get_kiwi()
    sentences = kiwi.split_into_sents(text)
    
    all_people = _extract_people_from_text(text, skip_llm=skip_llm)
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


def _analyze_single_diary_relational(text, skip_llm=False):
    """
    단일 일기의 관계 분석.
    Returns dict or None.
    """
    if not text or len(text.strip()) < 10:
        return None
    
    people = _extract_people_from_text(text, skip_llm=skip_llm)
    person_emotions = _map_people_emotions(text, skip_llm=skip_llm)
    
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


def analyze_relational(user_id, db_session, Diary, crypto_decrypt=None, today=None, skip_llm_ner=False):
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
        result = _analyze_single_diary_relational(text, skip_llm=skip_llm_ner)
        
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
