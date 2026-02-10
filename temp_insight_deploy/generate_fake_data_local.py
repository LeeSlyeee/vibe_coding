import os
import requests
import json
import datetime
import random
import time
import concurrent.futures

# User provided API KEY
API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_API_KEY_HERE")
URL = "https://api.openai.com/v1/chat/completions"

start_date = datetime.date(2026, 1, 1)
end_date = datetime.date(2026, 2, 8)

results = []

def process_date(date_val):
    date_str = date_val.strftime("%Y-%m-%d")
    print(f"Generating for {date_str}...")
    
    prompt = f"""
    날짜: {date_str}
    한국에 사는 40대 직장인입니다.
    이 날짜의 일기를 작성해주세요.
    날씨는 한국의 1월/2월 겨울 날씨를 반영해주세요.
    기분은 날마다 다르게 (행복, 우울, 평범, 스트레스, 감사 등) 자연스럽게 흐름을 만들어주세요.
    
    다음 7가지 항목을 포함한 JSON 형식으로만 응답해주세요:
    1. weather: 날씨 (예: 맑음, 흐림, 눈, 한파)
    2. sleep_condition: 수면 상태 (예: 푹 잤음, 자다 깸, 불면, 개운함)
    3. event: 오늘 있었던 일 (3-4문장, 구체적이고 일상적인 내용)
    4. emotion: 느낀 감정 키워드 (예: 뿌듯함, 답답함, 평온함)
    5. meaning: 감정의 깊은 의미나 원인 분석 (심리적 통찰)
    6. self_talk: 나에게 보내는 따뜻한 위로의 한마디
    7. medication_taken: 약물 복용 여부 (예: '혈압약 복용', '비타민', '없음')
    8. mood_score: 1(최악)~10(최고) 정수

    JSON 예시:
    {{
        "weather": "-3도 맑음",
        "sleep_condition": "중간에 깨지도 않고 푹 잠",
        "event": "...",
        "emotion": "...",
        "meaning": "...",
        "self_talk": "...",
        "medication_taken": "혈압약 복용",
        "mood_score": 8
    }}
    """
    
    retries = 3
    while retries > 0:
        try:
            resp = requests.post(URL, headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }, json={
                "model": "gpt-4-turbo", # or 4o-mini
                "messages": [{"role": "system", "content": "You are a helpful assistant that generates realistic diary entries in JSON format. Return only JSON."}, 
                             {"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }, timeout=30)
            
            if resp.status_code != 200:
                print(f"Error {date_str} ({resp.status_code}): {resp.text}")
                time.sleep(2)
                retries -= 1
                continue

            content = resp.json()['choices'][0]['message']['content']
            entry = json.loads(content)
            entry['date'] = date_str
            return entry
        except Exception as e:
            print(f"Failed {date_str}: {e}")
            time.sleep(2)
            retries -= 1
    return None

date_range = []
current = start_date
while current <= end_date:
    date_range.append(current)
    current += datetime.timedelta(days=1)

print(f"Starting parallel generation for {len(date_range)} days with 5 workers...")
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(process_date, d): d for d in date_range}
    for future in concurrent.futures.as_completed(futures):
        res = future.result()
        if res:
            results.append(res)

# Sort by date
results.sort(key=lambda x: x['date'])

with open('fake_diaries_2026.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Successfully generated {len(results)} entries.")
