from app import app, mongo

with app.app_context():
    # Find Feb 11 diary for slyeee
    u = mongo.db.users.find_one({'username': 'slyeee'})
    uid = str(u['_id'])
    
    cursor = mongo.db.diaries.find({'user_id': uid, 'date': '2026-02-11'})
    print(f"Count: {mongo.db.diaries.count_documents({'user_id': uid, 'date': '2026-02-11'})}")
    
    for d in cursor:
        print(f"--- Diary {d.get('_id')} ---")
        print(f"Task ID: {d.get('task_id')}")
        print(f"AI Analysis: {d.get('ai_analysis')}")
        print(f"AI Comment: {d.get('ai_comment')}")
        print(f"AI Prediction: {d.get('ai_prediction')}")
