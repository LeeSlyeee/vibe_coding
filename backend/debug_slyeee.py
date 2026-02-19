
import requests

def debug_diaries():
    s = requests.Session()
    s.verify=False
    # Login as slyeee
    res = s.post('https://217.142.253.35.nip.io/api/login', json={'username': 'slyeee', 'password': '1234'})
    if res.status_code != 200:
        print(f"Login failed: {res.text}")
        return
        
    token = res.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get Diaries
    d_res = s.get('https://217.142.253.35.nip.io/api/diaries', headers=headers)
    
    if d_res.status_code != 200:
        print(f"Get Diaries failed: {d_res.text}")
        return

    diaries = d_res.json()
    print(f'Total Diaries: {len(diaries)}')
    
    target_diaries = [d for d in diaries if d['date'] == '2026-02-09']
    print(f'Slyeee Diaries for 2026-02-09: {len(target_diaries)}')
    
    for d in target_diaries:
        print(f"ID: {d['id']} | Mood: {d.get('mood_level')} | Created: {d.get('created_at')}")
        print(f" - AI Emotion: {d.get('ai_emotion')}")
        print(f" - AI Comment: {d.get('ai_comment')}")
        # Print first 20 chars of content
        content = d.get('content') or d.get('event')
        print(f" - Content: {content[:20] if content else 'None'}")
        print("-" * 50)

if __name__ == '__main__':
    debug_diaries()
