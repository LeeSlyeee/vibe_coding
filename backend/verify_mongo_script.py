import pymongo

def verify_mongo():
    try:
        client = pymongo.MongoClient('mongodb://localhost:27017/')
        db = client['mood_diary_db']
        
        users = db['users']
        diaries = db['diaries']
        
        u = users.find_one({'username': 'slyeee'})
        
        if u:
            print(f'Mongo User Found: {u["username"]} (ID: {u["_id"]})')
            uid_str = str(u['_id'])
            
            # Check string user_id
            count1 = diaries.count_documents({'user_id': uid_str})
            # Check ObjectId user_id
            count2 = diaries.count_documents({'user_id': u['_id']})
            
            print(f'Diaries (String ID): {count1}')
            print(f'Diaries (ObjectId): {count2}')
        else:
            print('Mongo User slyeee not found')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    verify_mongo()
