from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from config import Config
from models import db, User, Diary, ChatLog, Center
import os
from crypto_utils import EncryptionManager
from analysis_worker import start_analysis_thread # [New] Background Worker for PG

app = Flask(__name__)

# [PostgreSQL Integration]
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://vibe_user:vibe1234@127.0.0.1/vibe_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY

# [MongoDB Integration]
app.config['MONGO_URI'] = Config.MONGO_URI or "mongodb://localhost:27017/maumon_db" 
# Ensure Config.MONGO_URI is defined or fallback

# Initialize DB (Postgres)
db.init_app(app)

# Initialize MongoDB
mongo = PyMongo(app)

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


@app.before_request
def log_request_info():
    print(f"📡 [Global] Request: {request.method} {request.url}")
    if request.method in ['PUT', 'POST']:
        pass

jwt = JWTManager(app)

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
    current_username = get_jwt_identity()
    return jsonify({"valid": True, "username": current_username}), 200

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
        user_id=username, # Legacy mapping
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
         # Try finding by center linkage if needed? No.
         return jsonify({'msg': '아이디 또는 비밀번호가 올바르지 않습니다.'}), 401
         
    if not check_password_hash(user.password, password):
        return jsonify({'msg': '아이디 또는 비밀번호가 올바르지 않습니다.'}), 401

    access_token = create_access_token(identity=username)
    
    # [B2G] Sync Center Code if provided on login
    real_center_code = user.center_code
    
    # [Mongo Sync Check]
    # Check if user exists in Mongo too?
    # medication_routes depends on Mongo user document.
    linked_code_mongo = None
    try:
        mongo_user = mongo.db.users.find_one({"username": username})
        if mongo_user and mongo_user.get('linked_center_code'):
             linked_code_mongo = mongo_user.get('linked_center_code')
    except:
        pass

    return jsonify({
        'access_token': access_token,
        'username': user.username,
        'center_code': user.center_code, # Postgres
        'linked_center_code': linked_code_mongo, # Mongo (B2G Priority)
        'role': user.role
    })

# [API Endpoint: User Profile]
@app.route('/api/user/me', methods=['GET'])
@jwt_required()
def get_me():
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return jsonify({'msg': '사용자를 찾을 수 없습니다.'}), 404
        
    # Sync with Mongo
    linked_code_mongo = None
    try:
        mongo_user = mongo.db.users.find_one({"username": current_username})
        if mongo_user:
            linked_code_mongo = mongo_user.get('linked_center_code')
    except:
        pass

    return jsonify({
        'username': user.username,
        'center_code': user.center_code,
        'linked_center_code': linked_code_mongo, # Include Mongo linkage
        'role': user.role,
        'is_premium': (user.role == 'premium' or user.role == 'admin')
    })
    
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

# [API Endpoint: Get Diaries]
@app.route('/api/diaries', methods=['GET'])
@jwt_required()
def get_diaries():
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    year = request.args.get('year')
    month = request.args.get('month')

    query = Diary.query.filter_by(user_id=user.id)

    if year and month:
        start_date = f"{year}-{month}-01"
        # Determine end date logic omitted for brevity, Assuming query string is YYYY, MM
        # Simplified: Just filter within month
        # In real world, use proper date range
        pass # To be fully implemented if needed for PG-only mode

    # If backend runs in Hybrid mode (PG + Mongo), we usually rely on Mongo diaries for App compatibility.
    # But if frontend calls THIS endpoint, it gets PG diaries.
    # Frontend usually calls /api/diaries without id for calendar list?
    # No, App uses Mongo routes. Web uses Mongo routes.
    # This route might be legacy or admin console specific.
    diaries = query.all()
    result = [serialize_diary(d) for d in diaries]
    return jsonify(result)

