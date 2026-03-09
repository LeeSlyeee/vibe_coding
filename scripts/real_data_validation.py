"""
킥 #2 실제 데이터 교차 검증
=============================
서버 DB의 실제 일기 데이터를 mood_level별로 분류하고,
언어 지표가 실제로 차이나는지 통계적으로 검증한다.

검증 논리:
  mood_level 낮음(1~2) → 문장 짧고, 어휘 단조, 자기 집중 높아야
  mood_level 높음(4~5) → 문장 길고, 어휘 다양, 타인 등장해야
  상관관계 없으면 → 방법론 폐기
"""

import psycopg2
from cryptography.fernet import Fernet
from kiwipiepy import Kiwi
import re

# ─── 설정 ───
ENCRYPTION_KEY = "no-cI2OmQ0K2Eb7cNlfmndN159GET62e-YqVncAkjKg="
DB_CONFIG = {
    "dbname": "vibe_db",
    "user": "vibe_user",
    "password": "vibe1234",
    "host": "127.0.0.1",
    "port": 15432  # SSH 터널
}

fernet = Fernet(ENCRYPTION_KEY.encode())
kiwi = Kiwi()

def decrypt(text):
    if not text:
        return ""
    try:
        return fernet.decrypt(text.encode()).decode()
    except:
        return text  # 암호화 안 된 평문

def analyze_text(text):
    """단일 텍스트에 대한 언어 지문 분석"""
    if not text or len(text.strip()) < 5:
        return None
    
    tokens = kiwi.tokenize(text)
    sentences = kiwi.split_into_sents(text)
    
    # 1. 문장 길이 평균
    sent_lengths = [len(s.text.strip()) for s in sentences if s.text.strip()]
    avg_sent_len = sum(sent_lengths) / max(len(sent_lengths), 1)
    
    # 2. 총 글자 수
    char_count = len(text.replace('\n', '').replace(' ', ''))
    
    # 3. 어휘 다양성 (TTR) — 내용어만
    content_words = [t.form for t in tokens if t.tag.startswith(('NN', 'VV', 'VA', 'MAG'))]
    ttr = len(set(content_words)) / max(len(content_words), 1) if content_words else 0
    
    # 4. 1인칭 대명사 비율
    first_sg = sum(1 for t in tokens if t.tag == 'NP' and t.form in ['나', '내', '저', '제'])
    first_pl = sum(1 for t in tokens if t.tag == 'NP' and t.form in ['우리', '저희'])
    total_pronouns = first_sg + first_pl
    self_focus = first_sg / max(total_pronouns, 1) if total_pronouns > 0 else 0.5
    
    # 5. 타인 등장 (고유명사)
    people = [t.form for t in tokens if t.tag == 'NNP']
    people_count = len(set(people))
    
    # 6. 감정어 밀도 (감정 형용사/동사 비율)
    emotion_stems = ['슬프', '우울', '기쁘', '행복', '즐겁', '화나', '짜증', 
                     '불안', '걱정', '무섭', '외롭', '쓸쓸', '지치', '힘들',
                     '편안', '따뜻', '설레', '뿌듯', '감사', '신나',
                     '답답', '억울', '허무', '무기력', '괴롭', '아프',
                     '좋', '싫', '두렵', '초조']
    
    emotion_count = 0
    for t in tokens:
        if t.tag.startswith(('VA', 'VV', 'NNG')):
            if any(stem in t.form for stem in emotion_stems):
                emotion_count += 1
    
    emotion_density = emotion_count / max(len(content_words), 1)
        
    return {
        'avg_sent_len': round(avg_sent_len, 1),
        'char_count': char_count,
        'ttr': round(ttr, 3),
        'self_focus': round(self_focus, 2),
        'people_count': people_count,
        'emotion_density': round(emotion_density, 3),
        'sentence_count': len(sent_lengths),
        'content_word_count': len(content_words)
    }


# ─── DB 조회 ───
print("📡 서버 DB 연결 중...")
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# 모든 일기 조회 (mood_level이 있는 것만)
cur.execute("""
    SELECT id, mood_level, event, emotion_desc, emotion_meaning, self_talk, date
    FROM diaries
    WHERE mood_level IS NOT NULL
    ORDER BY date DESC
""")
rows = cur.fetchall()
print(f"✅ 총 {len(rows)}개 일기 로드 완료\n")

# ─── 분석 실행 ───
results_by_mood = {1: [], 2: [], 3: [], 4: [], 5: []}
failed = 0
analyzed = 0

for row in rows:
    diary_id, mood_level, event, emotion_desc, emotion_meaning, self_talk, date = row
    
    if mood_level not in [1, 2, 3, 4, 5]:
        continue
    
    # 모든 텍스트 필드 합치기 (복호화)
    parts = []
    for field in [event, emotion_desc, emotion_meaning, self_talk]:
        dec = decrypt(field)
        if dec and len(dec.strip()) > 2:
            parts.append(dec)
    
    full_text = " ".join(parts)
    
    if len(full_text.strip()) < 10:
        failed += 1
        continue
    
    result = analyze_text(full_text)
    if result:
        result['mood_level'] = mood_level
        result['diary_id'] = diary_id
        result['date'] = str(date)
        results_by_mood[mood_level].append(result)
        analyzed += 1

