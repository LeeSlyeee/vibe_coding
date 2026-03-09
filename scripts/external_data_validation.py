"""
킥 #2 외부 공개 데이터 교차 검증
==================================
네이버 쇼핑 리뷰 (1~5점 평점 + 한국어 텍스트 20만건)를 사용하여,
Kiwi 형태소 분석기의 언어 지표가 감정/만족도 점수와 실제로 상관관계가 있는지 검증.

검증 논리:
  - 평점 1~2 (부정) vs 평점 4~5 (긍정) 그룹의 언어 지표 비교
  - LIWC 이론대로라면: 
    부정 그룹 → 문장 짧고, 어휘 단조, 자기 집중 높음
    긍정 그룹 → 문장 길고, 어휘 다양
  
데이터 출처: https://github.com/bab2min/corpus (공개)
조작 여지: 없음. 외부 공개 데이터를 그대로 가져와 분석.
"""

import requests
from kiwipiepy import Kiwi
import random
import time

kiwi = Kiwi()

# ─── 1. 외부 데이터 다운로드 ───
print("📡 외부 공개 데이터 다운로드 중 (bab2min/corpus)...")
url = "https://raw.githubusercontent.com/bab2min/corpus/master/sentiment/naver_shopping.txt"
r = requests.get(url, timeout=30)
lines = r.text.strip().split('\n')
print(f"✅ 총 {len(lines)}건 로드 완료")

# 파싱: "평점\t리뷰텍스트" 형식
data = []
for line in lines:
    parts = line.split('\t', 1)
    if len(parts) == 2:
        try:
            score = int(parts[0].strip())
            text = parts[1].strip()
            if score in [1, 2, 3, 4, 5] and len(text) >= 10:
                data.append({'score': score, 'text': text})
        except:
            pass

print(f"✅ 유효 데이터: {len(data)}건")

# 분포 확인
from collections import Counter
score_dist = Counter(d['score'] for d in data)
print(f"\n📊 평점 분포:")
for s in [1, 2, 3, 4, 5]:
    print(f"   ★{s}: {score_dist.get(s, 0):>6}건")

# ─── 2. 샘플링 (공정한 비교를 위해 각 그룹 동일 수) ───
SAMPLE_PER_GROUP = 500  # 각 그룹 500건

negative = [d for d in data if d['score'] in [1, 2]]
positive = [d for d in data if d['score'] in [4, 5]]

random.seed(42)  # 재현 가능한 시드 고정
neg_sample = random.sample(negative, min(SAMPLE_PER_GROUP, len(negative)))
pos_sample = random.sample(positive, min(SAMPLE_PER_GROUP, len(positive)))

print(f"\n🎲 샘플링 (시드=42, 조작 불가):")
print(f"   부정 (★1~2): {len(neg_sample)}건")
print(f"   긍정 (★4~5): {len(pos_sample)}건")

# ─── 3. Kiwi 분석 ───
def analyze_text(text):
    try:
        tokens = kiwi.tokenize(text)
        sentences = kiwi.split_into_sents(text)
    except:
        return None
    
    # 문장 길이
    sent_lengths = [len(s.text.strip()) for s in sentences if s.text.strip()]
    avg_sent_len = sum(sent_lengths) / max(len(sent_lengths), 1)
    
    # 글자 수
    char_count = len(text.replace(' ', ''))
    
    # 어휘 다양성 (내용어 TTR)
    content_words = [t.form for t in tokens if t.tag.startswith(('NN', 'VV', 'VA', 'MAG'))]
    ttr = len(set(content_words)) / max(len(content_words), 1) if content_words else 0
    
    # 1인칭 대명사 비율
    first_sg = sum(1 for t in tokens if t.tag == 'NP' and t.form in ['나', '내', '저', '제'])
    first_pl = sum(1 for t in tokens if t.tag == 'NP' and t.form in ['우리', '저희'])
    total_pn = first_sg + first_pl
    self_focus = first_sg / max(total_pn, 1) if total_pn > 0 else 0.5
    
    # 부정어 비율 (않, 못, 안, 없)
    negation_words = sum(1 for t in tokens if t.form in ['않', '못', '안', '없', '말'] and t.tag.startswith(('VX', 'MAG', 'VA')))
    negation_ratio = negation_words / max(len(tokens), 1)
    
    # 감탄/이모티콘 사용
    exclamation = text.count('!') + text.count('ㅋ') + text.count('ㅎ') + text.count('ㅠ') + text.count('ㅜ')
    
    return {
        'avg_sent_len': avg_sent_len,
        'char_count': char_count,
        'ttr': ttr,
        'self_focus': self_focus,
        'negation_ratio': negation_ratio,
        'exclamation': exclamation,
        'word_count': len(content_words),
        'sentence_count': len(sent_lengths),
    }

print(f"\n🔬 Kiwi 분석 실행 중...")
start_time = time.time()

neg_results = []
pos_results = []

