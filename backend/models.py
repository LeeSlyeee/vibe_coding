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
    diaries = db.relationship('Diary', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

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
    
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'event': self.event,
            'emotion_desc': self.emotion_desc,
            'emotion_meaning': self.emotion_meaning,
            'self_talk': self.self_talk,
            'mood_level': self.mood_level,
            'created_at': self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')
        }
