from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Center(db.Model):
    __tablename__ = 'centers'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    nickname = db.Column(db.String(80), nullable=True) # Added
    password = db.Column(db.String(200), nullable=False)
    center_code = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(20), default='user')  # user, admin
    
    # Relationships
    diaries = db.relationship('Diary', backref='author', lazy=True)

class Diary(db.Model):
    __tablename__ = 'diaries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    
    # Core Content
    event = db.Column(db.Text, nullable=True)
    sleep_condition = db.Column(db.String(100), nullable=True)
    emotion_desc = db.Column(db.Text, nullable=True)
    emotion_meaning = db.Column(db.Text, nullable=True)
    self_talk = db.Column(db.Text, nullable=True)
    
    # Metadata
    mood_level = db.Column(db.Integer, default=3)
    weather = db.Column(db.String(50), nullable=True)
    temperature = db.Column(db.String(20), nullable=True)
    
    # New Format
    mode = db.Column(db.String(20), default='green')
    mood_intensity = db.Column(db.Integer, default=0)
    gratitude_note = db.Column(db.Text, nullable=True)
    gratitude_note = db.Column(db.Text, nullable=True)
    ai_comment = db.Column(db.Text, nullable=True) # [Added] AI Comment
    ai_emotion = db.Column(db.Text, nullable=True) # [New] AI Analyzed Emotion Keyword
    safety_flag = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatLog(db.Model):
    __tablename__ = 'chat_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(10), nullable=False)  # user, bot
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
