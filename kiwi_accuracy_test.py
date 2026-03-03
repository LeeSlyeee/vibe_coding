"""
Kiwi 형태소 분석기 — 킥 #2 정확도 검증 테스트
==============================================
실제 일기 텍스트 샘플로 분석 정확도를 시연합니다.
"""
from kiwipiepy import Kiwi
import re

kiwi = Kiwi()

# ─── 테스트 1: 부정 표현 처리 ───
print("=" * 60)
print("테스트 1: 부정 표현 감지 (정규식 vs Kiwi)")
print("=" * 60)

test_sentences = [
    ("슬프지 않다", False, "부정 → 슬프지 않음"),
    ("슬프다", True, "긍정 → 슬픔"),
    ("기쁘지도 않고 슬프지도 않다", False, "이중 부정"),
    ("화나지 않아서 다행이다", False, "부정 → 화나지 않음"),
    ("너무 우울해서 죽겠다", True, "긍정 → 우울함"),
    ("괜찮아요", False, "감정어 아님 (거짓 괜찮음)"),
]

emotion_stems = ["슬프", "우울", "화나", "기쁘", "행복", "즐겁", "불안", "무섭", "외롭"]

for sentence, expected_emotion, desc in test_sentences:
    # 정규식 방식 (조잡)
    regex_found = any(stem in sentence for stem in emotion_stems)
    
    # Kiwi 방식 (정밀)
    tokens = kiwi.tokenize(sentence)
    
    # 부정 보조용언(않, 못, 말) 앞의 감정어는 제외
    kiwi_emotions = []
    for i, token in enumerate(tokens):
        if token.form in emotion_stems or any(stem in token.form for stem in emotion_stems):
            if token.tag.startswith('VA') or token.tag.startswith('VV'):
                # 다음 토큰들에서 부정 보조용언 확인
                is_negated = False
                for j in range(i+1, min(i+4, len(tokens))):
                    if tokens[j].form in ['않', '못', '말', '아니']:
                        is_negated = True
                        break
                if not is_negated:
                    kiwi_emotions.append(token.form)
    
    kiwi_found = len(kiwi_emotions) > 0
    
    regex_correct = "✅" if regex_found == expected_emotion else "❌"
    kiwi_correct = "✅" if kiwi_found == expected_emotion else "❌"
    
    print(f"\n  문장: \"{sentence}\"")
    print(f"  설명: {desc}")
    print(f"  정규식: {'감정 감지' if regex_found else '미감지'} {regex_correct}")
    print(f"  Kiwi:   {'감정 감지' if kiwi_found else '미감지'} {kiwi_correct}  {kiwi_emotions if kiwi_emotions else ''}")
    print(f"  토큰: {[(t.form, t.tag) for t in tokens]}")


# ─── 테스트 2: 대명사 분류 ───
print("\n" + "=" * 60)
print("테스트 2: 대명사 + 자기 집중도 분석")
print("=" * 60)

diary_normal = "오늘 우리 팀이 같이 프로젝트를 마무리했다. 민수랑 저녁도 먹었고, 다들 수고했다고 서로 격려해줬다."
diary_depressed = "나는 오늘도 혼자 집에만 있었다. 내가 뭘 해도 소용이 없는 것 같다. 나만 이렇게 무기력한 건지 모르겠다."

for label, text in [("정상 상태", diary_normal), ("우울 상태", diary_depressed)]:
    tokens = kiwi.tokenize(text)
    
    first_singular = []  # 나, 내, 저(겸양)
    first_plural = []    # 우리, 저희
    other_people = []    # 고유명사, 3인칭
    
    for t in tokens:
        if t.tag == 'NP':  # 대명사
            if t.form in ['나', '내', '저', '제']:
                first_singular.append(t.form)
            elif t.form in ['우리', '저희']:
                first_plural.append(t.form)
        elif t.tag == 'NNP':  # 고유명사
            other_people.append(t.form)
    
    total = len(first_singular) + len(first_plural)
    self_ratio = len(first_singular) / max(total, 1)
    
    print(f"\n  [{label}]")
    print(f"  텍스트: \"{text[:50]}...\"")
    print(f"  1인칭 단수: {first_singular} ({len(first_singular)}회)")
    print(f"  1인칭 복수: {first_plural} ({len(first_plural)}회)")
    print(f"  타인(고유명사): {other_people}")
    print(f"  자기 집중도: {self_ratio:.0%}")
    print(f"  → {'🚨 자기 집중 과잉' if self_ratio > 0.7 else '✅ 균형'}")


# ─── 테스트 3: 시제 분포 ───
print("\n" + "=" * 60)
print("테스트 3: 시제 분포 분석 (미래 시제 소멸 감지)")
print("=" * 60)

diary_with_future = "오늘 힘들었지만, 내일은 친구를 만날 거야. 다음 주에는 여행을 가려고 계획 중이다."
diary_no_future = "오늘도 힘들었다. 어제도 힘들었다. 아무것도 하고 싶지 않았다."

# 한국어 시제 어미 패턴
past_endings = ['었', '았', '였', '했']
future_markers = ['겠', '거야', '거예요', '려고', '할 거', '거다', '텐데', '갈 거', '만날 거']

