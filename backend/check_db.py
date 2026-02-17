from app import app, db
import os

print(f"DATABASE_URL: {os.environ.get('DATABASE_URL')}")
print(f"Flask Config DB: {app.config['SQLALCHEMY_DATABASE_URI']}")
print(f"SQLAlchemy Engine: {db.engine.url}")

try:
    with app.app_context():
        res = db.session.execute('SELECT 1').fetchone()
        print(f"DB Connection OK: {res}")
        
        # Check users count
        from models import User, Diary
        u_cnt = User.query.count()
        d_cnt = Diary.query.count()
        print(f"Users: {u_cnt}, Diaries: {d_cnt}")
        
        # Check center code linkage
        linked = User.query.filter(User.center_code != None).count()
        print(f"Linked Users: {linked}")

except Exception as e:
    print(f"DB Error: {e}")
