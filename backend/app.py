from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_migrate import Migrate
from config import Config
from models import db, User, Diary
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# CORS: Allow requests from frontend (127.0.0.1)
CORS(app, resources={r"/api/*": {"origins": "*"}})

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

@app.route('/api/diaries', methods=['GET'])
@jwt_required()
def get_diaries():
    current_user_id = get_jwt_identity()
    diaries = Diary.query.filter_by(user_id=current_user_id).order_by(Diary.created_at.desc()).all()
    return jsonify([d.to_dict() for d in diaries]), 200

@app.route('/api/diaries', methods=['POST'])
@jwt_required()
def create_diary():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    print(f"DEBUG: create_diary received: {data}")
    
    created_at_str = data.get('created_at')
    print(f"DEBUG: created_at_str: {created_at_str}")

    # Handle ISO string from JS (e.g. 2026-01-10T09:00:00.000Z). Python 3.7+ supports fromisoformat, but Z might need handling if < 3.11
    # Simple workaround: if it ends with Z, replace with +00:00
    if created_at_str and created_at_str.endswith('Z'):
        created_at_str = created_at_str[:-1] + '+00:00'
        
    created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.utcnow()
    print(f"DEBUG: Parsed created_at: {created_at}")

    new_diary = Diary(
        user_id=current_user_id,
        event=data['event'],
        emotion_desc=data['emotion_desc'],
        emotion_meaning=data['emotion_meaning'],
        self_talk=data['self_talk'],
        mood_level=data['mood_level'],
        created_at=created_at
    )
    
    db.session.add(new_diary)
    db.session.commit()
    
    return jsonify(new_diary.to_dict()), 201

@app.route('/api/diaries/<int:id>', methods=['PUT'])
@jwt_required()
def update_diary(id):
    current_user_id = get_jwt_identity()
    diary = Diary.query.get_or_404(id)

    # Ensure the diary belongs to the current user
    # Note: identity is string in token, user_id in DB is int usually, but let's check model.
    # casting current_user_id to int is safer if model uses int.
    if int(diary.user_id) != int(current_user_id):
         return jsonify({"message": "Permission denied"}), 403

    data = request.get_json()
    
    diary.event = data.get('event', diary.event)
    diary.emotion_desc = data.get('emotion_desc', diary.emotion_desc)
    diary.emotion_meaning = data.get('emotion_meaning', diary.emotion_meaning)
    diary.self_talk = data.get('self_talk', diary.self_talk)
    diary.mood_level = data.get('mood_level', diary.mood_level)
    
    db.session.commit()
    return jsonify(diary.to_dict()), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)

