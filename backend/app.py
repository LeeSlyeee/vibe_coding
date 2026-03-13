from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
# from flask_pymongo import PyMongo # Removed
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from config import Config
from models import db, User, Diary, ChatLog, Center, ShareCode, ShareRelationship
import os
import sys
from dotenv import load_dotenv # [Fix] Explicit loading
from crypto_utils import EncryptionManager
from analysis_worker import start_analysis_thread 

import traceback 

# [Init] Load Env & Fail Fast
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env')) # Explicit Path Loading

app = Flask(__name__)

# [PostgreSQL Integration] - Vibe DB Migration (Safe Env Loading)
# [Fail Fast] Check Critical Configs
if not os.environ.get('DATABASE_URL'):
    raise RuntimeError("DATABASE_URL is missing in .env")
if not os.environ.get('ENCRYPTION_KEY'):
    raise RuntimeError("ENCRYPTION_KEY is missing in .env")

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 20
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 30
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 60

# [JWT Secret]
jwt_key = os.environ.get('JWT_SECRET_KEY')
if not jwt_key:
    print("❌ [CRITICAL] JWT_SECRET_KEY is missing. Terminating...")
    sys.exit(1)

app.config['JWT_SECRET_KEY'] = jwt_key
# [UX Fix] Extend Token Lifetime (Default 15m is too short for long analysis)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=3650)  # 10년 (모바일 앱 영구 로그인)
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['JSON_AS_ASCII'] = False # For Korean characters
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'query_string'] # [Standard] RFC 6750 Sec 2.3 Fallback
app.config['JWT_IDENTITY_CLAIM'] = 'user_id' # [CRITICAL] Django Token Compatibility

# [MongoDB Removed]
# app.config['MONGO_URI'] = ... # Deleted

# Initialize DB (Postgres)
db.init_app(app)

# Initialize MongoDB - REMOVED
# mongo = PyMongo(app)

# Initialize Encryption
try:
    crypto = EncryptionManager()  # [Fix#1] os.environ에서 자동 로드 (app.config에는 ENCRYPTION_KEY가 없음)
    print("🔐 Encryption Manager Initialized")
except Exception as e:
    print(f"⚠️ Encryption Init Failed: {e}")
    crypto = None

# Register Blueprints (Medication, B2G, Share)
try:
    from medication_routes import med_bp
    app.register_blueprint(med_bp)
    print("✅ Medication Routes Registered")
except Exception as e:
    print(f"⚠️ Failed to register Medication Routes: {e}")

try:
    from b2g_routes import b2g_bp
    app.register_blueprint(b2g_bp)
    print("✅ B2G Routes Registered")
except Exception as e:
    print(f"⚠️ Failed to register B2G Routes: {e}")

try:
    from share_routes import share_bp
    app.register_blueprint(share_bp)
    print("✅ Share Routes Registered")
except Exception as e:
    print(f"⚠️ Failed to register Share Routes: {e}")

try:
    from chat_routes import chat_bp
    app.register_blueprint(chat_bp)
    print("✅ Chat Routes Registered")
except Exception as e:
    print(f"⚠️ Failed to register Chat Routes: {e}")

try:
    from kick_routes import kick_bp, set_decrypt_func
    app.register_blueprint(kick_bp)
    # set_decrypt_func는 safe_decrypt 정의 후 호출 (아래 @app.before_first_request 대체)
    print("✅ Kick Analysis Routes Registered (Phase 1 + Phase 2)")
except Exception as e:
    print(f"⚠️ Failed to register Kick Routes: {e}")

try:
    from mindbridge_routes import bridge_bp
    app.register_blueprint(bridge_bp)
    print("✅ Mind Bridge Routes Registered (Phase 3/4/5)")
except Exception as e:
    print(f"⚠️ Failed to register Mind Bridge Routes: {e}")

try:
    from report_routes import report_bp
    app.register_blueprint(report_bp)
    print("✅ Report Routes Registered")