print(f"📊 분석 성공: {analyzed}건 / 실패(텍스트 부족): {failed}건\n")

# ─── 결과 출력 ───
print("=" * 70)
print("  mood_level별 언어 지표 평균 (실제 데이터 기반)")
print("=" * 70)
print(f"{'mood':>6} | {'건수':>5} | {'문장길이':>8} | {'글자수':>6} | {'TTR':>6} | {'자기집중':>8} | {'타인수':>6} | {'감정밀도':>8}")
print("-" * 70)

mood_averages = {}
for mood in [1, 2, 3, 4, 5]:
    data = results_by_mood[mood]
    if not data:
        print(f"  {mood:>4} | {'없음':>5} |")
        continue
    
    n = len(data)
    avg = {
        'avg_sent_len': sum(d['avg_sent_len'] for d in data) / n,
        'char_count': sum(d['char_count'] for d in data) / n,
        'ttr': sum(d['ttr'] for d in data) / n,
        'self_focus': sum(d['self_focus'] for d in data) / n,
        'people_count': sum(d['people_count'] for d in data) / n,
        'emotion_density': sum(d['emotion_density'] for d in data) / n,
    }
    mood_averages[mood] = avg
    
    print(f"  {mood:>4} | {n:>5} | {avg['avg_sent_len']:>8.1f} | {avg['char_count']:>6.0f} | {avg['ttr']:>.4f} | {avg['self_focus']:>8.2f} | {avg['people_count']:>6.1f} | {avg['emotion_density']:>8.4f}")

# ─── 상관관계 분석 ───
print("\n" + "=" * 70)
print("  상관관계 판정: mood_level과 언어 지표 간 추세")
print("=" * 70)

if len(mood_averages) >= 2:
    moods_sorted = sorted(mood_averages.keys())
    
    indicators = [
        ('avg_sent_len', '문장 길이', '길어야', 'positive'),
        ('char_count', '글자 수', '많아야', 'positive'),
        ('ttr', '어휘 다양성', '높아야', 'positive'),
        ('self_focus', '자기 집중도', '낮아야', 'negative'),
        ('people_count', '타인 등장 수', '많아야', 'positive'),
        ('emotion_density', '감정어 밀도', '변화 관찰', 'observe'),
    ]
    
    for key, label, expect, direction in indicators:
        vals = [(m, mood_averages[m][key]) for m in moods_sorted if m in mood_averages]
        if len(vals) < 2:
            continue
        
        # 단순 추세: 첫 값 vs 마지막 값
        low_mood_val = vals[0][1]   # mood 1 or lowest
        high_mood_val = vals[-1][1]  # mood 5 or highest
        
        if direction == 'positive':
            # 기분 좋을수록 높아야 정상
            trend_correct = high_mood_val > low_mood_val
            change_pct = ((high_mood_val - low_mood_val) / max(abs(low_mood_val), 0.001)) * 100
        elif direction == 'negative':
            # 기분 좋을수록 낮아야 정상
            trend_correct = high_mood_val < low_mood_val
            change_pct = ((low_mood_val - high_mood_val) / max(abs(high_mood_val), 0.001)) * 100
        else:
            trend_correct = None
            change_pct = ((high_mood_val - low_mood_val) / max(abs(low_mood_val), 0.001)) * 100
        
        icon = "✅" if trend_correct else ("📊" if trend_correct is None else "❌")
        trend_desc = f"mood↑ → {label}↑" if direction == 'positive' else (f"mood↑ → {label}↓" if direction == 'negative' else f"변화량 {change_pct:+.1f}%")
        
        vals_str = " → ".join(f"[{m}]={v:.2f}" for m, v in vals)
        print(f"\n  {icon} {label} ({expect})")
        print(f"     추세: {vals_str}")
        print(f"     변화율: {change_pct:+.1f}% | 판정: {trend_desc}")

else:
    print("  데이터가 2개 mood_level 이상 필요합니다.")

# ─── 개별 일기 샘플 출력 ───
print("\n" + "=" * 70)
print("  실제 일기 샘플 (mood_level 극단값)")
print("=" * 70)

for mood in [1, 2, 4, 5]:
    data = results_by_mood[mood]
    if data:
        sample = data[0]
        # 일기 내용 일부 표시 (개인정보 보호 위해 앞 30자만)
        cur.execute("SELECT event FROM diaries WHERE id = %s", (sample['diary_id'],))
        enc_text = cur.fetchone()
        if enc_text and enc_text[0]:
            dec = decrypt(enc_text[0])
            preview = dec[:50] + "..." if len(dec) > 50 else dec
        else:
            preview = "(내용 없음)"
        
        print(f"\n  [mood={mood}] ID={sample['diary_id']} ({sample['date']})")
        print(f"    텍스트: \"{preview}\"")
        print(f"    문장길이={sample['avg_sent_len']} | TTR={sample['ttr']} | 자기집중={sample['self_focus']} | 타인={sample['people_count']}")

cur.close()
conn.close()
print("\n\n✅ 검증 완료")
