"""
보호자 푸시 알림 발송 서비스
Firebase Admin SDK를 통해 FCM 푸시 알림 전송

[구조]
- Flask 백엔드에서 import하여 사용
- Firebase 서비스 계정 키가 없으면 자동으로 비활성화 (서버 중단 없음)
- send_to_guardians(): 내담자의 보호자들에게 일괄 푸시 발송
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Firebase Admin SDK 초기화 (Graceful Degradation)
_firebase_initialized = False

try:
    import firebase_admin
    from firebase_admin import credentials, messaging

    # 서비스 계정 키 파일 경로
    SERVICE_ACCOUNT_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'firebase-service-account.json'
    )

    if os.path.exists(SERVICE_ACCOUNT_PATH):
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info("✅ Firebase Admin SDK 초기화 완료")
    else:
        logger.warning("⚠️ firebase-service-account.json 없음 → 푸시 알림 비활성화")

except ImportError:
    logger.warning("⚠️ firebase-admin 미설치 → 푸시 알림 비활성화 (pip install firebase-admin)")
except Exception as e:
    logger.warning(f"⚠️ Firebase 초기화 실패: {e}")


def is_push_available():
    """푸시 알림 발송 가능 여부"""
    return _firebase_initialized


def send_push(fcm_token: str, title: str, body: str, data: dict = None, apns_token: str = None) -> bool:
    """
    단일 기기에 푸시 알림 발송
    1. APNs 직접 발송 시도 (iOS, .p8 키 필요)
    2. APNs 성공 시 완료, 실패 시 FCM fallback
    3. FCM 발송 시 iOS 기기면 apns config 제외 (Firebase에 APNs키 미등록 시 ThirdPartyAuthError 방지)
    """
    if not _firebase_initialized and not apns_token:
        logger.debug("푸시 비활성화 상태 → 건너뜀")
        return False

    success = False
    is_ios = bool(apns_token)
    
    # 1. iOS인 경우 APNs 직접 발송 우선 실행
    if apns_token:
        logger.info("🍏 APNs 직접 발송 우선 시도...")
        success = _send_apns_direct(apns_token, title, body, data)
        if success:
            return True  # APNs 성공 → FCM 불필요

    # 2. FCM 발송 (Android / APNs 실패 시 백업)
    if _firebase_initialized and fcm_token:
        try:
            safe_data = {str(k): str(v) for k, v in (data or {}).items()}
            
            # 메시지 구성: iOS 기기면 apns config 제외 (Firebase에 APNs키 미등록 시 ThirdPartyAuthError 방지)
            msg_kwargs = dict(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=safe_data,
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        channel_id='guardian_alerts',
                        icon='ic_notification',
                        color='#7C4DFF',
                    ),
                ),
            )
            
            # iOS가 아닌 경우에만 apns config 추가
            if not is_ios:
                msg_kwargs['apns'] = messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1,
                        ),
                    ),
                )
            
            message = messaging.Message(**msg_kwargs)
            response = messaging.send(message)
            logger.info(f"✅ FCM 푸시 발송 성공: {response}")
            success = True

        except messaging.UnregisteredError:
            logger.warning(f"⚠️ 유효하지 않은 FCM 토큰 (앱 삭제됨): {fcm_token[:20]}...")
        except Exception as e:
            error_name = type(e).__name__
            logger.error(f"❌ FCM 푸시 발송 실패 ({error_name}): {e}")

    return success


def _send_apns_direct(device_token: str, title: str, body: str, data: dict = None) -> bool:
    """직접 APNs HTTP/2로 푸시 발송 (.p8 키 사용)"""
    try:
        import jwt as pyjwt
        import time
        import json
        import httpx

        TEAM_ID = "NU29S54D23"
        KEY_ID = "FX46Y248BT"
        BUNDLE_ID = "com.slyeee.maumon2026"
        
        key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apns_key_new.p8')
        if not os.path.exists(key_path):
            logger.error("❌ APNs .p8 키 파일 없음")
            return False

        with open(key_path) as f:
            private_key = f.read()

        token = pyjwt.encode(
            {"iss": TEAM_ID, "iat": int(time.time())},
            private_key, algorithm="ES256",
            headers={"alg": "ES256", "kid": KEY_ID}
        )

        # production 먼저 시도, 실패 시 sandbox (production 빌드 앱 대응)
        for env, host in [("production", "api.push.apple.com"), ("sandbox", "api.sandbox.push.apple.com")]:
            url = f"https://{host}/3/device/{device_token}"
            headers = {
                "authorization": f"bearer {token}",
                "apns-topic": BUNDLE_ID,
                "apns-push-type": "alert",
                "apns-priority": "10",
            }
            payload = {
                "aps": {"alert": {"title": title, "body": body}, "sound": "default", "badge": 1}
            }
            if data:
                payload.update(data)

            client = httpx.Client(http2=True)
            r = client.post(url, headers=headers, content=json.dumps(payload), timeout=10)
            client.close()

            if r.status_code == 200:
                logger.info(f"✅ APNs 직접 발송 성공 ({env})")
                return True
            elif r.status_code == 400 and "BadDeviceToken" in r.text:
                logger.warning(f"⚠️ APNs {env}: BadDeviceToken, 다음 환경 시도...")
                continue
            elif r.status_code == 410:  # Gone: 토큰 만료, 재시도 불필요
                break
            else:
                logger.warning(f"⚠️ APNs {env}: {r.status_code} {r.text}")
                if "BadEnvironment" not in r.text:
                    break

        logger.error(f"❌ APNs 직접 발송 실패")
        return False

    except Exception as e:
        logger.error(f"❌ APNs 직접 발송 에러: {e}")
        return False


def notify_guardians_mood(sharer_user, mood_level: int):
    """
    [트리거 ①] 기분 온도 알림
    - 일기 저장 시 모든 mood_level에 대해 보호자에게 알림
    - share_mood=True인 보호자만 대상
    - mood_level에 따라 메시지 내용이 동적으로 변경됨
    """
    # APNs 직접 발송 가능하므로 Firebase 미초기화 시에도 진행
    pass

    from models import db, User, ShareRelationship

    try:
        # 이 사용자에게 연결된 보호자 목록 조회
        relationships = ShareRelationship.query.filter_by(
            sharer_id=sharer_user.id,
            share_mood=True
        ).all()

        if not relationships:
            return

        sharer_name = sharer_user.nickname or sharer_user.real_name or "사용자"
        messages = {
            1: f"{sharer_name}님의 오늘 마음 온도가 많이 낮아요. 따뜻한 위로가 필요해 보입니다 😢",
            2: f"{sharer_name}님의 오늘 마음 온도가 조금 낮아요. 가벼운 안부를 전해보세요 😟",
            3: f"{sharer_name}님의 오늘 마음 온도는 평온합니다. 오늘도 응원해주세요 😐",
            4: f"{sharer_name}님의 오늘 마음 온도가 좋아요! 함께 기뻐해주세요 🙂",
            5: f"{sharer_name}님의 오늘 마음 온도가 아주 높아요! 행복한 하루를 공유해주세요 😊"
        }
        body_msg = messages.get(mood_level, f"{sharer_name}님이 일기를 기록했습니다.")

        for rel in relationships:
            viewer = User.query.get(rel.viewer_id)
            if viewer and (viewer.fcm_token or getattr(viewer, 'apns_token', None)):
                send_push(
                    fcm_token=viewer.fcm_token or '',
                    title=f"🌡️ {sharer_name}님의 마음 온도",
                    body=body_msg,
                    data={
                        "type": "mood_alert",
                        "sharer_id": str(sharer_user.id),
                        "mood_level": str(mood_level),
                    },
                    apns_token=getattr(viewer, 'apns_token', None),
                )

                # 중복 알림 방지 - 마지막 알림 시각 갱신
                rel.last_alert_at = datetime.utcnow()

        db.session.commit()
        logger.info(f"✅ 기분 알림 발송 완료: {sharer_name} (mood={mood_level})")

    except Exception as e:
        logger.error(f"❌ 기분 알림 발송 실패: {e}")


def notify_guardians_crisis(sharer_user):
    """
    [트리거 ②] 위기 감지 알림
    - safety_flag=True 일기 저장 시 보호자에게 긴급 알림
    - share_crisis=True인 보호자만 대상
    """
    # APNs 직접 발송 가능하므로 Firebase 미초기화 시에도 진행
    pass
    
    from models import db, User, ShareRelationship
    
    try:
        relationships = ShareRelationship.query.filter_by(
            sharer_id=sharer_user.id,
            share_crisis=True
        ).all()
        
        if not relationships:
            return
            
        sharer_name = sharer_user.nickname or sharer_user.real_name or "사용자"
        body_msg = f"🚨 {sharer_name}님의 최근 기록에서 위기 신호가 감지되었습니다. 직접 안부를 확인해주세요."
        
        for rel in relationships:
            viewer = User.query.get(rel.viewer_id)
            if viewer and (viewer.fcm_token or getattr(viewer, 'apns_token', None)):
                send_push(
                    fcm_token=viewer.fcm_token or '',
                    title="⚠️ 긴급: 위기 신호 감지",
                    body=body_msg,
                    data={
                        "type": "crisis_alert",
                        "sharer_id": str(sharer_user.id)
                    },
                    apns_token=getattr(viewer, 'apns_token', None),
                )
                rel.last_alert_at = datetime.utcnow()
                
        db.session.commit()
    except Exception as e:
        logger.error(f"❌ 위기 신호 알림 발송 실패: {e}")

def notify_guardians_ai_report(sharer_id: int, ai_comment: str):
    """
    [트리거 ③] AI 분석 리포트 완료 알림 (킬러 콘텐츠)
    - 일기 AI 분석 완료 시, 보호자(공유 설정된)에게 AI 요약 한 줄 코멘트와 함께 푸시 알림 발송
    - share_report=True (또는 share_mood=True) 인 보호자 대상
    """
    # APNs 직접 발송 가능하므로 Firebase 미초기화 시에도 진행
    pass
        
    from models import db, User, ShareRelationship
    import json
    
    try:
        # JSON 예외 처리하여 순수 텍스트만 추출
        clean_comment = ai_comment
        json_start = ai_comment.find('{')
        json_end = ai_comment.rfind('}')
        if json_start >= 0 and json_end > json_start:
            try:
                parsed = json.loads(ai_comment[json_start:json_end+1])
                clean_comment = parsed.get('comment') or parsed.get('ai_comment') or parsed.get('analysis') or parsed.get('message') or clean_comment
            except Exception:
                pass
                
        sharer_user = User.query.get(sharer_id)
        if not sharer_user:
            return
            
        relationships = ShareRelationship.query.filter_by(
            sharer_id=sharer_id
        ).all()
        
        sharer_name = sharer_user.nickname or sharer_user.username or "사용자"
        
        for rel in relationships:
            # 리포트 공유 권한이 없으면 제외
            if rel.share_report is False:
                continue
                
            viewer = User.query.get(rel.viewer_id)
            if viewer and (viewer.fcm_token or getattr(viewer, 'apns_token', None)):
                send_push(
                    fcm_token=viewer.fcm_token or '',
                    title=f"✨ {sharer_name}님의 AI 마음 분석이 도착했어요",
                    body=f"{clean_comment}",
                    data={
                        "type": "ai_report_alert",
                        "sharer_id": str(sharer_id)
                    },
                    apns_token=getattr(viewer, 'apns_token', None),
                )
        
        logger.info(f"✅ AI 리포트 자동 알림 발송 완료: {sharer_name}")
    except Exception as e:
        logger.error(f"❌ AI 리포트 알림 발송 실패: {e}")

    from models import db, User, ShareRelationship

    try:
        relationships = ShareRelationship.query.filter_by(
            sharer_id=sharer_user.id,
            share_crisis=True
        ).all()

        if not relationships:
            return

        sharer_name = sharer_user.nickname or sharer_user.real_name or "사용자"

        for rel in relationships:
            viewer = User.query.get(rel.viewer_id)
            if viewer and (viewer.fcm_token or getattr(viewer, 'apns_token', None)):
                send_push(
                    fcm_token=viewer.fcm_token or '',
                    title=f"⚠️ 긴급: {sharer_name}님 위기 신호 감지",
                    body=f"{sharer_name}님에게서 위기 신호가 감지되었습니다. 지금 바로 확인해 주세요.",
                    data={
                        "type": "crisis_alert",
                        "sharer_id": str(sharer_user.id),
                        "priority": "high",
                    },
                    apns_token=getattr(viewer, 'apns_token', None),
                )

                rel.last_alert_at = datetime.utcnow()

        db.session.commit()
        logger.info(f"🚨 위기 알림 발송 완료: {sharer_name}")

    except Exception as e:
        logger.error(f"❌ 위기 알림 발송 실패: {e}")


def notify_guardians_kick_flag(sharer_user, flags: list):
    """
    [트리거 ③] 킥 분석 플래그 알림
    - 시계열 분석에서 medium 또는 high 플래그 발생 시 보호자에게 알림
    - share_mood=True인 보호자에게 발송 (기분 관련 알림 설정 재활용)
    - 중복 방지: last_alert_at 기준 24시간 이내 동일 유형 재발송 안 함
    """
    # APNs 직접 발송 가능하므로 Firebase 미초기화 시에도 진행
    pass

    # medium/high만 필터
    alert_flags = [f for f in flags if f.get('severity') in ('medium', 'high')]
    if not alert_flags:
        return

    from models import db, User, ShareRelationship

    try:
        relationships = ShareRelationship.query.filter_by(
            sharer_id=sharer_user.id,
            share_mood=True
        ).all()

        if not relationships:
            return

        sharer_name = sharer_user.nickname or sharer_user.real_name or "사용자"

        # 가장 심각한 플래그를 메인 메시지로
        has_high = any(f['severity'] == 'high' for f in alert_flags)
        main_flag = next((f for f in alert_flags if f['severity'] == 'high'), alert_flags[0])

        if has_high:
            title = f"🔴 {sharer_name}님 주의 필요"
        else:
            title = f"🟠 {sharer_name}님 변화 감지"

        body = main_flag['message']
        if len(alert_flags) > 1:
            body += f" 외 {len(alert_flags) - 1}건"

        for rel in relationships:
            # 중복 알림 방지: 24시간 이내 발송 이력 있으면 건너뜀
            if rel.last_alert_at:
                hours_since = (datetime.utcnow() - rel.last_alert_at).total_seconds() / 3600
                if hours_since < 24:
                    continue

            viewer = User.query.get(rel.viewer_id)
            if viewer and (viewer.fcm_token or getattr(viewer, 'apns_token', None)):
                send_push(
                    fcm_token=viewer.fcm_token or '',
                    title=title,
                    body=body,
                    data={
                        "type": "kick_flag_alert",
                        "sharer_id": str(sharer_user.id),
                        "priority": "high" if has_high else "normal",
                        "flag_count": str(len(alert_flags)),
                    },
                    apns_token=getattr(viewer, 'apns_token', None),
                )

                rel.last_alert_at = datetime.utcnow()

        db.session.commit()
        logger.info(f"📊 킥 플래그 알림 발송 완료: {sharer_name} ({len(alert_flags)}건)")

    except Exception as e:
        logger.error(f"❌ 킥 플래그 알림 발송 실패: {e}")
