import os
import sys
import django
from pymongo import MongoClient
from datetime import datetime
from django.utils.timezone import make_aware
from cryptography.fernet import Fernet

# Django 환경 설정
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from maum_on.models import MaumOn

User = get_user_model()

# 암호화 키 (OCI 서버와 동일)
ENCRYPTION_KEY = b'no-cI2OmQ0K2Eb7cNlfmndN159GET62e-YqVncAkjKg='
cipher = Fernet(ENCRYPTION_KEY)

def decrypt_text(encrypted_text):
    if not encrypted_text or not isinstance(encrypted_text, str):
        return ""
    if not encrypted_text.startswith('gAAAA'):
        return encrypted_text
    try:
        return cipher.decrypt(encrypted_text.encode()).decode()
    except Exception as e:
        return encrypted_text 

def migrate_data():
    print("🚀 Connecting to Remote MongoDB via SSH Tunnel (localhost:27018)...")
    
    try:
        # 1. 기존 데이터 초기화 (완전 재구성을 위해)
        # 이미 마이그레이션 된 데이터 중 analysis가 암호화된 상태인 것들을 갱신하기 위해
        # 간단하게 전체 삭제 후 재수행 (개발 환경이므로 가능)
        print("🧹 Clearing existing MaumOn data for clean migration...")
        deleted_count, _ = MaumOn.objects.all().delete() 
        print(f"   - Deleted {deleted_count} entries.")

        # 2. MongoDB 연결
        client = MongoClient('mongodb://localhost:27018/')
        db = client['mood_diary_db']
        collection = db['diaries']
        
        migrated_count = 0
        skipped_count = 0
        
        cursor = collection.find({})
        print("🔄 Starting Content & Analysis Decryption & Migration...")
        
        for doc in cursor:
            try:
                # A. 본문 복호화 및 통합
                event = decrypt_text(doc.get('event'))
                emotion_desc = decrypt_text(doc.get('emotion_desc'))
                self_talk = decrypt_text(doc.get('self_talk'))
                sleep_condition = decrypt_text(doc.get('sleep_condition'))
                
                content_parts = []
                if event: content_parts.append(f"[오늘 있었던 일]\n{event}")
                if emotion_desc: content_parts.append(f"[느낀 감정]\n{emotion_desc}")
                if self_talk: content_parts.append(f"[나에게 한마디]\n{self_talk}")
                if sleep_condition: content_parts.append(f"[수면 상태]\n{sleep_condition}")
                
                final_content = "\n\n".join(content_parts)
                if not final_content:
                    final_content = "내용 없음 (복호화 실패 또는 데이터 누락)"

                # B. AI 분석 결과 복호화
                ai_prediction = decrypt_text(doc.get('ai_prediction'))
                ai_comment = decrypt_text(doc.get('ai_comment'))
                
                analysis_data = {
                    'comment': ai_comment,
                    'prediction': ai_prediction,
                    'migrated': True
                }

                # C. 메타데이터 처리
                email = doc.get('user_id')
                mood_score = doc.get('mood_level') or doc.get('mood_score', 5)
                
                created_at_raw = doc.get('created_at') or doc.get('date')
                if isinstance(created_at_raw, str):
                    created_at = make_aware(datetime.strptime(created_at_raw, '%Y-%m-%d %H:%M:%S'))
                elif isinstance(created_at_raw, datetime):
                    created_at = make_aware(created_at_raw)
                else:
                    created_at = make_aware(datetime.now())

                # D. User 매핑
                username = email.split('@')[0] if '@' in email else email
                user, _ = User.objects.get_or_create(username=username, defaults={'email': email})

                # 저장
                is_high_risk = int(mood_score) <= 2
                
                MaumOn.objects.create(
                    user=user,
                    content=final_content,
                    mood_score=mood_score,
                    is_high_risk=is_high_risk,
                    created_at=created_at,
                    analysis_result=analysis_data
                )
                migrated_count += 1
                    
            except Exception as e:
                continue

        print(f"\n🎉 Migration Completed!")
        print(f"- Processed & Saved: {migrated_count}")

    except Exception as e:
        print(f"🔥 Critical Error: {e}")

if __name__ == "__main__":
    migrate_data()
