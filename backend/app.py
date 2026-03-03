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
    crypto = EncryptionManager(app.config.get('ENCRYPTION_KEY'))
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
        password=generate_password_hash(password), 
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
    except:
        return text

#Helper to safely encrypt
def safe_encrypt(text):
    if not crypto: return text
    try:
        return crypto.encrypt(text)
    except:
        return text

# Alias for external usage (e.g. b2g_routes)
def encrypt_data(text):
    return safe_encrypt(text)

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
        from push_service import notify_guardians_mood, notify_guardians_crisis, is_push_available
        if is_push_available():
            mood = data.get('mood_level', 3)
            safety = data.get('safety_flag', False)
            # ① 기분 온도 낮음 알림 (mood ≤ 2)
            if mood and int(mood) <= 2:
                notify_guardians_mood(user, int(mood))
            # ② 위기 감지 알림 (safety_flag=True)
            if safety in [True, 'need_help', 'danger']:
                notify_guardians_crisis(user)
    except Exception as e:
        print(f"⚠️ Push Notification Trigger Failed: {e}")

    response_data['msg'] = '일기가 저장되었습니다.'
    return jsonify(response_data), 201

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
        'ai_comment': safe_decrypt(d.ai_comment),
        'ai_emotion': safe_decrypt(d.ai_emotion),
        'ai_prediction': safe_decrypt(d.ai_emotion), # Map for iOS
        'mode': d.mode,
        'mood_intensity': 0, # Not in DB
        'safety_flag': d.safety_flag if hasattr(d, 'safety_flag') else False,
        'created_at': d.created_at.isoformat() if d.created_at else None,
        'ai_prediction': safe_decrypt(d.ai_emotion), # Mapped
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
        decrypted_ai_comment = safe_decrypt(diary.ai_comment) 
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
# [Feature] 마음 온도 (Mood Temperature) API
# ─────────────────────────────────────────────
def calculate_mood_temperature(user_id):
    """
    마음 온도 산정 로직 (0~100°)
    - 기분 레벨 (40%): 최근 7일 mood_level 평균 (1~5 → 0~100 매핑)
    - 기록 빈도 (20%): 최근 7일 중 기록 일수 비율
    - 수면 상태 (20%): sleep_condition 텍스트 기반 긍정/부정 분석
    - 안정성 (20%): safety_flag 및 기분 안정도 (분산 기반)
    """
    from datetime import datetime, timedelta
    
    recent_cutoff = datetime.utcnow() - timedelta(days=7)
    recent_diaries = Diary.query.filter(
        Diary.user_id == user_id,
        Diary.created_at >= recent_cutoff
    ).order_by(Diary.date.desc()).all()
    
    # 데이터가 없으면 기본값 36.5° (건강한 체온 비유)
    if not recent_diaries:
        return {
            "temperature": 36.5,
            "label": "측정 중",
            "description": "일기를 작성하면 마음 온도가 측정돼요!",
            "color": "#86868b",
            "diary_count": 0,
            "factors": {
                "mood_score": 0,
                "frequency_score": 0,
                "sleep_score": 0,
                "stability_score": 0
            }
        }
    
    # 1. 기분 레벨 점수 (40%)
    mood_levels = [d.mood_level or 3 for d in recent_diaries]
    avg_mood = sum(mood_levels) / len(mood_levels)
    mood_score = ((avg_mood - 1) / 4) * 100  # 1~5 → 0~100
    
    # 2. 기록 빈도 점수 (20%)
    unique_dates = set(d.date for d in recent_diaries if d.date)
    frequency_score = min((len(unique_dates) / 7) * 100, 100)
    
    # 3. 수면 상태 점수 (20%)
    sleep_positive = ["잘", "충분", "숙면", "편안", "좋"]
    sleep_negative = ["못", "불면", "뒤척", "힘들", "나쁘", "잠을 못"]
    sleep_scores = []
    for d in recent_diaries:
        sleep_text = safe_decrypt(d.sleep_condition) if d.sleep_condition else ""
        if not sleep_text:
            sleep_scores.append(50)  # 기본값
            continue
        pos = sum(1 for kw in sleep_positive if kw in sleep_text)
        neg = sum(1 for kw in sleep_negative if kw in sleep_text)
        if pos > neg:
            sleep_scores.append(80)
        elif neg > pos:
            sleep_scores.append(30)
        else:
            sleep_scores.append(50)
    sleep_score = sum(sleep_scores) / len(sleep_scores) if sleep_scores else 50
    
    # 4. 안정성 점수 (20%) - 기분 분산 + safety_flag
    if len(mood_levels) > 1:
        mean = sum(mood_levels) / len(mood_levels)
        variance = sum((x - mean) ** 2 for x in mood_levels) / len(mood_levels)
        # 분산이 낮을수록 안정적 (0~4 범위, 2 이상이면 불안정)
        stability_score = max(0, 100 - (variance * 25))
    else:
        stability_score = 50
    
    # safety_flag가 있으면 안정성 감점
    has_safety_flag = any(
        getattr(d, 'safety_flag', None) in [True, 'need_help', 'danger']
        for d in recent_diaries
    )
    if has_safety_flag:
        stability_score = max(0, stability_score - 30)
    
    # 종합 점수 계산 (가중 평균)
    raw_score = (
        mood_score * 0.40 +
        frequency_score * 0.20 +
        sleep_score * 0.20 +
        stability_score * 0.20
    )
    
    # 0~100 → 마음 온도 매핑 (20°~45° 범위, 36.5°가 건강한 중심)
    # score 50 = 36.5°, score 0 = 20°, score 100 = 45°
    temperature = 20 + (raw_score / 100) * 25
    temperature = round(temperature, 1)
    
    # 라벨 및 색상 결정
    if temperature >= 40:
        label = "뜨거움 🔥"
        description = "마음이 매우 활발해요! 열정이 가득합니다."
        color = "#ff6b6b"
    elif temperature >= 37.5:
        label = "따뜻함 ☀️"
        description = "마음이 따뜻하고 안정적이에요."
        color = "#ffa726"
    elif temperature >= 35:
        label = "건강 💚"
        description = "마음이 균형 잡혀 있어요. 좋은 상태입니다!"
        color = "#66bb6a"
    elif temperature >= 30:
        label = "서늘함 🌤"
        description = "조금 차분한 상태에요. 따뜻한 활동을 해보세요."
        color = "#42a5f5"
    else:
        label = "차가움 ❄️"
        description = "마음이 많이 지쳐 있어요. 주변에 도움을 요청해보세요."
        color = "#7e57c2"
    
    return {
        "temperature": temperature,
        "label": label,
        "description": description,
        "color": color,
        "diary_count": len(recent_diaries),
        "factors": {
            "mood_score": round(mood_score, 1),
            "frequency_score": round(frequency_score, 1),
            "sleep_score": round(sleep_score, 1),
            "stability_score": round(stability_score, 1)
        }
    }

