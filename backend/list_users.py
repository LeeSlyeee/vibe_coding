from app import app, mongo

def list_users():
    with app.app_context():
        users = mongo.db.users.find()
        print(f"Total Users: {mongo.db.users.count_documents({})}")
        for u in users:
            print(f"- {u.get('username')} / {u.get('nickname')} (Assessed: {u.get('assessment_completed')})")

if __name__ == "__main__":
    list_users()