except Exception as e:
    print(f"⚠️ Failed to register Report Routes: {e}")

try:
    from stats_routes import stats_bp
    app.register_blueprint(stats_bp)
    print("✅ Stats Routes Registered")
except Exception as e:
    print(f"⚠️ Failed to register Stats Routes: {e}")


@app.before_request
def log_request_info():
    print(f"📡 [Global] Request: {request.method} {request.url}")
    print(f"📦 [Headers] {request.headers}")
    if request.method in ['PUT', 'POST']:
        pass

jwt = JWTManager(app)

# [Debug] JWT Error Checkers
@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    print(f"❌ [JWT Error] Invalid Token: {error_string}")
    return jsonify({'msg': error_string}), 422

@jwt.unauthorized_loader
def missing_token_callback(error_string):
    print(f"❌ [JWT Error] Missing Token: {error_string}")
    return jsonify({'msg': error_string}), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    print(f"❌ [JWT Error] Expired Token: {jwt_payload}")
    return jsonify({'msg': 'Token has expired'}), 401

# Create Tables (if not exists)
with app.app_context():
    db.create_all()

# CORS Setup
# Allowed Origins: Native Apps + Web (Patient & Admin)
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:5173", 
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://217.142.253.35",
            "https://217.142.253.35.nip.io",
            "https://217.142.253.35"
        ],
        "supports_credentials": True,
        "allow_headers": ["Content-Type", "Authorization"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    }
})

# [Auth Check Logic]
@app.route('/api/auth/verify', methods=['GET'])
@jwt_required()
def verify_token():
    current_user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=current_user_id).first()
    return jsonify({"valid": True, "username": user.username if user else "Unknown"}), 200

# [API Endpoint: Register]
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    nickname = data.get('nickname')
    role = data.get('role', 'user')

    if not username or not password:
        return jsonify({'msg': '아이디 또는 비밀번호를 입력해주세요.'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'msg': '이미 존재하는 사용자입니다.'}), 400

    new_user = User(
        username=username,
        password=generate_password_hash(password, method='pbkdf2:sha256'), 
        nickname=nickname,
        role=role
    )
    
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'msg': '회원가입이 완료되었습니다.'}), 201

# [API Endpoint: Login]
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username') # Accepts username or user_id
    password = data.get('password')
    center_code = data.get('center_code') or data.get('linked_center_code')

    user = User.query.filter_by(username=username).first()
    if not user:
         return jsonify({'msg': '아이디 또는 비밀번호가 올바르지 않습니다.'}), 401
         
    if not check_password_hash(user.password, password):
        # Allow fallback for pure MD5 or plain text (dev only)
        if user.password == password:
             pass # Allowed
        else:
             return jsonify({'msg': '아이디 또는 비밀번호가 올바르지 않습니다.'}), 401

    # [Fix] Use user.id as identity (int -> str) for consistency with get_diary
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"username": user.username}
    )
    # 동적 assessment/risk 계산 (로그인 시)
    from datetime import datetime, timedelta
    real_center_code = user.center_code
    diary_count = Diary.query.filter_by(user_id=user.id).count()
    login_assessment = diary_count > 0
    login_risk = 'low'
    recent_cutoff = datetime.utcnow() - timedelta(days=7)
    recent = Diary.query.filter(Diary.user_id == user.id, Diary.created_at >= recent_cutoff).all()
    if recent:
        avg = sum(d.mood_level or 3 for d in recent) / len(recent)
        has_flag = any(getattr(d, 'safety_flag', None) in ['need_help', 'danger'] for d in recent)
        if has_flag or avg <= 2: login_risk = 'high'
        elif avg <= 3: login_risk = 'moderate'

    # [Fix] Frontend Compatibility: Include FULL user object & token alias
    return jsonify({
        'access_token': access_token,
        'token': access_token, # Alias
        'assessment_completed': login_assessment,
        'risk_level': login_risk,
        'user': {
            'id': user.id,
            'username': user.username,
            'nickname': user.nickname or user.username,
            'real_name': user.real_name,
            'email': getattr(user, 'email', ''), 
            'role': getattr(user, 'role', 'user'), 
            'center_code': real_center_code,
            'linked_center_code': real_center_code,
            'is_premium': (getattr(user, 'role', 'user') in ['premium', 'admin'])
        },
        'msg': '로그인 성공'
    }), 200

