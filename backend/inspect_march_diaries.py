#!/usr/bin/env python3
"""3/18, 3/22 일기 AI 분석 상태 직접 확인"""
import os
import sys
sys.path.insert(0, '/home/ubuntu/vibe_coding/backend')

from dotenv import load_dotenv
load_dotenv('/home/ubuntu/vibe_coding/backend/.env')

import psycopg2
from crypto_utils import EncryptionManager

crypto = EncryptionManager(os.environ.get('ENCRYPTION_KEY'))

def safe_decrypt(val):
    if not val:
        return None
    try:
        return crypto.decrypt(val)
    except:
        return f"[복호화실패] {str(val)[:30]}..."

db_url = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute("""
    SELECT d.id, d.date, d.event, d.emotion_desc, d.self_talk,
           d.ai_comment, d.ai_emotion, d.mood_intensity, d.mood_level, d.created_at
    FROM diaries d
    JOIN users u ON d.user_id = u.id
    WHERE u.username = 'slyeee'
      AND d.date IN ('2026-03-18', '2026-03-22')
    ORDER BY d.date
""")

rows = cur.fetchall()
print(f"✅ 총 {len(rows)}개 일기 발견\n")

for row in rows:
    diary_id, date, event_enc, emotion_enc, self_talk_enc, ai_comment_enc, ai_emotion_enc, mood_score, mood_level, created_at = row

    event      = safe_decrypt(event_enc)
    emotion    = safe_decrypt(emotion_enc)
    self_talk  = safe_decrypt(self_talk_enc)
    ai_comment = safe_decrypt(ai_comment_enc)
    ai_emotion = safe_decrypt(ai_emotion_enc)

    print(f"=" * 60)
    print(f"📅 날짜: {date}  (ID: {diary_id})")
    print(f"🌡️  기분레벨: {mood_level},  AI점수: {mood_score}")
    print(f"📝 사건: {event}")
    print(f"💭 감정설명: {emotion}")
    print(f"💬 스스로에게: {self_talk}")
    print(f"🤖 AI 감정: {ai_emotion}")
    print(f"🤖 AI 코멘트: {ai_comment}")
    print()

cur.close()
conn.close()
