import requests

def verify_all_endpoints():
    base_url = 'https://217.142.253.35.nip.io/api'
    
    print('🔬 Final Endpoint Verification...')
    
    # login
    try:
        res = requests.post(f'{base_url}/login', json={'username': 'slyeee', 'password': '1234'}, timeout=5)
        if res.status_code == 200:
            print('✅ Login OK (/api/login)')
        else:
            print(f'❌ Login FAIL: {res.status_code}')
    except Exception as e:
        print(f'❌ Login ERROR: {e}')

    # register
    # We won't actually register, just check 400 (Bad Request implies endpoint exists) vs 404
    try:
        res = requests.post(f'{base_url}/register', json={}, timeout=5)
        if res.status_code == 400:
             print('✅ Register Endpoint OK (400 Bad Request implies existence)')
        elif res.status_code == 404:
             print('❌ Register FAIL (404 Not Found)')
        elif res.status_code == 201:
             print('✅ Register OK (Created)')
        else:
             print(f'❓ Register Status: {res.status_code}')
    except Exception as e:
        print(f'❌ Register ERROR: {e}')

if __name__ == '__main__':
    verify_all_endpoints()
