from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_migrate import Migrate
from config import Config
from models import db, User, Diary
from ai_analysis import ai_analyzer

from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# CORS: Allow requests from frontend with full credentials support
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# -------------------- Auth Routes --------------------

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username already exists"}), 400

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=str(user.id)) # Use ID as identity
        return jsonify(access_token=access_token, username=user.username), 200

    return jsonify({"message": "Invalid credentials"}), 401

# -------------------- Diary Routes --------------------

from sqlalchemy import extract

@app.route('/api/diaries', methods=['GET'])
@jwt_required()
def get_diaries():
    current_user_id = get_jwt_identity()
    
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    query = Diary.query.filter_by(user_id=current_user_id)
    
    if year and month:
        query = query.filter(extract('year', Diary.created_at) == year,
                             extract('month', Diary.created_at) == month)
    
    # order_by를 limit 전에 호출해야 함
    query = query.order_by(Diary.created_at.desc())
    
    # 필터가 없으면 최근 100개만 반환
    if not (year and month):
        query = query.limit(100)
                             
    diaries = query.all()
    return jsonify([d.to_dict() for d in diaries]), 200

@app.route('/api/diaries', methods=['POST'])
@jwt_required()
def create_diary():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    created_at_str = data.get('created_at')

    # Handle ISO string from JS (e.g. 2026-01-10T09:00:00.000Z). Python 3.7+ supports fromisoformat, but Z might need handling if < 3.11
    # Simple workaround: if it ends with Z, replace with +00:00
    if created_at_str and created_at_str.endswith('Z'):
        created_at_str = created_at_str[:-1] + '+00:00'
        
    created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.utcnow()

    # Combine event and emotion_desc for comprehensive analysis
    # Combine event and emotion_desc for comprehensive analysis
    combined_text = f"{data['event']} {data['emotion_desc']}"
    ai_result = ai_analyzer.predict(combined_text)
    
    # Pass structured context for better AI generation
    context_data = {
        "event": data['event'],
        "emotion": data['emotion_desc'],
        "self_talk": data['emotion_meaning'] # Q3 (Deep Reflection) is more relevant for analysis than Q4 (Self Comfort)
    }
    ai_comment_text = ai_analyzer.generate_comment(ai_result, context_data)
    
    new_diary = Diary(
        user_id=current_user_id,
        event=data['event'],
        emotion_desc=data['emotion_desc'],
        emotion_meaning=data['emotion_meaning'],
        self_talk=data['self_talk'],
        mood_level=data['mood_level'],
        ai_prediction=ai_result,
        ai_comment=ai_comment_text,
        created_at=created_at
    )
    
    db.session.add(new_diary)
    db.session.commit()
    
    # Trigger AI Learning from this entry
    # We use the user's provided mood_level (Ground Truth) to teach the AI
    try:
        ai_analyzer.update_keywords(combined_text, data['mood_level'])
    except Exception as e:
        print(f"AI Learning failed: {e}")
    
    return jsonify(new_diary.to_dict()), 201

# 개별 일기 조회
@app.route('/api/diaries/<int:id>', methods=['GET'])
@jwt_required()
def get_diary(id):
    current_user_id = get_jwt_identity()
    diary = Diary.query.get_or_404(id)
    
    # 다른 사용자의 일기는 조회 불가
    if diary.user_id != int(current_user_id):
        return jsonify({"message": "Unauthorized"}), 403
    
    return jsonify(diary.to_dict()), 200

# 일기 수정
@app.route('/api/diaries/<int:id>', methods=['PUT'])
@jwt_required()
def update_diary(id):
    current_user_id = get_jwt_identity()
    diary = Diary.query.get_or_404(id)
    
    # 다른 사용자의 일기는 수정 불가
    if diary.user_id != int(current_user_id):
        return jsonify({"message": "Unauthorized"}), 403
    
    data = request.get_json()
    
    diary.event = data.get('event', diary.event)
    diary.emotion_desc = data.get('emotion_desc', diary.emotion_desc)
    diary.emotion_meaning = data.get('emotion_meaning', diary.emotion_meaning)
    diary.self_talk = data.get('self_talk', diary.self_talk)
    diary.mood_level = data.get('mood_level', diary.mood_level)
    
    # 일기 수정 시 감정 다시 분석
    combined_text = f"{diary.event} {diary.emotion_desc}"
    diary.ai_prediction = ai_analyzer.predict(combined_text)
    diary.ai_comment = ai_analyzer.generate_comment(diary.ai_prediction)
    
    db.session.commit()
    return jsonify(diary.to_dict()), 200

# 일기 삭제
@app.route('/api/diaries/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_diary(id):
    current_user_id = get_jwt_identity()
    diary = Diary.query.get_or_404(id)
    
    # 다른 사용자의 일기는 삭제 불가
    if diary.user_id != int(current_user_id):
        return jsonify({"message": "Unauthorized"}), 403
    
    db.session.delete(diary)
    db.session.commit()
    return jsonify({"message": "Diary deleted successfully"}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)