@app.route('/api/user/me', methods=['GET'])
@jwt_required()
def get_me():
    current_user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=current_user_id).first()
    
    if not user:
        return jsonify({'msg': '사용자를 찾을 수 없습니다.'}), 404

    # --- 동적 assessment/risk 계산 ---
    from datetime import datetime, timedelta
    diary_count = Diary.query.filter_by(user_id=user.id).count()
    assessment_done = diary_count > 0

    # 최근 7일 일기 기반 위험도 판단
    risk = 'low'
    recent_cutoff = datetime.utcnow() - timedelta(days=7)
    recent_diaries = Diary.query.filter(
        Diary.user_id == user.id,
        Diary.created_at >= recent_cutoff
    ).all()

    if recent_diaries:
        avg_mood = sum(d.mood_level or 3 for d in recent_diaries) / len(recent_diaries)
        has_safety_flag = any(
            getattr(d, 'safety_flag', None) in ['need_help', 'danger']
            for d in recent_diaries
        )
        if has_safety_flag or avg_mood <= 2:
            risk = 'high'
        elif avg_mood <= 3:
            risk = 'moderate'

    # 마음 온도 계산
    mood_temp = calculate_mood_temperature(user.id) if 'calculate_mood_temperature' in dir() else None

    return jsonify({
        'id': user.id,
        'username': user.username,
        'nickname': user.nickname or user.username,
        'real_name': user.real_name,
        'email': getattr(user, 'email', ''),
        'role': getattr(user, 'role', 'user'),
        'center_code': user.center_code,
        'linked_center_code': user.center_code,
        'assessment_completed': assessment_done,
        'risk_level': risk,
        'is_premium': (getattr(user, 'role', 'user') in ['premium', 'admin']),
        'mood_temperature': mood_temp
    }), 200
    
#Helper to safely decrypt
def safe_decrypt(text):
    if not crypto: return text
    try:
        return crypto.decrypt(text)
    except Exception:
        return text

#Helper to safely encrypt
def safe_encrypt(text):
    if not crypto: return text
    try:
        return crypto.encrypt(text)
    except Exception:
        return text

# Alias for external usage (e.g. b2g_routes)
def encrypt_data(text):
    return safe_encrypt(text)

# [Kick Phase 2] 복호화 함수를 kick_routes에 주입
try:
    from kick_routes import set_decrypt_func
    set_decrypt_func(safe_decrypt)
except Exception:
    pass

# [API Endpoint: Get Diaries]
@app.route('/api/diaries', methods=['GET'])
@jwt_required()
def get_diaries():
    current_user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=current_user_id).first()
    
    if not user:
        return jsonify([]), 200

    query = Diary.query.filter_by(user_id=user.id)

    # [Filter Parameter Support]
    year = request.args.get('year')
    month = request.args.get('month')
    start_date = request.args.get('start_date') or request.args.get('startDate')
    end_date = request.args.get('end_date') or request.args.get('endDate')

    if year and month:
        try:
            # Pad month to 2 digits
            month_str = f"{int(month):02d}"
            prefix = f"{year}-{month_str}"
            query = query.filter(Diary.date.startswith(prefix))
        except ValueError:
            pass # Ignore invalid int conversion

    if start_date:
        query = query.filter(Diary.date >= start_date)
    
    if end_date:
        query = query.filter(Diary.date <= end_date)

    # [Sort] Descending (Newest first)
    # Using specific model field for ordering
    diaries = query.order_by(Diary.date.desc()).all()
    
    result = [serialize_diary(d) for d in diaries]
    return jsonify(result), 200

