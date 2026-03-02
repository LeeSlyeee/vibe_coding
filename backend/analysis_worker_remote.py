import threading
import psycopg2
import requests
import json
import os
import re
import logging
import ast
from cryptography.fernet import Fernet # Direct use or utility

# Django Environment Check
try:
    from django.conf import settings
    # Use settings if available
    ENCRYPTION_KEY = getattr(settings, 'ENCRYPTION_KEY', os.environ.get('ENCRYPTION_KEY'))
    DATABASE_URL = getattr(settings, 'DATABASE_URL', os.environ.get('DATABASE_URL'))
except:
    # Fallback to env
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    DATABASE_URL = os.environ.get('DATABASE_URL')

# Simple Crypto Class to avoid dependency hell
class SimpleCrypto:
    def __init__(self, key):
        self.cipher = Fernet(key.encode()) if key else None
    
    def encrypt(self, plain_text):
        if not plain_text or not self.cipher: return plain_text
        try:
            return self.cipher.encrypt(plain_text.encode()).decode()
        except:
            return plain_text
            
    def decrypt(self, cipher_text):
        if not cipher_text or not self.cipher: return cipher_text
        try:
            return self.cipher.decrypt(cipher_text.encode()).decode()
        except:
            return cipher_text

crypto = SimpleCrypto(ENCRYPTION_KEY)

# RunPod Config
RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY')
RUNPOD_LLM_URL = os.getenv('RUNPOD_LLM_URL')

def call_llm_hybrid(prompt, model="maumON-gemma:latest", options=None):
    """
    Hybrid LLM Caller: RunPod (Priority) -> Local Ollama (Fallback)
    """
    if options is None: options = {}
    
    import time

    # 1. Try RunPod Serverless (Priority)
    if RUNPOD_API_KEY and RUNPOD_LLM_URL and "YOUR_POD_ID" not in RUNPOD_LLM_URL:
        try:
            logging.info("🚀 Sending Async request to RunPod Serverless...")
            base_url = RUNPOD_LLM_URL.replace('/runsync', '').replace('/run', '').rstrip('/')
            submit_url = f"{base_url}/run"
            headers = {
                "Authorization": f"Bearer {RUNPOD_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "input": {
                    "prompt": prompt,
                    "max_tokens": options.get('num_predict', 512),
                    "temperature": options.get('temperature', 0.7),
                    "stream": False
                }
            }
            res = requests.post(submit_url, json=payload, headers=headers, timeout=30)
            if res.status_code != 200:
                raise Exception("RunPod Submit Failed")
            job_id = res.json()['id']
            
            # Poll Status
            status_url = f"{base_url}/status/{job_id}"
            start_time = time.time()
            while True:
                if time.time() - start_time > 300: break
                status_res = requests.get(status_url, headers=headers, timeout=30)
                status_data = status_res.json()
                status = status_data.get('status')
                if status == 'COMPLETED':
                    output = status_data.get('output')
                    # ... processing logic (simplified) ...
                    if isinstance(output, dict):
                         if 'reaction' in output: return output['reaction'] # Simplify
                         content = output.get('response') or str(output)
                    else: content = str(output)
                    return content
                elif status in ['FAILED', 'CANCELLED']: break
                time.sleep(2)
        except: pass

    # 2. Local Ollama (Fallback)
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json" if options.get('format') == 'json' else "",
            "options": options
        }
        res = requests.post("http://localhost:11434/api/generate", json=payload, timeout=180)
        if res.status_code == 200:
            return res.json().get('response', '').strip()
    except: pass
    return None

def generate_ai_analysis(content):
    prompt_text = (
        f"너는 다정하고 섬세한 감정 케어 AI '마음온'이야. 아래 회원의 일기를 읽고 분석 결과를 JSON 형태로 줘.\n"
        f"{content}\n\n"
        "### 지시사항:\n"
        "1. 'comment': 회원의 감정을 읽고 따뜻하게 위로하는 말 (해요체, 150자 내외)\n"
        "2. 'emotion': 회원의 현재 감정을 나타내는 **단 하나의 핵심 단어** (예: 불안함, 설렘, 홀가분함, 답답함)\n"
        "3. 'score': 회원의 감정 상태를 **1점(매우 나쁨/우울)**에서 **10점(매우 좋음/행복)** 사이의 정수로 평가해.\n"
        "4. 반드시 아래 JSON 형식으로만 답변해.\n\n"
        "{\n"
        '  "emotion": "핵심감정단어",\n'
        '  "comment": "위로의 메시지...",\n'
        '  "score": 5\n'
        "}"
    )
    
    try:
        options = {"temperature": 0.7, "num_predict": 500, "format": "json"}
        raw = call_llm_hybrid(prompt_text, options=options)
        
        if raw:
             try:
                 # Clean up raw string if needed (sometimes output has garbage)
                 import json
                 if isinstance(raw, dict): data = raw
                 else: data = json.loads(raw)
                 
                 return data.get('comment', ''), data.get('emotion', ''), data.get('score', 5)
             except:
                 return raw, "분석중", 5
    except Exception as e:
        print(f"❌ AI Gen Error: {e}")
    return "당신의 마음을 깊이 응원합니다.", "대기중", 5

# Set up logging
logging.basicConfig(level=logging.INFO)

def run_analysis_process(diary_id, date, event, sleep, emotion_desc, emotion_meaning, self_talk):
    logging.info(f"🧵 [Thread] Starting Analysis for Diary {diary_id}...")
    
    full_text = f"날짜: {date}\n수면: {sleep}\n사건: {event}\n감정: {emotion_desc}\n의미: {emotion_meaning}\n스스로에게: {self_talk}"
    comment, emotion, score = generate_ai_analysis(full_text)
    
    enc_comment = crypto.encrypt(comment)
    enc_emotion = crypto.encrypt(emotion)
    
    # Update DB (Using psycopg2 directly)
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        try:
            score = int(score)
            score = max(1, min(10, score))
        except: score = 5

        # Update diary record in DB
        # Django model uses db_table = "diaries"
        cur.execute(
            "UPDATE diaries SET ai_comment = %s, ai_emotion = %s, mood_score = %s WHERE id = %s", 
            (enc_comment, enc_emotion, score, diary_id)
        )
        
        print(f"✅ [Thread] Analysis Complete for Diary {diary_id} (Score: {score})")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ [Thread] DB Update Failed: {e}")

def start_analysis_thread(diary_id, date, event, sleep, emotion_desc, emotion_meaning, self_talk):
    t = threading.Thread(target=run_analysis_process, args=(diary_id, date, event, sleep, emotion_desc, emotion_meaning, self_talk))
    t.start()