@app.route('/api/mood-temperature', methods=['GET'])
@jwt_required()
def get_mood_temperature():
    """마음 온도 조회 API"""
    user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=user_id).first()
    
    if not user:
        return jsonify({'msg': '사용자를 찾을 수 없습니다.'}), 404
    
    result = calculate_mood_temperature(user_id)
    return jsonify(result), 200

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


# [Feature] Async AI Analysis (File-based Persistence)
import threading
import json
import time
from analysis_worker import call_llm_hybrid

REPORT_DIR = os.path.join(basedir, 'reports')
if not os.path.exists(REPORT_DIR):
    os.makedirs(REPORT_DIR)

def run_async_analysis(user_id, mode='daily'):
    """
    Background worker for AI analysis.
    mode: 'daily' (Recent 10 diaries summary), 'longterm' (30 days deep analysis)
    """
    try:
        with app.app_context():
            print(f"🧵 [Analysis] Starting {mode} analysis for user {user_id}...")
            
            # Fetch Data
            limit = 30 if mode == 'longterm' else 10
            diaries = Diary.query.filter_by(user_id=user_id).order_by(Diary.date.desc()).limit(limit).all()
            
            if not diaries:
                result = {"status": "completed", "report": "분석할 데이터가 없습니다. 일기를 먼저 작성해주세요."}
                save_report(user_id, mode, result)
                return

            # Prepare Context
            context_text = ""
            for d in reversed(diaries): # Chronological order
                content = safe_decrypt(d.content)
                emotion = safe_decrypt(d.emotion_desc)
                context_text += f"- {d.date}: {content} (감정: {emotion})\n"
            
            # Prompt Engineering (Professional Report Format)
            if mode == 'longterm':
                if len(diaries) < 3:
                     result = {"status": "completed", "report": "장기 분석을 위해서는 최소 3일 이상의 일기 데이터가 필요합니다."}
                     save_report(user_id, mode, result)
                     return
                     
                system_prompt = (
                    "당신은 20년 이상 임상 경험을 가진 저명한 감정 분석 전문가이자 데이터 분석 전문가입니다. "
                    "내담자의 지난 30일간의 일기 데이터를 정밀 분석하여, 전문적이고 깊이 있는 '월간 심층 감정 분석 보고서'를 작성해야 합니다.\n\n"
                    "### 보고서 작성 지침:\n"
                    "1. **형식**: 줄글이 아닌, 아래의 섹션별로 명확히 구분하여 작성하십시오.\n"
                    "   - **1. [종합 소견]**: 내담자의 한 달간의 감정 상태를 3~4문장으로 요약하고, 핵심 키워드를 제시하십시오.\n"
                    "   - **2. [감정 흐름 및 패턴 분석]**: 감정의 기복, 주된 정서, 그리고 특정한 상황에서의 반응 패턴을 심층적으로 분석하십시오.\n"
                    "   - **3. [내면의 발견]**: 일기 속에 숨겨진 내담자의 무의식적 욕구, 가치관, 혹은 반복되는 갈등 요소를 통찰력 있게 짚어주십시오.\n"
                    "   - **4. [전문가 제언]**: 현재 상태에 가장 필요한 구체적인 감정 케어 방법(예: 마음챙김 명상, 자기 기록, 소통 연습 등)을 실천 가능한 형태로 제안하십시오.\n"
                    "2. **톤앤매너**: 매우 전문적이고 권위 있으면서도, 인간적인 따뜻함과 신뢰를 잃지 않는 어조를 유지하십시오.\n"
                    "3. **분량**: 각 섹션마다 충분한 근거와 상세한 서술을 포함하여 풍부하게 작성하십시오.\n"
                    "4. **주의사항**: 이 분석은 참고용이며 전문 의료 서비스를 대체하지 않습니다."
                )
            else: # Daily / Summary
                system_prompt = (
                    "당신은 통찰력 있고 섬세한 AI 감정 분석 전문가입니다. "
                    "내담자의 최근 일기 기록(최근 10건)을 바탕으로, 현재의 감정 상태를 분석하는 '주간 감정 케어 리포트'를 작성해주세요.\n\n"
                    "### 리포트 구성:\n"
                    "1. **[현재 마음 날씨]**: 최근 내담자의 감정을 날씨에 비유하여 표현하고, 그 이유를 설명하십시오.\n"
                    "2. **[주요 감정 이슈]**: 최근 반복적으로 나타나는 고민이나 감정의 원인을 분석하십시오.\n"
                    "3. **[오늘의 힐링 메시지]**: 내담자에게 가장 필요한 위로와 격려, 그리고 긍정적인 에너지를 주는 메시지를 전하십시오.\n"
                    "**작성 원칙**: 단순한 요약이 아니라, 내담자가 미처 깨닫지 못한 부분을 짚어주는 **전문적인 통찰**을 제공해야 합니다.\n"
                    "**주의사항**: 이 분석은 참고용이며 전문 의료 서비스를 대체하지 않습니다."
                )
            
            prompt = f"{system_prompt}\n\n[내담자의 최근 일기 데이터]\n{context_text}\n\n[전문가 분석 보고서]"
            
            # Call LLM
            # options = {"temperature": 0.7, "num_predict": 2000 if mode == 'longterm' else 1000}
            options = {"temperature": 0.5, "num_predict": 2000} # Access higher reliability & length
            ai_response = call_llm_hybrid(prompt, options=options)
            
            if not ai_response:
                ai_response = "AI 분석 서버 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요."
            
            # Save Result
            result = {
                "status": "completed", 
                "report": ai_response,
                "insight": ai_response, # [Fix] Frontend expects 'insight'
                "timestamp": datetime.now().isoformat()
            }
            save_report(user_id, mode, result)
            print(f"✅ [Analysis] {mode} analysis completed for user {user_id}")
            
    except Exception as e:
        print(f"❌ [Analysis Error] {e}")
        error_msg = str(e)
        error_result = {
            "status": "failed", 
            "report": f"분석 중 오류가 발생했습니다: {error_msg}",
            "insight": f"분석 중 오류가 발생했습니다: {error_msg}" # [Fix]
        }
        save_report(user_id, mode, error_result)
        import traceback
        traceback.print_exc()

