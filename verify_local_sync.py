import requests

def test_local_sync():
    import datetime
    import json
    session = requests.Session()
    session.verify = False 

    BASE_URL = 'https://217.142.253.35.nip.io/api'

    timestamp = int(datetime.datetime.now().timestamp())
    test_user = f'pg_sync_local_{timestamp}'
    
    # 1. Register & Login
    res = session.post(f'{BASE_URL}/register', json={
        'username': test_user,
        'password': 'password',
        'nickname': 'Local_Sync_Tester',
        'role': 'user'
    })
    
    res = session.post(f'{BASE_URL}/login', json={'username': test_user, 'password': 'password'})
    token = res.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    # 2. Try to Link a Code (via Localhost:8000 Proxy)
    # We need a code that exists in the Local Dashboard (Django)
    # If we don't know any, we just test the proxy mechanism.
    # verify-code endpoint will call localhost:8000
    
    print('🔗 Testing Local Proxy (Verify Code)...')
    v_res = session.post(f'{BASE_URL}/v1/centers/verify-code/', json={'code': 'ANY_CODE'})
    # If 217 server logs show "🔄 Proxying verification... to Local Dashboard(8000)..." we are good.
    
    # 3. Create Diary (Sync Trigger)
    diary_payload = {
        'date': datetime.datetime.now().strftime('%Y-%m-%d'),
        'event': 'Local Sync Test',
        'mood_level': 4,
        'sleep_condition': 'Good',
        'ai_comment': 'Local Sync Check'
    }
    
    print('📝 Creating Diary...')
    res = session.post(f'{BASE_URL}/diaries', json=diary_payload, headers=headers)
    
    if res.status_code == 201:
        print('✅ Diary Created. Inspecting logs for Local 8000 Sync...')
    else:
        print(f'❌ Diary Create Failed: {res.text}')

if __name__ == '__main__':
    test_local_sync()
