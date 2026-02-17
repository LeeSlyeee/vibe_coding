
import requests

def verify_trailing_slash():
    base_url = 'https://217.142.253.35.nip.io/api'
    payload = {'username': 'slyeee', 'password': '1234'}
    
    print('🔬 Testing API Endpoint Logic...')
    
    # Test 1: With Trailing Slash (The Bug)
    url_bad = f'{base_url}/login/'
    print(f'\n1️⃣  Testing WITH trailing slash: {url_bad}')
    try:
        res1 = requests.post(url_bad, json=payload, timeout=5)
        print(f'   👉 Status Code: {res1.status_code}')
        if res1.status_code == 404:
            print('   ✅ Result: 404 Not Found (Expected Failure)')
        else:
            print(f'   ❌ Result: Unexpected {res1.status_code}')
    except Exception as e:
        print(f'   ⚠️ Error: {e}')

    # Test 2: Without Trailing Slash (The Fix)
    url_good = f'{base_url}/login'
    print(f'\n2️⃣  Testing WITHOUT trailing slash: {url_good}')
    try:
        res2 = requests.post(url_good, json=payload, timeout=5)
        print(f'   👉 Status Code: {res2.status_code}')
        if res2.status_code == 200:
            print(f'   ✅ Result: 200 OK (Login Success!)')
            token = res2.json().get('access_token')
            print(f'   🔑 Token received: {token[:10]}...')
        elif res2.status_code == 400 or res2.status_code == 401:
             print(f'   ❌ Logic Error: {res2.json()}')
        else:
            print(f'   ❌ Result: Failed with {res2.status_code}')
            print(f'   📝 Response: {res2.text}')
    except Exception as e:
        print(f'   ⚠️ Error: {e}')

if __name__ == '__main__':
    verify_trailing_slash()
