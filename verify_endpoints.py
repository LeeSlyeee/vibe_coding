
import requests

def verify_server_endpoints():
    base_url = 'https://217.142.253.35.nip.io/api'
    
    print('Testing Login Endpoint...')
    try:
        res = requests.post(f'{base_url}/login', json={'username': 'slyeee', 'password': '1234'}, timeout=5)
        if res.status_code == 200:
            print('✅ Login Success (/api/login)')
        else:
            print(f'❌ Login Failed: {res.status_code} - {res.text}')
    except Exception as e:
        print(f'❌ Login Error: {e}')

if __name__ == "__main__":
    verify_server_endpoints()