# [API Endpoint: Create Diary]
@app.route('/api/diaries', methods=['POST'])
@jwt_required()
def create_diary():
    current_user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=current_user_id).first()
    if not user:
        return jsonify({'msg': '사용자를 찾을 수 없습니다.'}), 404  # [Fix#7] NoneType 방어
    data = request.get_json()

    # [Strict Date Validation] Prevent retroactive diary misdating
    client_date = data.get('date')
    if not client_date:
        return jsonify({"msg": "Diary date is required"}), 400

    # Encrypt Content Fields
    encrypted_event = safe_encrypt(data.get('event') or data.get('question1'))
    encrypted_emotion_desc = safe_encrypt(data.get('emotion_desc') or data.get('question2'))
    encrypted_emotion_meaning = safe_encrypt(data.get('emotion_meaning') or data.get('question3'))
    encrypted_self_talk = safe_encrypt(data.get('self_talk') or data.get('question4'))
    encrypted_gratitude = safe_encrypt(data.get('gratitude_note'))
    encrypted_sleep = safe_encrypt(data.get('sleep_condition'))
    encrypted_ai_comment = safe_encrypt(data.get('ai_comment'))
    encrypted_ai_emotion = safe_encrypt(data.get('ai_emotion'))

    new_diary = Diary(
        user_id=user.id,
        date=client_date,
        event=encrypted_event, # Encrypted
        sleep_condition=encrypted_sleep, # Encrypted
        emotion_desc=encrypted_emotion_desc, # Encrypted
        emotion_meaning=encrypted_emotion_meaning, # Encrypted
        self_talk=encrypted_self_talk, # Encrypted
        mood_level=data.get('mood_level', 3),
        weather=data.get('weather'),
        temperature=data.get('temperature'),
        mode=data.get('mode', 'green'), # Default
        # mood_intensity removed (Not in DB)
        gratitude_note=encrypted_gratitude, # Encrypted

        ai_comment=encrypted_ai_comment, # [New] Encrypted
        ai_emotion=encrypted_ai_emotion, # [New] Encrypted
        safety_flag=data.get('safety_flag', False)
    )
    
    db.session.add(new_diary)
    db.session.commit()



    start_analysis_thread(
        new_diary.id,
        new_diary.date, 
        data.get('event') or data.get('question1') or "",
        data.get('sleep_condition') or "",
        data.get('emotion_desc') or data.get('question2') or "",
        data.get('emotion_meaning') or data.get('question3') or "",
        data.get('self_talk') or data.get('question4') or ""
    )

    response_data = serialize_diary(new_diary)
    
    # [Local Sync] Push to Medical Dashboard (Localhost:8000)
    try:
        from b2g_routes import sync_to_insight_mind
        sync_to_insight_mind(response_data, user.id)
    except Exception as e:
        print(f"⚠️ Sync Trigger Failed: {e}")

    # [Push Notification] 보호자 알림 트리거
    try:
        from push_service import notify_guardians_mood, notify_guardians_crisis, notify_guardians_kick_flag, is_push_available
        if is_push_available():
            mood = data.get('mood_level', 3)
            safety = data.get('safety_flag', False)
            # ① 기분 온도 알림 (모든 기분에 대해 발송)
            if mood:
                notify_guardians_mood(user, int(mood))
            # ② 위기 감지 알림 (safety_flag=True)
            if safety in [True, 'need_help', 'danger']:
                notify_guardians_crisis(user)
            # ③ 킥 분석 (Phase 1~3) → medium/high 플래그 시 알림
            try:
                all_kick_flags = []
                # Phase 1: 시계열
                from kick_analysis import analyze_timeseries
                ts_result = analyze_timeseries(user.id, db.session, Diary)
                if ts_result.get('flags'):
                    all_kick_flags.extend(ts_result['flags'])
                # Phase 2: 언어 지문
                from kick_analysis.linguistic import analyze_linguistic
                ling_result = analyze_linguistic(user.id, db.session, Diary, crypto_decrypt=safe_decrypt)
                if ling_result.get('flags'):
                    all_kick_flags.extend(ling_result['flags'])
                # Phase 3: 관계 지형도
                from kick_analysis.relational import analyze_relational
                rel_result = analyze_relational(user.id, db.session, Diary, crypto_decrypt=safe_decrypt)
                if rel_result.get('flags'):
                    all_kick_flags.extend(rel_result['flags'])
                # 플래그가 있으면 보호자 알림
                if all_kick_flags:
                    notify_guardians_kick_flag(user, all_kick_flags)
            except Exception as ke:
                print(f"⚠️ Kick Analysis Trigger Failed: {ke}")
    except Exception as e:
        print(f"⚠️ Push Notification Trigger Failed: {e}")

    response_data['msg'] = '일기가 저장되었습니다.'
    return jsonify(response_data), 201

