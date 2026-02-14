from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from config import Config
from models import db, User, Diary, ChatLog
import os

app = Flask(__name__)

# [PostgreSQL Integration]
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://vibe_user:vibe1234@127.0.0.1/vibe_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY

# Initialize DB
db.init_app(app)

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

jwt = JWTManager(app)

# [API Endpoint: Register]
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(username=username).first():
        return jsonify({'msg': 'User already exists'}), 400

    new_user = User(username=username, password=password) # Hash password in production!
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'msg': 'User created successfully'}), 201

# [API Endpoint: Login]
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if not user or user.password != password:
        return jsonify({'msg': 'Bad username or password'}), 401

    access_token = create_access_token(identity={'username': username, 'id': user.id})
    return jsonify(access_token=access_token)

# [API Endpoint: User Profile]
@app.route('/api/user/me', methods=['GET'])
@jwt_required()
def get_me():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user['username']).first()
    
    if not user:
        return jsonify({'msg': 'User not found'}), 404
        
    return jsonify({
        'username': user.username,
        'center_code': user.center_code,
        'role': user.role
    })

# [API Endpoint: Get Diaries]
@app.route('/api/diaries', methods=['GET'])
@jwt_required()
def get_diaries():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user['username']).first()
    year = request.args.get('year')
    month = request.args.get('month')

    query = Diary.query.filter_by(user_id=user.id)

    if year and month:
        search_date = f"{year}-{int(month):02d}"
        query = query.filter(Diary.date.like(f"{search_date}%"))

    diaries = query.all()
    
    result = []
    for d in diaries:
        result.append({
            'id': d.id,
            'date': d.date,
            'mood': d.mood_level, 
            'content': d.event,
            'emotion_desc': d.emotion_desc
        })

    return jsonify(result)

# [API Endpoint: Create Diary]
@app.route('/api/diaries', methods=['POST'])
@jwt_required()
def create_diary():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user['username']).first()
    data = request.get_json()

    new_diary = Diary(
        user_id=user.id,
        date=data.get('created_at', datetime.now().strftime('%Y-%m-%d')),
        event=data.get('event'),
        sleep_condition=data.get('sleep_condition'),
        emotion_desc=data.get('emotion_desc'),
        emotion_meaning=data.get('emotion_meaning'),
        self_talk=data.get('self_talk'),
        mood_level=data.get('mood_level', 3),
        weather=data.get('weather'),
        temperature=data.get('temperature')
    )
    
    db.session.add(new_diary)
    db.session.commit()

    return jsonify({'msg': 'Diary created successfully', 'id': new_diary.id}), 201

# [Health Check]
@app.route('/', methods=['GET'])
def health_check():
    return "Vibe Coding Backend is Running! (PostgreSQL Integrated)"

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
