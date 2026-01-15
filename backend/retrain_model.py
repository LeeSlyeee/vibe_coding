#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mood Diary AI - Model Retraining Script

이 스크립트는 데이터베이스에 쌓인 사용자 일기 데이터를 사용하여
감정 분석 LSTM 모델을 재훈련합니다.

실행 방법:
    cd backend
    source venv/bin/activate
    python retrain_model.py

기능:
    1. DB에서 모든 일기 데이터 로드 (event + emotion_desc + self_talk)
    2. 기존 감성대화말뭉치와 결합
    3. LSTM 모델 재훈련
    4. 모델 저장 (emotion_model.h5, tokenizer.pickle)
"""

import os
import sys
import numpy as np

# Flask app context를 위한 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Diary
from ai_analysis import EmotionAnalysis

def main():
    print("=" * 60)
    print("🔄 Mood Diary AI - 모델 재훈련 시작")
    print("=" * 60)
    
    with app.app_context():
        # 1. DB에서 일기 데이터 확인
        total_diaries = db.session.query(Diary).count()
        print(f"\n📊 데이터베이스 상태:")
        print(f"   - 총 일기 개수: {total_diaries}개")
        
        if total_diaries < 10:
            print("\n⚠️  경고: 일기 데이터가 너무 적습니다 (10개 미만).")
            print("   모델 재훈련을 위해서는 최소 100개 이상의 일기를 권장합니다.")
            
            response = input("\n계속 진행하시겠습니까? (y/N): ")
            if response.lower() != 'y':
                print("재훈련이 취소되었습니다.")
                return
        
        # 2. AI 분석기 초기화 (기존 모델 로드)
        print("\n🤖 AI 분석기 초기화 중...")
        # Prevent auto-training in __init__ since we are doing manual retraining
        os.environ['SKIP_TRAINING'] = '1'
        ai = EmotionAnalysis()
        del os.environ['SKIP_TRAINING'] # Clean up
        
        # 3. 기존 모델 백업
        import shutil
        from datetime import datetime
        
        backup_dir = os.path.join(os.path.dirname(__file__), 'model_backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        model_path = ai.model_path
        tokenizer_path = ai.tokenizer_path
        
        if os.path.exists(model_path):
            backup_model = os.path.join(backup_dir, f'emotion_model_{timestamp}.h5')
            shutil.copy2(model_path, backup_model)
            print(f"✅ 기존 모델 백업: {backup_model}")
        
        if os.path.exists(tokenizer_path):
            backup_tokenizer = os.path.join(backup_dir, f'tokenizer_{timestamp}.pickle')
            shutil.copy2(tokenizer_path, backup_tokenizer)
            print(f"✅ 기존 토크나이저 백업: {backup_tokenizer}")
        
        # 4. DB 데이터 로드
        print(f"\n📚 데이터베이스에서 일기 로드 중...")
        db_texts, db_labels = ai.load_db_data()
        
        if not db_texts:
            print("❌ DB에서 데이터를 불러오는데 실패했습니다.")
            return
        
        print(f"✅ {len(db_texts)}개의 일기 데이터 로드 완료")
        
        # 5. 감성대화말뭉치 로드
        print("\n📚 감성대화말뭉치 로드 중...")
        # Reset internal buffers to ensure clean load (in case they were used)
        ai.train_texts = []
        ai.train_labels = np.array([])
        
        ai.load_sentiment_corpus()
        
        corpus_texts = ai.train_texts
        # Convert numpy array to list for concatenation
        corpus_labels = ai.train_labels.tolist() if hasattr(ai.train_labels, 'tolist') else list(ai.train_labels)
        
        if corpus_texts:
            print(f"✅ {len(corpus_texts)}개의 코퍼스 데이터 로드 완료")
        else:
            print("⚠️  감성대화말뭉치를 찾을 수 없습니다. DB 데이터만으로 훈련합니다.")
        
        # 6. 데이터 결합
        all_texts = corpus_texts + db_texts
        all_labels = corpus_labels + db_labels
        
        print(f"\n📊 최종 훈련 데이터:")
        print(f"   - 코퍼스: {len(corpus_texts)}개")
        print(f"   - 사용자 일기: {len(db_texts)}개")
        print(f"   - 총합: {len(all_texts)}개")
        
        # 7. 모델 재훈련
        print("\n🔥 모델 재훈련 시작...")
        print("   (이 과정은 5-10분 정도 소요될 수 있습니다)")
        print("-" * 60)
        
        try:
            # 기존 _train_initial_model을 직접 호출하되, 데이터를 전달
            ai._train_with_data(all_texts, all_labels)
            
            print("-" * 60)
            print("✅ 모델 재훈련 완료!")
            print(f"   - 모델 파일: {model_path}")
            print(f"   - 토크나이저: {tokenizer_path}")
            
            # Update state for app.py to prevent redundant auto-training
            try:
                current_kw = ai._get_keyword_count()
                ai._save_training_state(current_kw)
                print(f"✅ Training state updated (Count: {current_kw})")
            except Exception as e:
                print(f"⚠️ Warning: perform state update failed: {e}")
            
        except Exception as e:
            print(f"\n❌ 재훈련 중 오류 발생: {e}")
            print("기존 백업 파일을 복원하시려면 model_backups 폴더를 확인하세요.")
            return
        
        # 8. 모델 검증
        print("\n🧪 모델 검증 중...")
        test_texts = [
            "오늘 시험에 떨어져서 너무 슬프다",
            "친구들과 놀러가서 정말 행복했어",
            "아무것도 하기 싫고 무기력해"
        ]
        
        for text in test_texts:
            result = ai.predict(text)
            print(f"   입력: {text}")
            print(f"   → 예측: {result}\n")
        
        print("=" * 60)
        print("🎉 재훈련 프로세스가 성공적으로 완료되었습니다!")
        print("=" * 60)
        print("\n💡 Tip: 서버를 재시작하면 새 모델이 적용됩니다.")
        print("   $ pkill -f app.py && python app.py")


if __name__ == "__main__":
    main()