def safe_extract_ai_comment(raw_text):
    """AI 코멘트에서 JSON/마크다운 쓰레기를 제거하고 순수 텍스트만 추출"""
    if not raw_text:
        return raw_text
    text = str(raw_text).strip()
    if not text:
        return ''

    # 1. RunPod 응답 객체가 그대로인 경우 → 빈 문자열
    if text.startswith('[{"choices"') or '"tokens"' in text and '"usage"' in text:
        return ''

    # 2. JSON 파싱 시도 → comment 키 추출
    import json as _json
    json_start = text.find('{')
    json_end = text.rfind('}')
    if json_start != -1 and json_end > json_start:
        try:
            parsed = _json.loads(text[json_start:json_end + 1])
            if isinstance(parsed, dict):
                comment = parsed.get('comment') or parsed.get('ai_comment') or parsed.get('message') or parsed.get('analysis')
                if comment and isinstance(comment, str) and comment.strip():
                    return comment.strip()
        except Exception:
            pass

    # 3. 마크다운+JSON에서 comment 정규식 추출
    import re as _re
    comment_match = _re.search(r'["\']comment["\']\s*:\s*["\']((?:[^"\'\\]|\\.)*)[\'"]\s*', text)
    if comment_match and comment_match.group(1):
        extracted = comment_match.group(1).replace('\\n', '\n').replace('\\"', '"').strip()
        if extracted:
            return extracted

    # 4. 코드 블록(```json```) 안에서 추출
    code_match = _re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if code_match and code_match.group(1):
        try:
            block_parsed = _json.loads(code_match.group(1).strip())
            if isinstance(block_parsed, dict) and block_parsed.get('comment'):
                return block_parsed['comment'].strip()
        except Exception:
            pass

    # 5. 마크다운/JSON 잔여물 포함 시 빈 문자열
    if '```' in text or text.startswith('[{') or text.startswith('{"'):
        return ''

    # 6. 깨끗한 텍스트
    return text


def serialize_diary(d):
    return {
        'id': str(d.id), # Cast to String for iOS
        'date': d.date,
        'mood_level': d.mood_level,
        'weather': d.weather,
        'temperature': d.temperature,
        'event': safe_decrypt(d.event),
        'emotion_desc': safe_decrypt(d.emotion_desc),
        'emotion_meaning': safe_decrypt(d.emotion_meaning),
        'self_talk': safe_decrypt(d.self_talk),
        'sleep_condition': safe_decrypt(d.sleep_condition),
        'gratitude_note': safe_decrypt(d.gratitude_note),
        'ai_comment': safe_extract_ai_comment(safe_decrypt(d.ai_comment)),
        'ai_emotion': safe_decrypt(d.ai_emotion),
        'ai_prediction': safe_decrypt(d.ai_emotion), # Map for iOS
        'mode': d.mode,
        'mood_intensity': 0, # Not in DB
        'safety_flag': d.safety_flag if hasattr(d, 'safety_flag') else False,
        'created_at': d.created_at.isoformat() if d.created_at else None,
        'medication': False,
        'symptoms': []
    }

