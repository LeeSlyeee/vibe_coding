import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

load_dotenv()

def get_korea_time():
    """Returns the current time in KST (UTC+9)"""
    KST = pytz.timezone('Asia/Seoul')
    return datetime.now(KST)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-prod'
    # MariaDB Connection String
    # [Legacy] RDBMS Connection (MariaDB/MySQL)
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:1q2w3e4r@127.0.0.1:3306/mood_diary'
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # [Target] MongoDB Connection
    # Default to localhost:27017 if MONGO_URI not provided
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/mood_diary_db'

    # [CRITICAL FIX] Hardcode Secret Key to match Main Server (150)
    # Environment variable loading via SystemD is failing, so we enforce it here.
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'django-insecure-dev-key-12345'
    # JWT 토큰 만료 시간 설정 (24시간)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    
    # [Data Privacy] Encryption Key for Diaries (Fernet)
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    

