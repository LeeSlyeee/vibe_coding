import requests

def debug_diaries():
    s = requests.Session()
    s.verify=False
    # Login as slyeee
    res = s.post('https://217.142.253.35.nip.io/api/login', json={'username': 'slyeee', 'password': '1234'})
    token = res.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get Diaries
    d_res = s.get('https://217.142.253.35.nip.io/api/diaries', headers=headers)
    
    print(f'Slyeee Diaries Count: {len(d_res.json())}')
    for d in d_res.json():
        print(f'Date: {d["date"]}, ID: {d["id"]}')

if __name__ == '__main__':
    debug_diaries()
