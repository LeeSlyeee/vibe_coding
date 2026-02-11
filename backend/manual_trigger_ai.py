from app import app, mongo
import threading
from tasks import analyze_diary_logic

with app.app_context():
    # Find the diary
    u = mongo.db.users.find_one({'username': 'slyeee'})
    uid = str(u['_id'])
    d = mongo.db.diaries.find_one({'user_id': uid, 'date': '2026-02-11'})
    
    if d:
        did = str(d['_id'])
        print(f"Triggering Analysis for {did}...")
        # Run Synchronously here for immediate feedback
        analyze_diary_logic(did)
        print("Done.")
    else:
        print("Diary Not Found.")
