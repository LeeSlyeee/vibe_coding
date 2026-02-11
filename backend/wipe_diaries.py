from app import app, mongo
with app.app_context():
    user = mongo.db.users.find_one({'username': 'slyeee'})
    if user:
        # Delete String ID
        res1 = mongo.db.diaries.delete_many({'user_id': str(user['_id'])})
        # Delete ObjectId ID (just in case)
        res2 = mongo.db.diaries.delete_many({'user_id': user['_id']})
        
        print(f"🗑️ Clean Slate: Deleted {res1.deleted_count} (String ID) + {res2.deleted_count} (ObjectId) items for slyeee.")
    else:
        print("User slyeee not found.")