for label, text in [("미래 지향적", diary_with_future), ("미래 부재", diary_no_future)]:
    tokens = kiwi.tokenize(text)
    
    past_count = 0
    future_count = 0
    present_count = 0
    
    for t in tokens:
        if t.tag.startswith('EP'):  # 선어말어미
            if t.form in past_endings:
                past_count += 1
        elif t.tag.startswith('EF') or t.tag.startswith('EC'):  # 종결/연결 어미
            pass
        
        # 미래 표현 감지 (어미 + 의존명사 패턴)
        if t.form in ['겠', '려고', '텐데']:
            future_count += 1
    
    # 텍스트 기반 미래 마커 보조 검사
    for marker in ['내일', '다음', '계획', '예정', '하려고', '거야', '거예요', '할 거']:
        if marker in text:
            future_count += 1
    
    total_tense = past_count + future_count + max(1, present_count)
    future_ratio = future_count / max(total_tense, 1)
    
    print(f"\n  [{label}]")
    print(f"  텍스트: \"{text[:60]}...\"")
    print(f"  과거 표현: {past_count}회")
    print(f"  미래 표현: {future_count}회")
    print(f"  미래 비율: {future_ratio:.0%}")
    print(f"  → {'✅ 미래 지향적' if future_ratio > 0.2 else '🚨 미래 시제 소멸'}")


# ─── 테스트 4: 어휘 다양성 (TTR) ───
print("\n" + "=" * 60)
print("테스트 4: 어휘 다양성 (Type-Token Ratio)")
print("=" * 60)

diary_diverse = "오늘은 정말 다양한 하루였다. 아침에 조깅을 하고, 점심에 친구와 맛있는 파스타를 먹었다. 오후에는 전시회를 보며 감탄했고, 저녁에는 가족과 영화를 봤다."
diary_monotone = "힘들다. 힘들다. 오늘도 힘들었다. 뭘 해도 힘들고 아무것도 하기 싫다. 그냥 힘들다."

for label, text in [("다양한 표현", diary_diverse), ("단조로운 표현", diary_monotone)]:
    tokens = kiwi.tokenize(text)
    
    # 내용어(명사, 동사, 형용사)만 추출
    content_words = [t.form for t in tokens if t.tag.startswith(('NN', 'VV', 'VA'))]
    
    total = len(content_words)
    unique = len(set(content_words))
    ttr = unique / max(total, 1)
    
    print(f"\n  [{label}]")
    print(f"  텍스트: \"{text[:60]}...\"")
    print(f"  내용어: {content_words}")
    print(f"  총 단어: {total}개 / 고유 단어: {unique}개")
    print(f"  TTR (어휘 다양성): {ttr:.2f}")
    print(f"  → {'✅ 어휘 풍부' if ttr > 0.6 else '🚨 어휘 단조화'}")


# ─── 테스트 5: 종합 — 정상 일기 vs 우울 일기 ───
print("\n" + "=" * 60)
print("테스트 5: 종합 비교 — 정상 일기 vs 우울 일기")
print("=" * 60)

normal_diary = """오늘 회사에서 팀 미팅이 있었는데, 우리 팀이 준비한 발표가 생각보다 잘 돼서 뿌듯했다. 
팀장님도 칭찬해주셨고, 민지랑 같이 커피 마시면서 다음 프로젝트 계획도 이야기했다. 
내일은 주말이라 가족이랑 나들이 갈 예정이다. 날씨가 좋다고 하니까 기대된다."""

depressed_diary = """힘들다. 오늘도 그냥 아무것도 안 했다. 
뭘 해야 하는지도 모르겠고 그냥 누워만 있었다.
아무도 연락 안 온다. 나만 이런 건지."""

for label, text in [("정상 일기", normal_diary), ("우울 일기", depressed_diary)]:
    tokens = kiwi.tokenize(text)
    
    # 문장 분리
    sentences = kiwi.split_into_sents(text)
    avg_sent_len = sum(len(s.text.strip()) for s in sentences) / max(len(sentences), 1)
    
    # 글자 수
    char_count = len(text.replace('\n', '').replace(' ', ''))
    
    # 내용어 TTR
    content_words = [t.form for t in tokens if t.tag.startswith(('NN', 'VV', 'VA'))]
    ttr = len(set(content_words)) / max(len(content_words), 1)
    
    # 1인칭 비율
    pronouns = [t for t in tokens if t.tag == 'NP']
    first_sg = [p for p in pronouns if p.form in ['나', '내', '저', '제']]
    first_pl = [p for p in pronouns if p.form in ['우리', '저희']]
    self_ratio = len(first_sg) / max(len(first_sg) + len(first_pl), 1)
    
    # 타인 등장 (고유명사)
    people = [t.form for t in tokens if t.tag == 'NNP']
    
    print(f"\n  [{label}]")
    print(f"  ┌ 문장 수: {len(sentences)}개")
    print(f"  ├ 평균 문장 길이: {avg_sent_len:.1f}자")
    print(f"  ├ 총 글자 수: {char_count}자")
    print(f"  ├ 어휘 다양성(TTR): {ttr:.2f}")
    print(f"  ├ 자기 집중도: {self_ratio:.0%}")
    print(f"  ├ 등장 인물: {people if people else '없음'}")
    print(f"  └ 내용어: {content_words[:15]}...")


print("\n" + "=" * 60)
print("테스트 완료")
print("=" * 60)