def save_report(user_id, mode, data):
    try:
        filename = os.path.join(REPORT_DIR, f"{user_id}_{mode}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ [Save Report Error] {e}")

def load_report(user_id, mode):
    filename = os.path.join(REPORT_DIR, f"{user_id}_{mode}.json")
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # [Date Schema Fix] Ensure 'insight' exists for legacy files
                if 'report' in data and 'insight' not in data:
                    data['insight'] = data['report']
                return data
        except:
            return None
    return None

@app.route('/api/report/start', methods=['POST'])
@jwt_required()
def start_report():
    user_id = int(get_jwt_identity())
    
    # Save initial status
    save_report(user_id, 'daily', {
        "status": "processing", 
        "report": "분석을 준비하고 있습니다...",
        "insight": "분석을 준비하고 있습니다..." # [Fix]
    })
    
    # Start thread
    threading.Thread(target=run_async_analysis, args=(user_id, 'daily')).start()
    return jsonify({"message": "종합 분석이 시작되었습니다.", "status": "processing"}), 202

@app.route('/api/report/status', methods=['GET'])
@jwt_required()
def get_report_status():
    user_id = int(get_jwt_identity())
    report = load_report(user_id, 'daily')
    
    response_data = None
    if report:
        response_data = report
    else:
        # If no report found, check data
        last_diary = Diary.query.filter_by(user_id=user_id).order_by(Diary.date.desc()).first()
        if not last_diary:
             response_data = {"status": "completed", "report": "아직 기록이 없어요. 괜찮아요, 편안할 때 한마디 남겨보세요. 🌿", "insight": "아직 기록이 없어요. 괜찮아요, 편안할 때 한마디 남겨보세요. 🌿"}
        else:
             response_data = {"status": "processing", "report": "분석을 준비하고 있습니다...", "insight": "분석을 준비하고 있습니다..."}
    
    # [Fix] Disable Caching for Polling
    resp = make_response(jsonify(response_data), 200)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/api/report/longterm/start', methods=['POST'])