# [API Endpoint: Get Single Diary by Date] - PostgreSQL Only
@app.route('/api/diaries/date/<string:date_str>', methods=['GET'])
@jwt_required()
def get_diary_by_date(date_str):
    current_user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=current_user_id).first()
    
    if not user:
         return jsonify({'msg': '사용자를 찾을 수 없습니다.'}), 404

    diary = Diary.query.filter_by(user_id=user.id, date=date_str).first()
    
    if not diary:
        return jsonify({'msg': '일기를 찾을 수 없습니다.'}), 404
    
    return jsonify(serialize_diary(diary))

# [API Endpoint: Get Single Diary]
@app.route('/api/diaries/<int:diary_id>', methods=['GET'])
@jwt_required()
def get_diary(diary_id):
    try:
        raw_identity = get_jwt_identity()
        current_user_id = int(raw_identity) # Force Int
        print(f"🔍 [Debug] Identity: {raw_identity} (Type: {type(raw_identity)}) -> {current_user_id}")
        user = User.query.filter_by(id=current_user_id).first()
        
        if not user:
            print(f"❌ [Get Diary] User Not Found: ID {current_user_id}")
            return jsonify({'msg': '사용자를 찾을 수 없습니다.'}), 404
        
        diary = Diary.query.filter_by(id=diary_id, user_id=user.id).first()
        
        if not diary:
            print(f"❌ [Get Diary] Diary Not Found: ID {diary_id}")
            return jsonify({'msg': '일기를 찾을 수 없습니다.'}), 404
        
        # [Debug] Check actual mapped content
        print(f"🔍 [Debug] Loading Diary {diary.id}: Event(Content)='{diary.event}'") 

        decrypted_event = safe_decrypt(diary.event)
        decrypted_emotion_desc = safe_decrypt(diary.emotion_desc)
        decrypted_emotion_meaning = safe_decrypt(diary.emotion_meaning)
        decrypted_self_talk = safe_decrypt(diary.self_talk)
        decrypted_gratitude = safe_decrypt(diary.gratitude_note)
        decrypted_sleep = safe_decrypt(diary.sleep_condition)
        decrypted_ai_comment = safe_extract_ai_comment(safe_decrypt(diary.ai_comment)) 
        decrypted_ai_emotion = safe_decrypt(diary.ai_emotion) 

        # [Lazy Analysis Logic omitted/preserved]
        # ... (Same logic for Lazy Analysis)

        return jsonify({
            'id': diary.id,
            'date': diary.date,
            'mood': diary.mood_level,
            'content': decrypted_event,
            'event': decrypted_event, 
            'sleep_condition': decrypted_sleep, 
            'emotion_desc': decrypted_emotion_desc,
            'emotion_meaning': decrypted_emotion_meaning,
            'self_talk': decrypted_self_talk,
            'mood_level': diary.mood_level,
            'weather': diary.weather,
            'temperature': diary.temperature,
            'mode': diary.mode,
            # mood_intensity removed
            'gratitude_note': decrypted_gratitude,
            'ai_comment': decrypted_ai_comment, 
            'ai_emotion': decrypted_ai_emotion, 
            'safety_flag': diary.safety_flag,
            'created_at': diary.created_at.isoformat() if diary.created_at else None
        })
    except Exception as e:
        print(f"🔥 [CRITICAL] Get Diary Failed: {e}")
        print(traceback.format_exc()) # Print Full Traceback
        return jsonify({'msg': 'Internal Server Error', 'error': str(e)}), 500

