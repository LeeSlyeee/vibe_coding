"""
마음온 AI 주간 편지 Cron 스크립트
==================================
매주 일요일 밤 (22:00 KST)에 실행하여 모든 사용자에 대한 주간 편지를 생성합니다.

crontab 예시:
  0 13 * * 0 cd /home/ubuntu/project/backend && source venv/bin/activate && python cron_weekly_letter.py >> /home/ubuntu/cron_weekly_letter.log 2>&1
  (22:00 KST = 13:00 UTC, 매주 일요일)

수동 실행:
  cd /home/ubuntu/project/backend && source venv/bin/activate && python cron_weekly_letter.py
"""

import os
import sys
import logging
from datetime import datetime

# 백엔드 루트 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kick_analysis.weekly_letter import process_all_users_weekly_letter

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [WeeklyLetter] %(message)s'
)
logger = logging.getLogger(__name__)


def run_weekly_letter_batch():
    """모든 사용자에 대해 주간 편지를 배치 생성합니다."""
    logger.info("=" * 60)
    logger.info("💌 마음온 AI 주간 편지 배치 생성 시작")
    logger.info(f"   실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    try:
        results = process_all_users_weekly_letter()
        
        success_count = results.get("success", 0)
        failed_count = results.get("failed", 0)
        errors = results.get("errors", [])

        logger.info(f"📊 배치 완료: 성공={success_count}, 실패={failed_count}")
        
        if errors:
            for err in errors:
                logger.error(f"   ❌ user_id={err['user_id']}: {err['error']}")
        
        if success_count > 0:
            logger.info(f"✅ {success_count}명의 주간 편지가 성공적으로 생성되었습니다.")
        elif failed_count == 0 and success_count == 0:
            logger.info("ℹ️ 이번 주 일기를 작성한 사용자가 없거나, 이미 편지가 생성되어 있습니다.")

    except Exception as e:
        logger.error(f"💥 주간 편지 배치 처리 중 치명적 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    logger.info("=" * 60)
    logger.info("💌 주간 편지 배치 처리 종료")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_weekly_letter_batch()
