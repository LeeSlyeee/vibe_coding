
import os
import pymongo
from app import app, mongo, crypto_manager

def cleanup_today_duplicates():
    with app.app_context():
        target_date = "2026-02-11"
        user_id = "slyeee"
        
        # 가짜 데이터 패턴 (DataSeeder에서 옴)
        fake_patterns = [
            "직장에서 큰 실수를 했다.",
            "친구와 말다툼을 했다.",
            "평범한 하루였다.",
            "오랜만에 산책을 다녀왔다.",
            "프로젝트가 성공적으로 끝났다!"
        ]
        
        print(f"🧹 Cleaning up duplicates for {user_id} on {target_date}...")
        
        # 1. 해당 날짜 일기 모두 조회
        diaries = list(mongo.db.diaries.find({"user_id": user_id, "date": target_date}))
        print(f"found {len(diaries)} diaries for today.")
        
        deleted_count = 0
        real_diary_id = None
        
        for diary in diaries:
            try:
                # Decrypt content
                content_enc = diary.get('content')
                if not content_enc: continue
                
                content = crypto_manager.decrypt(content_enc)
                print(f"[{diary.get('_id')}] Content: {content[:30]}...")
                
                is_fake = False
                for pattern in fake_patterns:
                    if pattern in content:
                        is_fake = True
                        break
                
                if is_fake:
                    print(f"   >>> Deleting FAKE diary: {diary.get('_id')}")
                    mongo.db.diaries.delete_one({"_id": diary.get('_id')})
                    
                    # [Tombstone] 앱 동기화 시 삭제 반영을 위해 Tombstone에 추가
                    mongo.db.deleted_diaries.insert_one({
                        "diary_id": str(diary.get('_id')),
                        "user_id": user_id,
                        "deleted_at": diary.get('created_at') # or now
                    })
                    deleted_count += 1
                else:
                    print(f"   >>> Keeping REAL diary: {diary.get('_id')}")
                    real_diary_id = diary.get('_id')
                    
            except Exception as e:
                print(f"Error processing diary {diary.get('_id')}: {e}")

        print(f"✨ Cleanup Complete. Deleted {deleted_count} fake entries.")
        if real_diary_id:
            print(f"✅ Real diary preserved: {real_diary_id}")

if __name__ == "__main__":
    cleanup_today_duplicates()