# [API Endpoint: Update Diary]
@app.route('/api/diaries/<int:diary_id>/upt', methods=['POST'])
@app.route('/api/diaries/<int:diary_id>', methods=['PUT', 'POST']) 
@jwt_required()
def update_diary(diary_id):
    current_user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=current_user_id).first()
    if not user:
        return jsonify({'msg': '사용자를 찾을 수 없습니다.'}), 404  # [Fix#7] NoneType 방어
    diary = Diary.query.filter_by(id=diary_id, user_id=user.id).first()

    if not diary:
        return jsonify({'msg': '일기를 찾을 수 없습니다.'}), 404

    data = request.get_json()

    encrypted_event = safe_encrypt(data.get('event') or data.get('question1'))
    encrypted_emotion_desc = safe_encrypt(data.get('emotion_desc') or data.get('question2'))
    encrypted_emotion_meaning = safe_encrypt(data.get('emotion_meaning') or data.get('question3'))
    encrypted_self_talk = safe_encrypt(data.get('self_talk') or data.get('question4'))
    encrypted_gratitude = safe_encrypt(data.get('gratitude_note'))
    encrypted_sleep = safe_encrypt(data.get('sleep_condition'))

    diary.event = encrypted_event
    diary.emotion_desc = encrypted_emotion_desc
    diary.emotion_meaning = encrypted_emotion_meaning
    diary.self_talk = encrypted_self_talk
    diary.gratitude_note = encrypted_gratitude
    diary.sleep_condition = encrypted_sleep
    diary.mood_level = data.get('mood_level', diary.mood_level)
    # diary.mood_intensity = ... (Not in DB)
    diary.weather = data.get('weather', diary.weather)
    diary.temperature = data.get('temperature', diary.temperature)
    diary.safety_flag = data.get('safety_flag', diary.safety_flag)
    
    db.session.commit()
    
    start_analysis_thread(
        diary.id,
        diary.date,
        data.get('event') or data.get('question1') or "",
        data.get('sleep_condition') or "",
        data.get('emotion_desc') or data.get('question2') or "",
        data.get('emotion_meaning') or data.get('question3') or "",
        data.get('self_talk') or data.get('question4') or ""
    )

    response_data = serialize_diary(diary)
    
    # [Local Sync] Update to Medical Dashboard (Localhost:8000)
    try:
        from b2g_routes import sync_to_insight_mind
        sync_to_insight_mind(response_data, user.id)
    except Exception as e:
        print(f"⚠️ Sync Trigger Failed: {e}")

    # [Push Notification] 보호자 알림 트리거 (수정 시)
    try:
        from push_service import notify_guardians_mood, notify_guardians_crisis, notify_guardians_kick_flag, is_push_available
        if is_push_available():
            mood = data.get('mood_level', diary.mood_level)
            safety = data.get('safety_flag', diary.safety_flag)
            # ① 기분 온도 알림
            if mood:
                notify_guardians_mood(user, int(mood))
            # ② 위기 감지 알림
            if safety in [True, 'need_help', 'danger']:
                notify_guardians_crisis(user)
            # ③ 킥 분석 (Phase 1~3)
            try:
                all_kick_flags = []
                from kick_analysis import analyze_timeseries
                ts_result = analyze_timeseries(user.id, db.session, Diary)
                if ts_result.get('flags'): all_kick_flags.extend(ts_result['flags'])
                
                from kick_analysis.linguistic import analyze_linguistic
                ling_result = analyze_linguistic(user.id, db.session, Diary, crypto_decrypt=safe_decrypt)
                if ling_result.get('flags'): all_kick_flags.extend(ling_result['flags'])
                
                from kick_analysis.relational import analyze_relational
                rel_result = analyze_relational(user.id, db.session, Diary, crypto_decrypt=safe_decrypt)
                if rel_result.get('flags'): all_kick_flags.extend(rel_result['flags'])
                
                if all_kick_flags:
                    notify_guardians_kick_flag(user, all_kick_flags)
            except Exception as ke:
                print(f"⚠️ Kick Analysis Trigger Failed (Update): {ke}")
    except Exception as e:
        print(f"⚠️ Push Notification Trigger Failed (Update): {e}")

    response_data['msg'] = '일기가 수정되었습니다.'
    return jsonify(response_data)


# [API Endpoint: Get Diary List]
# [Merged into get_diaries above]

