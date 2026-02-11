from app import app, mongo

with app.app_context():
    # Find Feb 11 diary for slyeee
    u = mongo.db.users.find_one({'username': 'slyeee'})
    uid = str(u['_id'])
    
    d = mongo.db.diaries.find_one({'user_id': uid, 'date': '2026-02-11'})
    if d:
        print(f"Diary Found: {d.get('_id')}")
        print(f"AI Advice: {d.get('ai_advice')}")
        print(f"Emotion: {d.get('emotion')}")
        print(f"Event: {d.get('event')}")
    else:
        print("Diary Not Found.")
