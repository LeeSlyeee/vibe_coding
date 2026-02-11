from app import app, mongo

with app.app_context():
    # Find Feb 11 diary for slyeee
    u = mongo.db.users.find_one({'username': 'slyeee'})
    uid = str(u['_id'])
    
    d = mongo.db.diaries.find_one({'user_id': uid, 'date': '2026-02-11'})
    if d:
        print(f"Diary Found: {d.get('_id')}")
        print(f"AI Analysis (Encrypted?): {d.get('ai_analysis')}")
        
        if d.get('ai_analysis'):
             try:
                 from crypto_utils import crypto_manager
                 dec = crypto_manager.decrypt(d.get('ai_analysis'))
                 print(f"Decrypted: {dec}")
             except:
                 print("Decrypt Failed")
    else:
        print("Diary Not Found.")
