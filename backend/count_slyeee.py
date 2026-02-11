from app import app, mongo
with app.app_context():
    # String ID
    user = mongo.db.users.find_one({'username': 'slyeee'})
    if user:
        c1 = mongo.db.diaries.count_documents({'user_id': str(user['_id'])})
        c2 = mongo.db.diaries.count_documents({'user_id': user['_id']})
        print(f"Slyeee ({user['_id']}): String={c1}, Object={c2}")
    else:
        print("Slyeee Not Found")
