from app import app
from flask_jwt_extended import create_access_token
from datetime import timedelta

with app.app_context():
    token = create_access_token(identity='1', expires_delta=timedelta(hours=24))
    print(token)

