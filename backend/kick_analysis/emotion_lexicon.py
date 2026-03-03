"""
한국어 감정어 사전 — 학술 데이터 기반
=====================================
출처: jonghwanhyeon/korean-emotion-lexicon (868개 감정어)
각 단어에 valence(긍정/부정, 0~3)와 arousal(각성도, 0~3) 학술 점수 부여됨.

사용 방식:
  - 어근 기반 매칭 (한국어 교착어 특성 반영)
  - "슬프" 어근 → "슬프다", "슬퍼서", "슬픈", "슬픔" 모두 매칭
  - 8개 감정 범주로 분류하여 "다양성(diversity)" 측정

범주 분류 기준:
  - valence ≥ 2.5 → 긍정 감정
  - valence ≤ 1.5 → 부정 감정
  - arousal ≥ 2.0 → 고각성 (분노, 흥분)
  - arousal ≤ 1.5 → 저각성 (우울, 무기력)
"""

# ─── 8개 감정 범주별 어근 사전 ───
# 학술 감정어 868개에서 어근을 추출하고 범주별로 분류
EMOTION_CATEGORIES = {
    "joy": {
        "label": "기쁨/행복",
        "stems": [
            "기쁘", "행복", "즐겁", "신나", "흥겹", "유쾌", "통쾌",
            "뿌듯", "감격", "감동", "감명", "환희", "희열", "흐뭇",
            "만족", "충만", "벅차", "설레", "들뜨", "흥분",
            "재미있", "재밌", "좋아하", "사랑하", "사랑스럽",
            "상쾌", "개운", "홀가분", "후련", "시원",
        ],
    },
    "sadness": {
        "label": "슬픔/우울",
        "stems": [
            "슬프", "우울", "서럽", "서운", "비참", "처참", "비통",
            "애통", "처량", "참담", "쓸쓸", "허전", "공허", "허무",
            "비애", "애절", "측은", "가엾", "가련", "불쌍",
            "눈물", "울적", "침울", "암울", "그립", "아쉽",
            "낙담", "실망", "절망", "좌절", "상심",
        ],
    },
    "anger": {
        "label": "분노/짜증",
        "stems": [
            "화나", "분노", "짜증", "성나", "격분", "격앙", "울분",
            "노여", "억울", "분하", "원통", "치밀", "부글",
            "열받", "빡치", "짜증나", "어이없", "황당",
            "가증", "밉", "싫", "증오", "혐오", "경멸",
            "못마땅", "불쾌", "거슬", "불만", "불평",
        ],
    },
    "anxiety": {
        "label": "불안/두려움",
        "stems": [
            "불안", "걱정", "두렵", "무섭", "겁나", "공포", "소름",
            "초조", "조마조마", "안절부절", "전전긍긍",
            "긴장", "떨리", "조바심", "노심초사",
            "염려", "근심", "우려", "위태", "불길",
            "겁먹", "두근", "떨", "오싹", "섬뜩",
        ],
    },
    "fatigue": {
        "label": "피로/무기력",
        "stems": [
            "지치", "힘들", "피곤", "무기력", "나른", "늘어지",
            "녹초", "기진맥진", "탈진", "기력",
            "귀찮", "게으", "나태", "권태", "따분", "지루",
            "싫증", "질리", "무감", "무덤덤", "시들",
            "지겹", "식상", "맥빠지", "풀죽",
        ],
    },
    "comfort": {
        "label": "편안/안정",
        "stems": [
            "편안", "안심", "포근", "따뜻", "차분", "평온", "고요",
            "안정", "여유", "느긋", "태평", "한가", "평화",
            "잔잔", "온화", "부드럽", "나긋", "순하",
            "안락", "아늑", "쾌적", "넉넉",
        ],
    },
    "loneliness": {
        "label": "외로움/고립",
        "stems": [
            "외롭", "고독", "쓸쓸", "적적", "고적",
            "혼자", "혼밥", "혼술", "홀로",
            "소외", "고립", "단절", "격리",
            "버림", "버려지", "방치", "무시", "냉대",
        ],
    },
    "gratitude": {
        "label": "감사/다행",
        "stems": [
            "감사", "고맙", "다행", "천만다행",
            "복", "은혜", "덕분", "보답",
            "존경", "경외", "우러", "숭고",
            "경탄", "감탄", "놀랍", "대단",
        ],
    },
}

# 전체 어근 목록 (빠른 검색용)
ALL_STEMS = {}
for category, info in EMOTION_CATEGORIES.items():
    for stem in info["stems"]:
        ALL_STEMS[stem] = category


def match_emotions_in_text(text):
    """
    텍스트에서 감정어를 감지하고 범주별로 분류한다.
    
    Returns:
        dict: {
            "found_categories": set of matched category names,
            "found_words": list of (word, category) tuples,
            "diversity_score": int (매칭된 범주 수, 0~8),
            "diversity_ratio": float (매칭 범주 / 전체 8범주)
        }
    """
    found = []
    found_categories = set()
    
    for stem, category in ALL_STEMS.items():
        if stem in text:
            found.append((stem, category))
            found_categories.add(category)
    
    return {
        "found_categories": found_categories,
        "found_words": found,
        "diversity_score": len(found_categories),
        "diversity_ratio": round(len(found_categories) / 8, 3),
    }


# 편의 함수
def get_category_label(category_name):
    """범주 코드를 한글 레이블로 변환"""
    info = EMOTION_CATEGORIES.get(category_name)
    return info["label"] if info else category_name


def get_all_stems_count():
    """전체 등록된 어근 수 반환"""
    return len(ALL_STEMS)