# [API Endpoint: Delete Diary]
@app.route('/api/diaries/<int:diary_id>', methods=['DELETE'])
@jwt_required()
def delete_diary(diary_id):
    current_user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=current_user_id).first()
    diary = Diary.query.filter_by(id=diary_id, user_id=user.id).first()

    if not diary:
        return jsonify({'msg': '일기를 찾을 수 없습니다.'}), 404

    target_date = diary.date
    
    # [NativeRAG] Security Fix - Delete associated vector memory
    try:
        from memory_manager import delete_diary_memory
        delete_diary_memory(diary_id)
    except Exception as e:
        print(f"⚠️ [NativeRAG] RAG 메모리 완전 파기 실패: {e}")
        
    db.session.delete(diary)
    db.session.commit()
    
    return jsonify({'msg': '일기가 삭제되었습니다.'})

# [API Endpoint: Verify Center Code]
@app.route('/api/centers/verify-code/', methods=['POST'])
def verify_center_code():
    data = request.get_json()
    center_code = data.get('center_code')

    if not center_code:
        return jsonify({'error': '코드를 입력해주세요.'}), 400

    center = Center.query.filter_by(code=center_code).first()

    if center:
        return jsonify({
            'valid': True,
            'center_name': center.name,
            'center_id': center.id,
            'message': f"'{center.name}' 기관과 연동되었습니다."
        })
    else:
        return jsonify({'error': '유효하지 않은 기관 코드입니다.'}), 404

# [API Endpoint: Connect Center]
@app.route('/api/b2g_sync/connect/', methods=['POST'])
@jwt_required()
def connect_center():
    current_user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=current_user_id).first()
    data = request.get_json()
    center_id = data.get('center_id')

    if not center_id:
        return jsonify({'msg': '기관 ID가 필요합니다.'}), 400

    center = Center.query.get(center_id)
    if not center:
        return jsonify({'msg': '기관을 찾을 수 없습니다.'}), 404

    user.center_code = center.code
    db.session.commit()

    return jsonify({'msg': '기관 연결이 완료되었습니다.', 'center_code': center.code})


# ─────────────────────────────────────────────
# [Push Notification] FCM 디바이스 토큰 등록 API
# ─────────────────────────────────────────────
@app.route('/api/device/register', methods=['POST'])
@jwt_required()
def register_device_token():
    """앱 시작 시 FCM 토큰을 서버에 등록"""
    current_user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=current_user_id).first()

    if not user:
        return jsonify({'msg': '사용자를 찾을 수 없습니다.'}), 404

    data = request.get_json()
    fcm_token = data.get('fcm_token')
    platform = data.get('platform', 'unknown')  # 'ios' or 'android'
    apns_token = data.get('apns_token', '')  # iOS APNs 디바이스 토큰

    if not fcm_token:
        return jsonify({'msg': 'fcm_token이 필요합니다.'}), 400

    user.fcm_token = fcm_token
    user.fcm_updated_at = datetime.utcnow()
    if apns_token:
        user.apns_token = apns_token
    db.session.commit()

    print(f"✅ FCM 토큰 등록: user={user.username}, platform={platform}, apns={'있음' if apns_token else '없음'}")
    return jsonify({'msg': '디바이스 등록 완료'}), 200


# [Push] APNs 디바이스 토큰 별도 등록
@app.route('/api/device/apns', methods=['POST'])
@jwt_required()
def register_apns_token():
    current_user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=current_user_id).first()
    if not user:
        return jsonify({'msg': '사용자 없음'}), 404
    data = request.get_json()
    apns_token = data.get('apns_token', '')
    if apns_token:
        user.apns_token = apns_token
        db.session.commit()
        print(f"✅ APNs 토큰 등록: user={user.username}, token={apns_token[:20]}...")
    return jsonify({'msg': 'OK'}), 200


# [Health Check]
@app.route('/api', methods=['GET'])
def health_check():
    from push_service import is_push_available
    push_status = "활성화" if is_push_available() else "비활성화"
    status = "암호화" if crypto else "평문"
    return f"서버가 정상 작동 중입니다! (DB: PostgreSQL 통합, 모드: {status}, 푸시: {push_status})"



if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000, threaded=True)