# [API Endpoint: Create Diary]
@app.route('/api/diaries', methods=['POST'])
@jwt_required()
def create_diary():
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    data = request.get_json()

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
        date=data.get('date', datetime.now().strftime('%Y-%m-%d')),
        event=encrypted_event, # Encrypted
        sleep_condition=encrypted_sleep, # Encrypted
        emotion_desc=encrypted_emotion_desc, # Encrypted
        emotion_meaning=encrypted_emotion_meaning, # Encrypted
        self_talk=encrypted_self_talk, # Encrypted
        mood_level=data.get('mood_level', 3),
        weather=data.get('weather'),
        temperature=data.get('temperature'),
        mode=data.get('mode', 'green'), # Default
        mood_intensity=data.get('mood_intensity', 0),
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
    response_data['msg'] = '일기가 저장되었습니다.'
    return jsonify(response_data), 201

def serialize_diary(d):
    return {
        'id': d.id,
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
        'mode': d.mode,
        'mood_intensity': d.mood_intensity,
        'safety_flag': d.safety_flag,
        'created_at': d.created_at.isoformat() if d.created_at else None
    }

# [API Endpoint: Get Single Diary]
@app.route('/api/diaries/<int:diary_id>', methods=['GET'])
@jwt_required()
def get_diary(diary_id):
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    diary = Diary.query.filter_by(id=diary_id, user_id=user.id).first()
    
    if not diary:
        return jsonify({'msg': '일기를 찾을 수 없습니다.'}), 404
    
    decrypted_event = safe_decrypt(diary.event)
    decrypted_emotion_desc = safe_decrypt(diary.emotion_desc)
    decrypted_emotion_meaning = safe_decrypt(diary.emotion_meaning)
    decrypted_self_talk = safe_decrypt(diary.self_talk)
    decrypted_gratitude = safe_decrypt(diary.gratitude_note)
    decrypted_sleep = safe_decrypt(diary.sleep_condition)
    decrypted_ai_comment = safe_decrypt(diary.ai_comment) 
    decrypted_ai_emotion = safe_decrypt(diary.ai_emotion) 
    
    # [Lazy Analysis] If AI comment is missing, trigger analysis now
    if not decrypted_ai_comment or decrypted_ai_comment.strip() == "":
        try:
            start_analysis_thread(
                diary.id,
                diary.date, 
                decrypted_event or "", 
                decrypted_sleep or "", 
                decrypted_emotion_desc or "", 
                decrypted_emotion_meaning or "", 
                decrypted_self_talk or ""
            )
            decrypted_ai_comment = "AI 심리 상담사가 당신의 하루를 읽고 있어요... (잠시 후 다시 열어주세요)"
            decrypted_ai_emotion = "분석중"
            print(f"🔥 Lazy Analysis Triggered for Diary {diary.id}")
        except Exception as e:
            print(f"⚠️ Lazy Analysis Failed: {e}")

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
        'mood_intensity': diary.mood_intensity,
        'gratitude_note': decrypted_gratitude,
        'ai_comment': decrypted_ai_comment, 
        'ai_emotion': decrypted_ai_emotion, 
        'safety_flag': diary.safety_flag,
        'created_at': diary.created_at.isoformat() if diary.created_at else None
    })

# [API Endpoint: Update Diary]
@app.route('/api/diaries/<int:diary_id>/upt', methods=['POST'])
@app.route('/api/diaries/<int:diary_id>', methods=['PUT', 'POST']) 
@jwt_required()
def update_diary(diary_id):
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
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
    diary.mood_intensity = data.get('mood_intensity', diary.mood_intensity)
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

# [API Endpoint: Delete Diary]
@app.route('/api/diaries/<int:diary_id>', methods=['DELETE'])
@jwt_required()
def delete_diary(diary_id):
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    diary = Diary.query.filter_by(id=diary_id, user_id=user.id).first()

    if not diary:
        return jsonify({'msg': '일기를 찾을 수 없습니다.'}), 404

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
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
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

# [Health Check]
@app.route('/api', methods=['GET'])
def health_check():
    status = "암호화" if crypto else "평문"
    return f"서버가 정상 작동 중입니다! (DB: PostgreSQL 통합, 모드: {status})"


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
