import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-prod'
    # MariaDB Connection String
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:1q2w3e4r@127.0.0.1:3306/mood_diary'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-prod'
    # JWT 토큰 만료 시간 설정 (24시간)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
