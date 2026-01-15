from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    diaries = db.relationship('Diary', backref='author', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Diary(db.Model):
    __tablename__ = 'diaries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 5-step Diary Fields
    event = db.Column(db.Text, nullable=False)           # 1. 사건 기록
    emotion_desc = db.Column(db.Text, nullable=False)    # 2. 감정 묘사
    emotion_meaning = db.Column(db.Text, nullable=False) # 3. 감정 탐색
    self_talk = db.Column(db.Text, nullable=False)       # 4. 자신에게 말해주기
    mood_level = db.Column(db.Integer, nullable=False)   # 5. 감정 5단계
    ai_prediction = db.Column(db.Text, nullable=True)    # AI 감정 분석 결과 (New)
    ai_comment = db.Column(db.Text, nullable=True)       # AI 코멘트 (New)
    
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'event': self.event,
            'emotion_desc': self.emotion_desc,
            'emotion_meaning': self.emotion_meaning,
            'self_talk': self.self_talk,
            'mood_level': self.mood_level,
            'ai_prediction': self.ai_prediction,
            'ai_comment': self.ai_comment,
            'created_at': self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')
        }

class EmotionKeyword(db.Model):
    __tablename__ = 'emotion_keywords'
    
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), unique=True, nullable=False)
    emotion_label = db.Column(db.Integer, nullable=False) # 0-4 matching our classes
    frequency = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)
