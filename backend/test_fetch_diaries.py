from app import app, mongo
from flask_jwt_extended import create_access_token

with app.app_context():
    # 1. Get Slyeee ID
    user = mongo.db.users.find_one({'username': 'slyeee'})
    if not user:
        print("User slyeee not found")
        exit()
        
    user_id_str = str(user['_id'])
    print(f"User ID: {user_id_str}")
    
    # 2. Generate Token
    access_token = create_access_token(identity=user_id_str)
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # 3. Test Fetch Diaries (No Filter)
    with app.test_client() as client:
        print("\n--- Testing GET /api/diaries (Limit 100) ---")
        res = client.get('/api/diaries', headers=headers)
        if res.status_code == 200:
            data = res.json
            print(f"Status: 200 OK. Count: {len(data)}")
            if len(data) > 0:
                print(f"First Entry Date: {data[0].get('created_at')}")
        else:
            print(f"Error: {res.status_code}, {res.data}")

        # 4. Test Fetch Diaries (Current Month)
        import datetime
        now = datetime.datetime.now()
        year = now.year
        month = now.month
        print(f"\n--- Testing GET /api/diaries?year={year}&month={month} ---")
        res = client.get(f'/api/diaries?year={year}&month={month}', headers=headers)
        if res.status_code == 200:
            data = res.json
            print(f"Status: 200 OK. Count: {len(data)}")
        else:
            print(f"Error: {res.status_code}, {res.data}")
