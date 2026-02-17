import requests

def test_150_sync():
    print('🚀 Testing connection to 150 (Dashboard Server)...')
    try:
        url = 'https://150.230.7.76.nip.io/api/v1/centers/verify-code/'
        res = requests.post(url, json={'code': 'TEST_PING'}, timeout=5, verify=False)
        print(f'✅ Connected to 150: {res.status_code} (This means Dashboard is reachable)')
    except Exception as e:
        print(f'❌ Failed to reach 150: {e}')

if __name__ == '__main__':
    test_150_sync()
