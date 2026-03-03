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
    __tablename__ = 'users' # [Migration] vibe_db table
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    real_name = db.Column(db.String(50), nullable=True)
    nickname = db.Column(db.String(80), nullable=True)
    center_code = db.Column(db.String(50), nullable=True)
    role = db.Column(db.String(20), nullable=True)
    birth_date = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, nullable=True) # vibe_db has this

    # [Push Notification] FCM 디바이스 토큰
    fcm_token = db.Column(db.Text, nullable=True)
    apns_token = db.Column(db.Text, nullable=True)
    fcm_updated_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    diaries = db.relationship('Diary', backref='author', lazy=True)

class Diary(db.Model):
    __tablename__ = 'diaries' # [Migration] vibe_db table
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # [Column Mapping]
    # DB column is 'event', but Flask app uses 'content'.
    # We map 'event' column to 'event' field, and add a property for compatibility.
    event = db.Column(db.Text, nullable=True)
    
    @property
    def content(self):
        # [Fix] Decrypt content on read
        try:
            from crypto_utils import crypto_manager
            if self.event and self.event.startswith('gAAAA'):
                return crypto_manager.decrypt(self.event)
            return self.event
        except Exception as e:
            print(f"Content Decryption Error: {e}")
            return self.event or ""
    
    @content.setter
    def content(self, value):
        self.event = value

    # Direct Mappings (vibe_db has these exact columns)
    date = db.Column(db.String(10), nullable=False) # stored as 'YYYY-MM-DD' string
    
    sleep_condition = db.Column(db.Text, nullable=True) # Text type in DB
    emotion_desc = db.Column(db.Text, nullable=True)
    emotion_meaning = db.Column(db.Text, nullable=True)
    self_talk = db.Column(db.Text, nullable=True)
    
    mood_level = db.Column(db.Integer, nullable=True)
    mood_intensity = db.Column(db.Integer, nullable=True) # Exists in vibe_db
    
    weather = db.Column(db.String(50), nullable=True)
    temperature = db.Column(db.String(20), nullable=True)
    mode = db.Column(db.String(20), nullable=True)
    
    gratitude_note = db.Column(db.Text, nullable=True)
    
    safety_flag = db.Column(db.Boolean, nullable=True)
    
    ai_comment = db.Column(db.Text, nullable=True)
    ai_emotion = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date,
            'content': self.content, # Use property
            'mood_level': self.mood_level,
            'mood_intensity': self.mood_intensity,
            'sleep_condition': self.sleep_condition,
            'emotion_desc': self.emotion_desc,
            'emotion_meaning': self.emotion_meaning,
            'self_talk': self.self_talk,
            'weather': self.weather,
            'temperature': self.temperature,
            'gratitude_note': self.gratitude_note,
            'ai_comment': self.ai_comment,
            'ai_emotion': self.ai_emotion,
            'safety_flag': self.safety_flag,
            'image_url': None # Not in DB
        }

class ChatLog(db.Model):
    __tablename__ = 'chat_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # [Fix] users table
    session_id = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class ShareCode(db.Model):
    """일회용 가족공유 초대 코드 (10분 만료)"""
    __tablename__ = 'share_codes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code = db.Column(db.String(6), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

class ShareRelationship(db.Model):
    """공유자(sharer) ↔ 조회자(viewer) 관계"""
    __tablename__ = 'share_relationships'
    id = db.Column(db.Integer, primary_key=True)
    sharer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    viewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    connected_at = db.Column(db.DateTime, default=datetime.utcnow)

    # [Phase 5] 보호자 역할 및 알림 설정
    role = db.Column(db.String(20), default='viewer')  # 'guardian' or 'viewer'
    
    # 알림 설정 (보호자가 받을 알림 종류)
    alert_mood_drop = db.Column(db.Boolean, default=True)    # 마음 온도 급락 알림
    alert_crisis = db.Column(db.Boolean, default=True)       # 위기 신호 알림
    alert_inactivity = db.Column(db.Boolean, default=True)   # 장기 미기록 알림 (7일)
    
    # [Phase 6] 공유 범위 설정 (내담자가 제어)
    share_mood = db.Column(db.Boolean, default=True)         # 마음 온도 공유
    share_report = db.Column(db.Boolean, default=False)      # 주간 리포트 공유
    share_crisis = db.Column(db.Boolean, default=True)       # 위기 신호 공유
    
    # 마지막 알림 발송 시각 (중복 알림 방지)
    last_alert_at = db.Column(db.DateTime, nullable=True)

    sharer = db.relationship('User', foreign_keys=[sharer_id], backref='shared_to')
    viewer = db.relationship('User', foreign_keys=[viewer_id], backref='shared_from')

