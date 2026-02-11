import sys
import os
import random
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, mongo

def run_stress_test(num_iterations=20):
    client = app.test_client()
    
    print(f"🤖 [Stress Test Initiated] Count: {num_iterations}")
    print("---------------------------------------------------")
    
    # [Setup: Clear old test data]
    # We will use random accounts per iteration
    
    failures = []
    success_count = 0
    
    for i in range(1, num_iterations + 1):
        # 1. Randomize Scenario (Web->App or App->Web)
        # 2. Randomize Birthdays (Today, D-3, D-7, D+1, Past, Future Year 2027)
        # 3. Check Result

        # [Generate Random Birthday Offset]
        offset = random.choice([0, 3, 7, -1, 365, -30]) # 0=Today, 3=D-3 ...
        is_web_sharer = random.choice([True, False]) # True=Web->App, False=App->Web
        
        today = datetime.now()
        target_bday = today + timedelta(days=offset)
        bday_str = target_bday.strftime("%Y-%m-%d")
        mmdd_str = target_bday.strftime("%m-%d") # Key Match Target
        
        # [Create Unique Test Usernames]
        sharer_name = f"stress_sharer_{i}"
        viewer_name = f"stress_viewer_{i}"
        p_role = 'patient'
        g_role = 'guardian'
        
        # Determine Roles based on scenario (Sharer is always Patient here for simplicity)
        try:
             # --- 1. Create Users ---
            # Sharer (Patient)
             # Sharer (Patient)
            with app.app_context():
                from werkzeug.security import generate_password_hash
                hashed_pw = generate_password_hash('test', method='pbkdf2:sha256')

                # Cleanup existing if any (unlikely due to unique name)
                mongo.db.users.delete_one({'username': sharer_name})
                mongo.db.users.delete_one({'username': viewer_name})

                sharer_id = mongo.db.users.insert_one({
                    'username': sharer_name,
                    'password_hash': hashed_pw, # Correct Hash
                    'nickname': f"S_Patient_{i}",
                    'birth_date': bday_str,
                    'role': p_role,
                    'created_at': datetime.now()
                }).inserted_id
                
                viewer_id = mongo.db.users.insert_one({
                    'username': viewer_name,
                    'password_hash': hashed_pw, # Correct Hash
                    'nickname': f"S_Guardian_{i}",
                    'role': g_role, 
                    'created_at': datetime.now()
                }).inserted_id
            
            # --- 2. Sharer Generates Code ---
            # Simulate Login & Code Gen (Skipping detailed login for speed, using ID direct if API allows or mocking auth)
            # Actually our API requires token for most parts, but share/code allows user_id body in testing mode we enabled previously?
            # Let's use the robust way: Login first.
            
            # [Optimization] Direct Code Gen via Internal Function to speed up testing logic
            # OR use test client proper. Let's use test client proper to simulate REAL WORLD.
            
            # Login Sharer
            # Note: We didn't set real password hash, so login API might fail. 
            # Let's direct insert relationship to simulate "Connected" state, 
            # and focus on "Data Fetching" logic which is the core of this test.
            # OR fix password.
            
            # Fix Password
            from werkzeug.security import generate_password_hash
            with app.app_context():
                mongo.db.users.update_one({'_id': sharer_id}, {'$set': {'password': generate_password_hash('test', method='pbkdf2:sha256')}})
                mongo.db.users.update_one({'_id': viewer_id}, {'$set': {'password': generate_password_hash('test', method='pbkdf2:sha256')}})

            # Login Sharer
            res_s = client.post('/api/login', json={'username': sharer_name, 'password': 'test'})
            token_s = res_s.json.get('access_token') or res_s.json.get('token')
            
            # Login Viewer
            res_v = client.post('/api/login', json={'username': viewer_name, 'password': 'test'})
            token_v = res_v.json.get('access_token') or res_v.json.get('token')
            
            # Sharer makes code
            res_code = client.post('/api/v1/share/code', headers={'Authorization': f'Bearer {token_s}'}, json={'user_id': str(sharer_id)})
            code = res_code.json['code']
            
            # Viewer connects
            res_conn = client.post('/api/v1/share/connect', headers={'Authorization': f'Bearer {token_v}'}, json={'code': code, 'user_id': str(viewer_id)})
            
            if res_conn.status_code != 200:
                failures.append(f"[{i}] Connection Failed: {res_conn.data}")
                continue

            # --- 3. Viewer Fetches List & Verifies Birthday ---
            res_list = client.get('/api/v1/share/list', headers={'Authorization': f'Bearer {token_v}'}, query_string={'user_id': str(viewer_id), 'role': 'viewer'})
            data = res_list.json['data']
            
            target_user = next((u for u in data if u['name'] == f"S_Patient_{i}"), None)
            
            if not target_user:
                failures.append(f"[{i}] Data Sync Failed: Patient not found in list")
                continue
                
            received_bday = target_user.get('birth_date', "")
            # Check Match (MM-DD)
            if received_bday[5:] == mmdd_str:
                success_count += 1
                # print(f"[{i}] Pass ✅ (Offset: {offset}, Sent: {bday_str}, Recv: {received_bday})")
            else:
                failures.append(f"[{i}] Birthday Mismatch: Sent {bday_str}, Recv {received_bday}")

        except Exception as e:
            failures.append(f"[{i}] Exception: {str(e)}")
            
    print("\n===================================================")
    print(f"📊 [Stress Test Report]")
    print(f"   - Total Attempts: {num_iterations}")
    print(f"   - Success: {success_count}")
    print(f"   - Failures: {len(failures)}")
    print("===================================================")
    
    if failures:
        print("\n❌ [Failure Details]")
        for f in failures:
            print(f"   - {f}")
    else:
        print("\n✅ All scenarios PASSED with NO failures.")

if __name__ == '__main__':
    run_stress_test(20)
