from app import app, mongo

with app.app_context():
    # Find Feb 11 diary for slyeee
    u = mongo.db.users.find_one({'username': 'slyeee'})
    uid = str(u['_id'])
    
    d = mongo.db.diaries.find_one({'user_id': uid, 'date': '2026-02-11'})
    if d:
        print(f"Diary Found: {d.get('_id')}")
        print(f"AI Comment (Encrypted?): {d.get('ai_comment')}")
        print(f"AI Prediction (Encrypted?): {d.get('ai_prediction')}")
        
        # Try Decrypt
        from crypto_utils import crypto_manager
        try:
            dec_com = crypto_manager.decrypt(d.get('ai_comment', ''))
            print(f"Decrypted Comment: {dec_com}")
        except:
            print("Decrypt Failed (Comment)")
            
        try:
            dec_pred = crypto_manager.decrypt(d.get('ai_prediction', ''))
            print(f"Decrypted Prediction: {dec_pred}")
        except:
             print("Decrypt Failed (Prediction)")
    else:
        print("Diary Not Found.")