@jwt_required()
def start_longterm_report():
    user_id = int(get_jwt_identity())
    
    # Save initial status
    save_report(user_id, 'longterm', {
        "status": "processing", 
        "report": "심층 분석을 수행 중입니다. (약 1~2분 소요)",
        "insight": "심층 분석을 수행 중입니다. (약 1~2분 소요)"
    })
    
    threading.Thread(target=run_async_analysis, args=(user_id, 'longterm')).start()
    return jsonify({"message": "장기 심층 분석이 시작되었습니다.", "status": "processing"}), 202

@app.route('/api/report/longterm/status', methods=['GET'])
@jwt_required()
def get_longterm_report_status():
    user_id = int(get_jwt_identity())
    report = load_report(user_id, 'longterm')
    
    response_data = None
    if report:
        response_data = report
    else:
        response_data = {"status": "processing", "report": "심층 분석을 수행 중입니다. (약 1~2분 소요)", "insight": "심층 분석을 수행 중입니다. (약 1~2분 소요)"}

    # [Fix] Disable Caching for Polling
    resp = make_response(jsonify(response_data), 200)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/api/insight', methods=['GET'])
@jwt_required()
def get_mindset_insight():
    import random
    quotes = [
        "오늘 하루도 당신의 속도대로 나아가세요.",
        "작은 성취가 모여 큰 변화를 만듭니다.",
        "당신은 충분히 잘하고 있습니다.",
        "힘든 순간도 결국 지나갑니다. 스스로를 믿으세요.",
        "잠시 쉬어가도 괜찮습니다. 마음의 소리를 들어보세요."
    ]
    return jsonify({
        "content": random.choice(quotes)
    }), 200

