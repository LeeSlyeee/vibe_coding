import sys
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Add backend directory to path to import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, mongo

def setup_test_users():
    with app.app_context():
        # 1. Cleanup old test users
        mongo.db.users.delete_many({'username': {'$in': ['patient_test', 'guardian_test']}})
        mongo.db.share_codes.delete_many({'user_id': {'$in': ['patient_test', 'guardian_test']}}) # This might need ObjectId logic check later
        # Also clean relationships involving these users requires ObjectIds. Will do after creation or via username lookup if possible.
        # Ideally, we get their IDs first, then clean relationships? 
        # For simplicity, let's just create new ones. The create_user logic usually handles uniqueness.

        print("🧹 Cleaning up old test users...")

        # 2. Create Patient User (내담자)
        # Birthday: 3 days from now (D-3)
        today = datetime.now()
        birthday = today + timedelta(days=3)
        birth_date_str = f"1990-{birthday.month:02d}-{birthday.day:02d}" # Year 1990

        patient_id = mongo.db.users.insert_one({
            'username': 'patient_test',
            'password_hash': generate_password_hash('test1234', method='pbkdf2:sha256'), # Fixed field name
            'nickname': '내담자_테스트',
            'birth_date': birth_date_str,
            'role': 'patient',
            'created_at': datetime.now()
        }).inserted_id
        print(f"✅ Created Patient User: patient_test (Birthday: {birth_date_str}, D-3)")

        # 3. Create Guardian User (보호자)
        guardian_id = mongo.db.users.insert_one({
            'username': 'guardian_test',
            'password_hash': generate_password_hash('test1234', method='pbkdf2:sha256'), # Fixed field name
            'nickname': '보호자_테스트',
            'role': 'guardian',
            'created_at': datetime.now()
        }).inserted_id
        print(f"✅ Created Guardian User: guardian_test")
        
        # Cleanup Relationships
        mongo.db.share_relationships.delete_many({
            '$or': [{'sharer_id': patient_id}, {'viewer_id': guardian_id}]
        })

        return patient_id, guardian_id

def run_scenario(patient_id, guardian_id):
    client = app.test_client()

    print("\n🚀 Starting Test Scenario...")

    # Step 1: Login as Patient & Generate Code
    print("\n[Step 1] Patient logs in and generates share code")
    # Actually, we need a token. Let's use a helper or just assume we mock the auth or use the login endpoint if available.
    # Looking at `app.py` or previous knowledge, there should be a login route.
    # Let's try /api/v1/auth/login or similar. 
    # Based on SignupPage.vue, `authAPI.signup` calls. Login might be `authAPI.login`.
    # Let's assume standard JWT flow.
    
    # Login Patient
    res_p = client.post('/api/login', json={'username': 'patient_test', 'password': 'test1234'}) # Fixed route
    if res_p.status_code != 200:
        print(f"❌ Patient Login Failed: {res_p.data}")
        return
    token_p = res_p.json.get('access_token') or res_p.json.get('token') # Check both
    headers_p = {'Authorization': f'Bearer {token_p}'}

    # Generate Code
    res_code = client.post('/api/v1/share/code', headers=headers_p, json={'user_id': str(patient_id)})
    if res_code.status_code not in [200, 201]:
        print(f"❌ Generate Code Failed: {res_code.data}")
        return
    share_code = res_code.json['code']
    print(f"👉 Generated Share Code: {share_code}")


    # Step 2: Login as Guardian & Connect
    print("\n[Step 2] Guardian logs in and connects using code")
    
    # Login Guardian
    res_g = client.post('/api/login', json={'username': 'guardian_test', 'password': 'test1234'}) # Fixed route
    if res_g.status_code != 200:
        print(f"❌ Guardian Login Failed: {res_g.data}")
        return
    token_g = res_g.json.get('access_token') or res_g.json.get('token')
    headers_g = {'Authorization': f'Bearer {token_g}'}

    # Connect
    res_connect = client.post('/api/v1/share/connect', json={'code': share_code, 'user_id': str(guardian_id)}, headers=headers_g)
    if res_connect.status_code != 200:
        print(f"❌ Connection Failed: {res_connect.data}")
        return
    print(f"✅ Connection Success: {res_connect.json['message']}")


    # Step 3: Check Connected List as Guardian (Verify Birthday Info)
    print("\n[Step 3] Guardian checks connected list (Expecting Birthday Info)")
    res_list = client.get('/api/v1/share/list', headers=headers_g, query_string={'user_id': str(guardian_id)})
    if res_list.status_code != 200:
        print(f"❌ Fetch List Failed: {res_list.data}")
        return
    
    connected_users = res_list.json
    print(f"📋 Connected Users: {connected_users}")

    # Validation
    found = False
    for user in connected_users['data']: # Fixed: Access 'data' key
        if user['name'] == '내담자_테스트' or user['id'] == str(patient_id):
            found = True
            birth_date = user.get('birth_date')
            print(f"🔎 Found Patient! Name: {user['name']}, BirthDate: {birth_date}")
            
            if birth_date:
                # Simple D-Day check
                # Note: This checks the RAW data from API. The D-Day badge logic is in Frontend (JS).
                # Here we verify the API provides the necessary data.
                print("✅ TEST PASSED: 'birth_date' is correctly provided in API response.")
            else:
                print("❌ TEST FAILED: 'birth_date' is missing or empty.")
            break
    
    if not found:
        print("❌ TEST FAILED: Connected patient not found in list.")


if __name__ == '__main__':
    try:
        p_id, g_id = setup_test_users()
        run_scenario(p_id, g_id)
    except Exception as e:
        print(f"💥 Error during test: {e}")
