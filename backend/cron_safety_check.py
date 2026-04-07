"""
마음온 안전 확인 (생존 신고) Cron 스크립트
==========================================
매일 오후 9시 KST에 실행하여 3일 이상 일기를 쓰지 않은 사용자에게
안부 확인 푸시 알림을 발송합니다.

[배경]
1인가구 사용자가 일기를 3일 이상 미작성할 경우,
건강 이상이나 위급 상황 가능성을 고려하여 안부를 확인합니다.

[단계별 에스컬레이션]
- 3일 미작성: 따뜻한 안부 확인 푸시 (본인)
- 5일 미작성: 걱정 표현 + 확인 요청 푸시 (본인)
- 7일 미작성: 보호자/연결된 사람에게도 알림 발송

crontab 예시:
  0 12 * * * cd /home/ubuntu/project/backend && /home/ubuntu/project/backend/venv/bin/python cron_safety_check.py >> /home/ubuntu/cron_safety_check.log 2>&1
  (21:00 KST = 12:00 UTC, 매일)
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# 백엔드 루트 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [SafetyCheck] %(message)s'
)
logger = logging.getLogger(__name__)

# 에스컬레이션 단계별 메시지
SAFETY_MESSAGES = {
    3: {
        "title": "✍️ 3일째 마음 기록이 없어요",
        "body": "요즘 바쁘셨나요? 괜찮으시다면 오늘 한 줄이라도 남겨보세요 😊",
        "level": "gentle",
    },
    5: {
        "title": "🙏 괜찮으신가요?",
        "body": "5일째 기록이 없어 걱정이 돼요. 간단히 '괜찮아요'라고만 남겨주셔도 좋아요.",
        "level": "concern",
    },
    7: {
        "title": "💛 마음온이 걱정하고 있어요",
        "body": "일주일째 소식이 없어요. 혹시 도움이 필요하시면 언제든 연락주세요. 당신의 안전이 가장 중요해요.",
        "level": "escalation",
    },
}

# 이 일수 이상이면 더 이상 알림 보내지 않음 (앱 자체를 안 쓰는 사용자일 수 있음)
MAX_INACTIVE_DAYS = 14

# 최소 일기 수: 이 이하면 아직 활성 사용자가 아님 (신규 설치 후 방치)
MIN_DIARY_COUNT = 2


def run_safety_check():
    """3일 이상 미작성 사용자에게 안전 확인 푸시를 발송합니다."""
    from app import app
    from models import db, User, Diary
    from push_service import send_push, is_push_available

    if not is_push_available():
        logger.warning("⚠️ 푸시 서비스 비활성화 상태 → 안전 확인 중단")
        return

    with app.app_context():
        now_utc = datetime.utcnow()
        users = db.session.query(User).all()

        sent_count = 0
        skip_count = 0

        for user in users:
            try:
                # 1. FCM 토큰 없으면 푸시 불가 → 건너뜀
                if not user.fcm_token:
                    continue

                # 2. 사용자의 일기 이력 확인
                diary_count = db.session.query(Diary).filter_by(user_id=user.id).count()
                if diary_count < MIN_DIARY_COUNT:
                    continue  # 활성 사용자가 아님

                # 3. 가장 최근 일기 날짜 조회
                latest_diary = db.session.query(Diary).filter_by(
                    user_id=user.id
                ).order_by(Diary.date.desc()).first()

                if not latest_diary or not latest_diary.date:
                    continue

                # 날짜 파싱 (date 필드는 'YYYY-MM-DD' 문자열)
                try:
                    last_date = datetime.strptime(latest_diary.date, "%Y-%m-%d")
                except (ValueError, TypeError):
                    continue

                # 4. 미작성 일수 계산 (KST 기준)
                kst_now = now_utc + timedelta(hours=9)
                kst_today = kst_now.replace(hour=0, minute=0, second=0, microsecond=0)
                inactive_days = (kst_today - last_date).days

                # 활성 범위 밖이면 건너뜀 (너무 오래된 → 앱 미사용자)
                if inactive_days > MAX_INACTIVE_DAYS or inactive_days < 3:
                    continue

                # 5. 에스컬레이션 단계 결정
                message = None
                if inactive_days >= 7:
                    message = SAFETY_MESSAGES[7]
                elif inactive_days >= 5:
                    message = SAFETY_MESSAGES[5]
                elif inactive_days >= 3:
                    message = SAFETY_MESSAGES[3]

                if not message:
                    continue

                # 6. 중복 발송 방지: 같은 단계 알림은 하루에 한 번만
                #    (단순 구현: 매일 1회 실행이므로 자연스럽게 중복 방지)

                # 7. 본인에게 푸시 발송
                logger.info(
                    "🔔 user=%s (%s): %d일 미작성 → [%s] 단계 푸시 발송",
                    user.id, user.username, inactive_days, message["level"]
                )

                send_push(
                    fcm_token=user.fcm_token,
                    title=message["title"],
                    body=message["body"],
                    data={
                        "type": "safety_check",
                        "inactive_days": str(inactive_days),
                        "level": message["level"],
                    },
                    apns_token=getattr(user, 'apns_token', None),
                )
                sent_count += 1

                # 8. 7일 이상이면 보호자에게도 알림
                if inactive_days >= 7:
                    _notify_guardians_inactive(user, inactive_days, db)

            except Exception as e:
                logger.error("❌ user=%s 처리 중 오류: %s", user.id, e)

        logger.info("📊 안전 확인 완료: 발송=%d, 건너뜀=%d", sent_count, skip_count)


def _notify_guardians_inactive(user, inactive_days, db):
    """7일 이상 미작성 시 보호자(ShareRelationship)에게 알림"""
    try:
        from models import User, ShareRelationship
        from push_service import send_push

        relationships = ShareRelationship.query.filter_by(
            sharer_id=user.id
        ).all()

        if not relationships:
            return

        user_name = user.nickname or user.real_name or user.username or "사용자"

        for rel in relationships:
            # 위기 알림 또는 기분 알림 허용된 보호자에게만
            if not (getattr(rel, 'share_crisis', False) or getattr(rel, 'share_mood', False)):
                continue

            viewer = User.query.get(rel.viewer_id)
            if viewer and viewer.fcm_token:
                send_push(
                    fcm_token=viewer.fcm_token,
                    title="⚠️ {}님 {}일째 기록 없음".format(user_name, inactive_days),
                    body="{}님이 {}일간 일기를 작성하지 않았습니다. 안부를 확인해 주세요.".format(
                        user_name, inactive_days
                    ),
                    data={
                        "type": "guardian_safety_alert",
                        "sharer_id": str(user.id),
                        "inactive_days": str(inactive_days),
                    },
                    apns_token=getattr(viewer, 'apns_token', None),
                )
                logger.info(
                    "  📮 보호자 알림: %s → %s (%d일 미작성)",
                    user_name, viewer.username, inactive_days
                )

    except Exception as e:
        logger.error("❌ 보호자 알림 발송 실패: %s", e)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🛡️ 마음온 안전 확인 (Safety Check) 배치 시작")
    logger.info("   실행 시각: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 60)

    run_safety_check()

    logger.info("=" * 60)
    logger.info("🛡️ 안전 확인 배치 종료")
    logger.info("=" * 60)
