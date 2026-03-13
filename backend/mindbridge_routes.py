"""
[Mind Bridge] Phase 3/4/5 — 마음 브릿지 API
수신자 관리 + 감정 데이터 공유 + 열람 + 이력 조회

Blueprint: /api/bridge/*
모든 엔드포인트는 JWT 인증 필수
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import json

from models import (
    db, User, Diary, BridgeRecipient, BridgeShare, BridgeViewLog
)

bridge_bp = Blueprint('bridge_bp', __name__, url_prefix='/api/bridge')

# ═══════════════════════════════════════════
# [Phase 3] 수신자 관리 CRUD
# ═══════════════════════════════════════════

@bridge_bp.route('/recipients', methods=['GET'])
@jwt_required()
def get_recipients():
    """내 수신자 목록 조회"""
    user_id = int(get_jwt_identity())  # [Fix#3] str→int 캐스팅
    recipients = BridgeRecipient.query.filter_by(user_id=user_id).order_by(BridgeRecipient.created_at.desc()).all()
    return jsonify({
        'status': 'ok',
        'recipients': [r.to_dict() for r in recipients],
        'family_count': sum(1 for r in recipients if r.type == 'family'),
        'counselor_count': sum(1 for r in recipients if r.type == 'counselor'),
    })


@bridge_bp.route('/recipients', methods=['POST'])
@jwt_required()
def add_recipient():
    """수신자 추가"""
    user_id = int(get_jwt_identity())  # [Fix#3] str→int 캐스팅
    data = request.get_json()
    
    # Whitelist 파라미터 검증
    name = data.get('name', '').strip()
    r_type = data.get('type', '')
    schedule = data.get('share_schedule', 'weekly')
    pin = data.get('pin')  # 상담사용 PIN (선택)
    
    if not name:
        return jsonify({'error': '수신자 이름을 입력하세요'}), 400
    if r_type not in ('family', 'counselor'):
        return jsonify({'error': '유형은 family 또는 counselor만 가능합니다'}), 400
    if schedule not in ('daily', 'weekly', 'biweekly', 'manual'):
        return jsonify({'error': '유효하지 않은 공유 주기입니다'}), 400
    
    # 수신자 수 제한 (가족 5명, 상담사 3명)
    existing = BridgeRecipient.query.filter_by(user_id=user_id, type=r_type).count()
    limit = 5 if r_type == 'family' else 3
    if existing >= limit:
        label = '가족/보호자' if r_type == 'family' else '상담사'
        return jsonify({'error': f'{label}는 최대 {limit}명까지 등록할 수 있습니다'}), 400
    
    recipient = BridgeRecipient(
        user_id=user_id,
        name=name,
        type=r_type,
        share_schedule=schedule,
        pin_hash=generate_password_hash(pin) if pin else None,
    )
    db.session.add(recipient)
    db.session.commit()
    
    print(f"🌉 [MindBridge] 수신자 등록: user={user_id}, name={name}, type={r_type}")
    return jsonify({'status': 'ok', 'recipient': recipient.to_dict()}), 201


@bridge_bp.route('/recipients/<int:recipient_id>', methods=['PUT'])
@jwt_required()
def update_recipient(recipient_id):
    """수신자 정보 수정 (활성화/비활성화, 스케줄 변경)"""
    user_id = int(get_jwt_identity())  # [Fix#3]
    recipient = BridgeRecipient.query.filter_by(id=recipient_id, user_id=user_id).first()
    
    if not recipient:
        return jsonify({'error': '수신자를 찾을 수 없습니다'}), 404
    
    data = request.get_json()
    
    # Whitelist 방식 업데이트
    if 'is_active' in data:
        recipient.is_active = bool(data['is_active'])
    if 'share_schedule' in data and data['share_schedule'] in ('daily', 'weekly', 'biweekly', 'manual'):
        recipient.share_schedule = data['share_schedule']
    if 'name' in data and data['name'].strip():
        recipient.name = data['name'].strip()
    if 'pin' in data:
        recipient.pin_hash = generate_password_hash(data['pin']) if data['pin'] else None
    
    db.session.commit()
    return jsonify({'status': 'ok', 'recipient': recipient.to_dict()})


@bridge_bp.route('/recipients/<int:recipient_id>', methods=['DELETE'])
@jwt_required()
def delete_recipient(recipient_id):
    """수신자 삭제 (관련 공유 데이터도 함께 삭제)"""
    user_id = int(get_jwt_identity())  # [Fix#3]
    recipient = BridgeRecipient.query.filter_by(id=recipient_id, user_id=user_id).first()
    
    if not recipient:
        return jsonify({'error': '수신자를 찾을 수 없습니다'}), 404
    
    name = recipient.name
    db.session.delete(recipient)  # cascade로 shares도 삭제됨
    db.session.commit()
    
    print(f"🌉 [MindBridge] 수신자 삭제: user={user_id}, name={name}")
    return jsonify({'status': 'ok', 'message': f'{name} 수신자가 삭제되었습니다'})


# ═══════════════════════════════════════════
# [Phase 4] 공유 깊이 설정
# ═══════════════════════════════════════════

@bridge_bp.route('/recipients/<int:recipient_id>/depth', methods=['PUT'])
@jwt_required()
def update_depth_settings(recipient_id):
    """수신자별 공유 깊이 설정 변경"""
    user_id = int(get_jwt_identity())  # [Fix#3]
    recipient = BridgeRecipient.query.filter_by(id=recipient_id, user_id=user_id).first()
    
    if not recipient:
        return jsonify({'error': '수신자를 찾을 수 없습니다'}), 404
    
    data = request.get_json()
    depth = data.get('depth_settings', {})
    
    # Whitelist 방식 — 허용된 필드만 업데이트
    allowed_fields = {
        'mood_status': 'depth_mood_status',
        'mood_graph': 'depth_mood_graph',
        'ai_summary': 'depth_ai_summary',
        'detailed_analysis': 'depth_detailed_analysis',
        'trigger_keywords': 'depth_trigger_keywords',
    }
    
    for key, col_name in allowed_fields.items():
        if key in depth:
            setattr(recipient, col_name, bool(depth[key]))
    
    db.session.commit()
    print(f"🌉 [MindBridge] 깊이 설정 변경: recipient={recipient.name}, settings={depth}")
    return jsonify({'status': 'ok', 'recipient': recipient.to_dict()})


# ═══════════════════════════════════════════
# [Phase 3/4] 감정 데이터 공유 (암호화 전송)
# ═══════════════════════════════════════════

@bridge_bp.route('/share', methods=['POST'])
@jwt_required()
def create_share():
    """
    수신자에게 감정 데이터 공유
    - 클라이언트에서 공유할 항목을 선별하여 JSON 전송
    - 서버에서 Fernet 암호화 후 저장
    - 30일 후 자동 만료
    """
    user_id = int(get_jwt_identity())  # [Fix#3]
    data = request.get_json()
    
    recipient_id = data.get('recipient_id')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    share_data = data.get('data')  # 클라이언트가 깊이 설정에 따라 선별한 JSON
    shared_items = data.get('shared_items', '')  # "감정상태,AI요약" 등
    
    if not all([recipient_id, start_date, end_date, share_data]):
        return jsonify({'error': '필수 항목이 누락되었습니다'}), 400
    
    # 수신자 소유자 검증
    recipient = BridgeRecipient.query.filter_by(id=recipient_id, user_id=user_id).first()
    if not recipient:
        return jsonify({'error': '수신자를 찾을 수 없습니다'}), 404
    
    if not recipient.is_active:
        return jsonify({'error': '비활성화된 수신자입니다'}), 400
    
    # 데이터 암호화
    try:
        from crypto_utils import crypto_manager
        if crypto_manager:
            json_str = json.dumps(share_data, ensure_ascii=False)
            encrypted = crypto_manager.encrypt(json_str)
        else:
            # 암호화 모듈 미로드 시 평문 저장 (개발 환경)
            encrypted = json.dumps(share_data, ensure_ascii=False)
            print("⚠️ [MindBridge] crypto_manager 미초기화, 평문 저장")
    except Exception as e:
        print(f"❌ [MindBridge] 암호화 실패: {e}")
        return jsonify({'error': '데이터 암호화에 실패했습니다'}), 500
    
    share = BridgeShare(
        user_id=user_id,
        recipient_id=recipient_id,
        start_date=start_date,
        end_date=end_date,
        encrypted_data=encrypted,
        shared_items=shared_items,
        expires_at=datetime.utcnow() + timedelta(days=30),
    )
    db.session.add(share)
    db.session.commit()
    
    print(f"🌉 [MindBridge] 공유 생성: user={user_id} → {recipient.name}, 항목={shared_items}")
    return jsonify({'status': 'ok', 'share': share.to_dict()}), 201


@bridge_bp.route('/shares', methods=['GET'])
@jwt_required()
def get_share_history():
    """내 공유 이력 조회 (최근 100건)"""
    user_id = int(get_jwt_identity())  # [Fix#3]
    shares = BridgeShare.query.filter_by(user_id=user_id)\
        .order_by(BridgeShare.created_at.desc())\
        .limit(100)\
        .all()
    
    results = []
    for s in shares:
        d = s.to_dict()
        # 수신자 이름 추가
        if s.recipient:
            d['recipient_name'] = s.recipient.name
            d['recipient_type'] = s.recipient.type
        results.append(d)
    
    return jsonify({'status': 'ok', 'shares': results})


# ═══════════════════════════════════════════
# [Phase 3] 상담사 대시보드 — 공유 데이터 열람
# ═══════════════════════════════════════════

@bridge_bp.route('/view/<int:share_id>', methods=['POST'])
def view_shared_data(share_id):
    """
    상담사/가족이 공유 데이터 열람
    - PIN 인증 필요 (상담사 수신자인 경우)
    - 열람 로그 기록
    - 사용자에게 푸시 알림 전송
    """
    share = BridgeShare.query.get(share_id)
    if not share:
        return jsonify({'error': '공유 데이터를 찾을 수 없습니다'}), 404
    
    # 만료 체크
    if share.expires_at and datetime.utcnow() > share.expires_at:
        return jsonify({'error': '만료된 공유 데이터입니다'}), 410
    
    # PIN 인증 (상담사인 경우)
    recipient = share.recipient
    if recipient and recipient.type == 'counselor' and recipient.pin_hash:
        pin = request.json.get('pin', '') if request.is_json else ''
        if not check_password_hash(recipient.pin_hash, pin):
            return jsonify({'error': 'PIN이 올바르지 않습니다'}), 403
    
    # 데이터 복호화
    try:
        from crypto_utils import crypto_manager
        if crypto_manager and share.encrypted_data.startswith('gAAAA'):
            decrypted_str = crypto_manager.decrypt(share.encrypted_data)
            decrypted_data = json.loads(decrypted_str)
        else:
            decrypted_data = json.loads(share.encrypted_data)
    except Exception as e:
        print(f"❌ [MindBridge] 복호화 실패: {e}")
        return jsonify({'error': '데이터 복호화에 실패했습니다'}), 500
    
    # 열람 상태 업데이트
    share.is_viewed = True
    share.viewed_at = datetime.utcnow()
    share.view_count += 1
    
    # 열람 로그 기록
    log = BridgeViewLog(
        share_id=share_id,
        viewer_name=recipient.name if recipient else 'unknown',
        viewer_ip=request.remote_addr,
    )
    db.session.add(log)
    db.session.commit()
    
    print(f"👁️ [MindBridge] 데이터 열람: share={share_id}, viewer={log.viewer_name}")
    
    # [Phase 5] 사용자에게 열람 알림 푸시 (비동기)
    _send_view_notification(share.user_id, recipient.name if recipient else '알 수 없음')
    
    return jsonify({
        'status': 'ok',
        'data': decrypted_data,
        'start_date': share.start_date,
        'end_date': share.end_date,
        'shared_items': share.shared_items,
    })


@bridge_bp.route('/view-logs', methods=['GET'])
@jwt_required()
def get_view_logs():
    """내 공유 데이터의 열람 로그 조회"""
    user_id = int(get_jwt_identity())  # [Fix#3]
    
    # 내 공유 데이터에 대한 열람 로그
    logs = db.session.query(BridgeViewLog)\
        .join(BridgeShare)\
        .filter(BridgeShare.user_id == user_id)\
        .order_by(BridgeViewLog.viewed_at.desc())\
        .limit(50)\
        .all()
    
    results = []
    for log in logs:
        results.append({
            'id': log.id,
            'share_id': log.share_id,
            'viewer_name': log.viewer_name,
            'viewed_at': log.viewed_at.isoformat() if log.viewed_at else None,
        })
    
    return jsonify({'status': 'ok', 'logs': results})


# ═══════════════════════════════════════════
# [Phase 3/4] 공유할 데이터 수집 (AI 분석 결과 기반)
# ═══════════════════════════════════════════

@bridge_bp.route('/prepare-share/<int:recipient_id>', methods=['GET'])
@jwt_required()
def prepare_share_data(recipient_id):
    """
    수신자의 공유 깊이 설정에 따라 공유할 데이터를 미리 생성
    실제 공유 전 미리보기로 사용
    """
    user_id = int(get_jwt_identity())  # [Fix#3]
    recipient = BridgeRecipient.query.filter_by(id=recipient_id, user_id=user_id).first()
    
    if not recipient:
        return jsonify({'error': '수신자를 찾을 수 없습니다'}), 404
    
    # 최근 7일 일기 조회
    from datetime import date, timedelta as td
    end_date = date.today()
    start_date = end_date - td(days=6)
    
    diaries = Diary.query.filter(
        Diary.user_id == user_id,
        Diary.date >= start_date.isoformat(),
        Diary.date <= end_date.isoformat(),
    ).order_by(Diary.date.asc()).all()
    
    # 깊이 설정에 따라 데이터 필터링
    share_data = {
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
        },
        'diary_count': len(diaries),
    }
    shared_items_list = []
    
    # 1) 주간 감정 상태 (🟢🟡🔴)
    if recipient.depth_mood_status:
        mood_levels = [d.mood_level for d in diaries if d.mood_level is not None]
        avg_mood = sum(mood_levels) / len(mood_levels) if mood_levels else 0
        # [Fix#6] mood_level은 1~5 스케일 (1=매우나쁨, 5=매우좋음)
        if avg_mood >= 4:
            status = '🟢 안정'
        elif avg_mood >= 3:
            status = '🟡 보통'
        else:
            status = '🔴 주의'
        share_data['mood_status'] = {
            'average': round(avg_mood, 1),
            'label': status,
            'count': len(mood_levels),
        }
        shared_items_list.append('감정상태')
    
    # 2) 감정 변화 그래프 데이터
    if recipient.depth_mood_graph:
        share_data['mood_graph'] = [
            {'date': d.date, 'level': d.mood_level}
            for d in diaries if d.mood_level is not None
        ]
        shared_items_list.append('감정그래프')
    
    # 3) AI 분석 요약
    if recipient.depth_ai_summary:
        summaries = []
        for d in diaries:
            if d.ai_comment:
                try:
                    from app import safe_decrypt, safe_extract_ai_comment
                    comment = safe_extract_ai_comment(safe_decrypt(d.ai_comment))
                except Exception:
                    comment = d.ai_comment
                if not comment:
                    continue
                # 첫 100자만 요약
                summaries.append({
                    'date': d.date,
                    'summary': comment[:100] + ('...' if len(comment) > 100 else ''),
                })
        share_data['ai_summaries'] = summaries
        shared_items_list.append('AI요약')
    
    # 4) 7개 항목 상세 (킥 분석)
    if recipient.depth_detailed_analysis:
        detailed = []
        for d in diaries:
            entry = {'date': d.date}
            if d.emotion_desc:
                try:
                    from app import safe_decrypt
                    entry['emotion'] = safe_decrypt(d.emotion_desc)
                except Exception:
                    entry['emotion'] = d.emotion_desc
            if d.ai_emotion:
                entry['ai_emotion'] = d.ai_emotion
            detailed.append(entry)
        share_data['detailed_analysis'] = detailed
        shared_items_list.append('상세분석')
    
    # 5) 트리거 키워드
    if recipient.depth_trigger_keywords:
        # AI 분석에서 키워드 추출 (간단 구현)
        keywords = set()
        for d in diaries:
            if d.ai_emotion:
                try:
                    emotions = json.loads(d.ai_emotion)
                    if isinstance(emotions, list):
                        keywords.update(emotions[:3])
                    elif isinstance(emotions, str):
                        keywords.add(emotions)
                except (json.JSONDecodeError, TypeError):
                    if d.ai_emotion:
                        keywords.add(d.ai_emotion)
        share_data['trigger_keywords'] = list(keywords)[:10]
        shared_items_list.append('키워드')
    
    # 위기 신호 체크 (항상 포함)
    crisis_days = [d.date for d in diaries if d.safety_flag]
    if crisis_days:
        share_data['crisis_alert'] = {
            'has_alert': True,
            'dates': crisis_days,
        }
        shared_items_list.append('위기신호')
    
    return jsonify({
        'status': 'ok',
        'preview': share_data,
        'shared_items': ','.join(shared_items_list),
        'recipient': recipient.to_dict(),
    })


# ═══════════════════════════════════════════
# [Phase 5] 보안 — 데이터 전체 삭제 (회원 탈퇴)
# ═══════════════════════════════════════════

@bridge_bp.route('/delete-all', methods=['DELETE'])
@jwt_required()
def delete_all_bridge_data():
    """
    회원 탈퇴 시 마음 브릿지 데이터 전체 삭제
    수신자, 공유 데이터, 열람 로그 모두 삭제
    """
    user_id = int(get_jwt_identity())  # [Fix#3]
    
    # 1) 열람 로그 삭제 (FK 순서)
    share_ids = [s.id for s in BridgeShare.query.filter_by(user_id=user_id).all()]
    if share_ids:
        BridgeViewLog.query.filter(BridgeViewLog.share_id.in_(share_ids)).delete(synchronize_session=False)
    
    # 2) 공유 데이터 삭제
    BridgeShare.query.filter_by(user_id=user_id).delete()
    
    # 3) 수신자 삭제
    BridgeRecipient.query.filter_by(user_id=user_id).delete()
    
    db.session.commit()
    
    print(f"🗑️ [MindBridge] 전체 삭제 완료: user={user_id}")
    return jsonify({'status': 'ok', 'message': '마음 브릿지 데이터가 모두 삭제되었습니다'})


# ═══════════════════════════════════════════
# [Phase 5] 열람 알림 푸시 (헬퍼)
# ═══════════════════════════════════════════

def _send_view_notification(user_id, viewer_name):
    """상담사/가족이 데이터를 열람했을 때 사용자에게 푸시 알림"""
    try:
        user = User.query.get(user_id)
        if not user:
            return
        
        title = "🌉 마음 브릿지"
        body = f"{viewer_name}님이 공유된 감정 리포트를 확인했습니다"
        
        # FCM 알림 (Android)
        if user.fcm_token:
            try:
                import firebase_admin
                from firebase_admin import messaging
                msg = messaging.Message(
                    notification=messaging.Notification(title=title, body=body),
                    token=user.fcm_token,
                    data={'type': 'bridge_view', 'viewer': viewer_name},
                )
                messaging.send(msg)
                print(f"📱 [MindBridge] FCM 알림 전송: user={user_id}")
            except Exception as e:
                print(f"⚠️ [MindBridge] FCM 전송 실패: {e}")
        
        # [Fix#8] APNs 알림 (iOS) — push_service.send_push()로 통합 (push_utils 모듈 존재하지 않음)
        if user.apns_token and not user.fcm_token:
            try:
                from push_service import send_push
                send_push(
                    fcm_token='',  # FCM 토큰 없음
                    title=title,
                    body=body,
                    data={'type': 'bridge_view', 'viewer': viewer_name},
                    apns_token=user.apns_token,
                )
                print(f"🍎 [MindBridge] APNs 알림 전송: user={user_id}")
            except Exception as e:
                print(f"⚠️ [MindBridge] APNs 전송 실패: {e}")
    except Exception as e:
        print(f"⚠️ [MindBridge] 알림 전송 중 오류: {e}")