for d in neg_sample:
    r = analyze_text(d['text'])
    if r:
        r['text'] = d['text']
        neg_results.append(r)

for d in pos_sample:
    r = analyze_text(d['text'])
    if r:
        r['text'] = d['text']
        pos_results.append(r)

elapsed = time.time() - start_time
total_analyzed = len(neg_results) + len(pos_results)
print(f"✅ 분석 완료: {total_analyzed}건 / {elapsed:.1f}초 (초당 {total_analyzed/max(elapsed,0.1):.0f}건)")

# ─── 4. 결과 비교 ───
def avg(lst, key):
    vals = [d[key] for d in lst]
    return sum(vals) / max(len(vals), 1)

print("\n" + "=" * 85)
print("  외부 공개 데이터 기반 언어 지표 비교 — 네이버 쇼핑 리뷰 1000건")
print("  데이터 출처: github.com/bab2min/corpus (제3자 공개 데이터)")
print("=" * 85)

print(f"\n{'지표':<18} | {'부정(★1~2)':>12} | {'긍정(★4~5)':>12} | {'차이':>8} | {'LIWC 이론 예측':<18} | {'일치':>4}")
print("-" * 90)

indicators = [
    ('avg_sent_len',  '문장 길이',     '긍정이 더 길다',   'positive_higher'),
    ('char_count',    '글자 수',       '긍정이 더 많다',   'positive_higher'),
    ('ttr',           '어휘 다양성',   '긍정이 더 높다',   'positive_higher'),
    ('self_focus',    '자기 집중도',   '부정이 더 높다',   'negative_higher'),
    ('negation_ratio','부정어 비율',   '부정이 더 높다',   'negative_higher'),
    ('word_count',    '단어 수',       '긍정이 더 많다',   'positive_higher'),
]

matches = 0
total_ind = 0

for key, label, theory, direction in indicators:
    neg_val = avg(neg_results, key)
    pos_val = avg(pos_results, key)
    
    diff_pct = ((pos_val - neg_val) / max(abs(neg_val), 0.001)) * 100
    
    if direction == 'positive_higher':
        correct = pos_val > neg_val
    else:
        correct = neg_val > pos_val
    
    icon = "✅" if correct else "❌"
    if correct:
        matches += 1
    total_ind += 1
    
    print(f"  {label:<16} | {neg_val:>12.4f} | {pos_val:>12.4f} | {diff_pct:>+7.1f}% | {theory:<18} | {icon}")

print(f"\n{'='*85}")
accuracy = matches / max(total_ind, 1) * 100
if accuracy >= 80:
    verdict = "✅ 학술 이론과 높은 일치 — 방법론 유효"
elif accuracy >= 60:
    verdict = "🟡 부분 일치 — 보완 필요"
else:
    verdict = "❌ 일치율 낮음 — 방법론 재검토 필요"

print(f"  이론 일치율: {matches}/{total_ind} ({accuracy:.0f}%) → {verdict}")
print(f"{'='*85}")

# ─── 5. 샘플 출력 ───
print(f"\n📝 부정 리뷰 샘플 (★1~2):")
for d in neg_results[:3]:
    print(f"   \"{d['text'][:70]}...\"")
    print(f"     문장길이={d['avg_sent_len']:.1f} | TTR={d['ttr']:.3f} | 자기집중={d['self_focus']:.2f} | 부정어={d['negation_ratio']:.3f}")

print(f"\n📝 긍정 리뷰 샘플 (★4~5):")
for d in pos_results[:3]:
    print(f"   \"{d['text'][:70]}...\"")
    print(f"     문장길이={d['avg_sent_len']:.1f} | TTR={d['ttr']:.3f} | 자기집중={d['self_focus']:.2f} | 부정어={d['negation_ratio']:.3f}")

# ─── 6. 추가: 868개 학술 감정어 사전과의 교차 검증 ───
print(f"\n" + "=" * 85)
print("  보너스: 학술 감정어 사전 (868개) 활용 가능성")
print("=" * 85)

from datasets import load_dataset
emotion_lexicon = load_dataset('jonghwanhyeon/korean-emotion-lexicon', split='train')
positive_emotions = [e['lexicon'] for e in emotion_lexicon if e['valence'] >= 2.5]
negative_emotions = [e['lexicon'] for e in emotion_lexicon if e['valence'] <= 1.5]
print(f"  학술 감정어 사전: 총 {len(emotion_lexicon)}개")
print(f"    긍정 감정어 (valence ≥ 2.5): {len(positive_emotions)}개 — 예: {positive_emotions[:5]}")
print(f"    부정 감정어 (valence ≤ 1.5): {len(negative_emotions)}개 — 예: {negative_emotions[:5]}")
print(f"\n  → 이 {len(emotion_lexicon)}개 감정어를 Kiwi + 어근 매칭에 사용하면")
print(f"    '100개 하드코딩'이 아닌 '학술적으로 검증된 감정어 사전' 기반 분석이 됩니다.")

print("\n✅ 외부 데이터 교차 검증 완료")