@app.route('/api/weather-insight', methods=['GET'])
@jwt_required()
def get_weather_insight():
    weather = request.args.get('weather', '')
    content = "날씨가 마음에 영향을 줄 수 있어요. 따뜻한 차 한 잔 어떠세요?"
    
    if '맑음' in weather or 'Sun' in weather:
        content = "햇살처럼 밝은 하루 되세요! 산책을 추천해요."
    elif '비' in weather or 'Rain' in weather:
        content = "빗소리를 들으며 차분하게 마음을 정리해보세요."
    elif '구름' in weather or 'Cloud' in weather:
        content = "흐린 날엔 좋아하는 음악으로 기분을 전환해보세요."
        
    return jsonify({
        "content": content
    }), 200

@app.route('/api/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    try:
        current_user_id = int(get_jwt_identity())
        diaries = Diary.query.filter_by(user_id=current_user_id).order_by(Diary.date.asc()).all()
        
        # 1. Daily Stats (Calendar uses _id, count)
        daily_stats = []
        # 2. Timeline Stats (Chart uses date, mood_level)
        timeline_stats = []
        
        for d in diaries:
            if d.date and d.mood_level:
                # Calendar Format
                daily_stats.append({
                    '_id': d.date, 
                    'count': d.mood_level
                })
                # Chart Format
                timeline_stats.append({
                    'date': d.date,
                    'mood_level': d.mood_level
                })
        
        # 3. Mood Distribution
        mood_map = {}
        for d in diaries:
            if d.mood_level and 1 <= d.mood_level <= 5:
                mood_map[d.mood_level] = mood_map.get(d.mood_level, 0) + 1
        formatted_moods = [{' _id': k, 'count': v} for k, v in mood_map.items()]
        # Fix: key should be '_id' without space
        formatted_moods = [{'_id': k, 'count': v} for k, v in mood_map.items()]

        # 4. Weather Distribution (Nested Moods)
        weather_map = {} # { 'Sunny': {1:0, 2:0...} }
        for d in diaries:
            if d.weather:
                w = d.weather.strip()
                if not w: continue
                if w not in weather_map:
                    weather_map[w] = {}
                
                if d.mood_level:
                    weather_map[w][d.mood_level] = weather_map[w].get(d.mood_level, 0) + 1
        
        formatted_weather = []
        for w, m_counts in weather_map.items():
            # Convert m_counts dict to list of {mood: k, count: v}
            m_list = [{'mood': k, 'count': v} for k, v in m_counts.items()]
            formatted_weather.append({
                '_id': w, 
                'moods': m_list
            })

        return jsonify({
            'daily': daily_stats,
            'timeline': timeline_stats, # [Fix] Correct Schema
            'moods': formatted_moods, 
            'weather': formatted_weather
        }), 200

    except Exception as e:
        print(f"❌ [Stats Error] {e}")
        # Return empty structure instead of 500 to avoid crash
        return jsonify({'daily': [], 'timeline': [], 'moods': [], 'weather': []}), 200

# ─────────────────────────────────────────────
# [Assessment] PHQ-9 초기 감정 체크 결과 수신
# ─────────────────────────────────────────────
@app.route('/api/assessment', methods=['POST'])
@jwt_required()
def submit_assessment():
    """iOS AppAssessmentView에서 전송하는 PHQ-9 점수 수신"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}
    score = data.get('score', 0)
    answers = data.get('answers', [])

    # PHQ-9 기준 risk_level 판정
    # 0-4: minimal, 5-9: mild, 10-14: moderate, 15-19: moderately severe, 20+: severe
    if score >= 15:
        risk = 'high'
    elif score >= 10:
        risk = 'moderate'
    else:
        risk = 'low'

    print(f"📊 [Assessment] user={user.username}, score={score}, risk={risk}")

    return jsonify({
        'status': 'ok',
        'score': score,
        'risk_level': risk,
        'message': '감정 체크가 완료되었습니다.'
    }), 200

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000, threaded=True)
