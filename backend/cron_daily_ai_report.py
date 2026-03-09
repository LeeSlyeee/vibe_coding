import os
import sys
import json
import logging
from datetime import datetime, timedelta
import pytz

# 백엔드 루트 디렉토리를 path에 추가하여 모듈 임포트가 가능하게 함
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, ShareRelationship, Diary
from push_service import _firebase_initialized, send_push
from crypto_utils import crypto_manager

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def send_daily_6pm_reports():
    logger.info("🚀 [Cron] 오후 6시 일일 마음 리포트 발송 시작")
    
    if not _firebase_initialized:
        logger.warning("⚠️ [Cron] Firebase Admin SDK가 초기화되지 않았습니다. 푸시를 발송할 수 없습니다.")
        return
        
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    today_start_kst = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # DB는 UTC로 저장될 확률이 높으므로 UTC로 변환 (필요시)
    today_start_utc = today_start_kst.astimezone(pytz.utc).replace(tzinfo=None)

    with app.app_context():
        # 리포트 공유가 허용된 보호자 관계 조회
        relationships = ShareRelationship.query.filter_by(share_report=True).all()
        if not relationships:
            logger.info("ℹ️ [Cron] 리포트 공유가 설정된 보호자 관계가 없습니다.")
            return

        # 내담자(sharer) 단위로 그룹화
        sharer_map = {}
        for rel in relationships:
            if rel.sharer_id not in sharer_map:
                sharer_map[rel.sharer_id] = []
            sharer_map[rel.sharer_id].append(rel.viewer_id)
            
        for sharer_id, viewer_ids in sharer_map.items():
            sharer = User.query.get(sharer_id)
            if not sharer: 
                continue
                
            # 해당 내담자의 오늘자 일기 조회
            # SQLite 또는 Postgres에 따라 UTC vs KST 기준이 다를 수 있어 넉넉하게 오늘 0시(UTC) 이후로 검색
            diary = Diary.query.filter(
                Diary.user_id == sharer_id,
                Diary.created_at >= today_start_utc
            ).order_by(Diary.created_at.desc()).first()
            
            if not diary or not diary.ai_comment:
                logger.info(f"⏭️ [Cron] 내담자 {sharer_id}님의 오늘 일기 또는 분석 결과가 없어 발송 생략.")
                continue

            raw_comment = diary.ai_comment
            
            # 복호화 시도
            try:
                if raw_comment.startswith('gAAAA') and crypto_manager:
                    raw_comment = crypto_manager.decrypt(raw_comment)
            except Exception as e:
                logger.error(f"❌ [Cron] 복호화 에러 (ID: {diary.id}): {e}")
                continue

            if "오류가 발생" in raw_comment:
                logger.info(f"⏭️ [Cron] 내담자 {sharer_id}님의 분석 결과가 오류 상태입니다. 발송 생략.")
                continue
            
            # JSON에서 텍스트만 깔끔하게 추출 (휴지심 제거 로직 포함)
            clean_comment = raw_comment
            json_start = raw_comment.find('{')
            json_end = raw_comment.rfind('}')
            
            if json_start >= 0 and json_end > json_start:
                try:
                    json_str = raw_comment[json_start:json_end+1]
                    parsed = json.loads(json_str)
                    if isinstance(parsed, dict):
                        clean_comment = parsed.get('comment') or parsed.get('ai_comment') or parsed.get('analysis') or parsed.get('message') or clean_comment
                except Exception:
                    pass

            sharer_name = sharer.nickname or sharer.username or "사용자"
            
            # 각 보호자에게 발송
            for v_id in viewer_ids:
                viewer = User.query.get(v_id)
                if viewer and getattr(viewer, 'fcm_token', None):
                    send_push(
                        fcm_token=viewer.fcm_token,
                        title=f"🌅 {sharer_name}님의 오늘 마음 정산",
                        body=f"{clean_comment}",
                        data={
                            "type": "ai_report_alert",
                            "sharer_id": str(sharer_id)
                        },
                        apns_token=getattr(viewer, 'apns_token', None)
                    )
            logger.info(f"✅ [Cron] 내담자 {sharer_id}({sharer_name})님의 일일 리포트 -> 보호자 {len(viewer_ids)}명에게 발송 완료")

    logger.info("🎉 [Cron] 일일 마음 리포트 발송 작업 종료")

if __name__ == "__main__":
    send_daily_6pm_reports()
