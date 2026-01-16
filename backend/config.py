import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-prod'
    # MariaDB Connection String
    # [Legacy] RDBMS Connection (MariaDB/MySQL)
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:1q2w3e4r@127.0.0.1:3306/mood_diary'
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # [Target] MongoDB Connection
    # Default to localhost:27017 if MONGO_URI not provided
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/mood_diary_db'

    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-prod'
    # JWT 토큰 만료 시간 설정 (24시간)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
