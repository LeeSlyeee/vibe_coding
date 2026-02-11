from app import app, mongo
from flask_jwt_extended import create_access_token
from bson import ObjectId

with app.app_context():
    # 1. Get User
    user = mongo.db.users.find_one({'username': 'slyeee'})
    if not user:
        print("User slyeee not found")
        exit()
        
    print(f"User ID: {user['_id']} (Type: {type(user['_id'])})")
    
    # 2. Create Token (Simulate Login)
    # Ensure we use exactly what login() uses: str(user['_id'])
    identity = str(user['_id'])
    token = create_access_token(identity=identity)
    print(f"Generated Token for Identity: {identity}")
    
    # 3. Simulate Request
    client = app.test_client()
    headers = {'Authorization': f"Bearer {token}"}
    
    # 4. GET /api/diaries
    print("--- Requesting GET /api/diaries ---")
    res = client.get('/api/diaries', headers=headers)
    print(f"Response Status: {res.status_code}")
    
    data = res.json
    if isinstance(data, list):
        print(f"Response List Length: {len(data)}")
        if len(data) > 0:
            print(f"Sample Item: {data[0].get('date')} (ID: {data[0].get('_id')})")
    else:
        print(f"Response Data (Not List): {data}")

    # 5. DB Debug
    print("--- DB Direct Check ---")
    
    # Check String ID
    count_str = mongo.db.diaries.count_documents({'user_id': str(user['_id'])})
    print(f"DB Query {{'user_id': '{str(user['_id'])}'}} Count: {count_str}")
    
    # Check ObjectId
    count_obj = mongo.db.diaries.count_documents({'user_id': user['_id']})
    print(f"DB Query {{'user_id': ObjectId(...)}} Count: {count_obj}")
