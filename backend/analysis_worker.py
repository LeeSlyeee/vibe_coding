import threading
import psycopg2
import requests
import json
import os
import re
import logging
import ast # Added for safe literal eval
from dotenv import load_dotenv
from crypto_utils import EncryptionManager

load_dotenv()

# PG Config
DB_NAME = "vibe_db"
DB_USER = "vibe_user"
DB_PASS = "vibe1234"
DB_HOST = "127.0.0.1"


crypto = EncryptionManager(os.environ.get('ENCRYPTION_KEY'))

# RunPod Config
RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY')
RUNPOD_LLM_URL = os.getenv('RUNPOD_LLM_URL')

def call_llm_hybrid(prompt, model="maumON-gemma:latest", options=None):
    """
    Hybrid LLM Caller: RunPod (Priority) -> Local Ollama (Fallback)
    """
    if options is None: options = {}
    
    logging.info(f"🔍 Hybrid Check: KEY_LEN={len(str(RUNPOD_API_KEY)) if RUNPOD_API_KEY else 0}, URL={RUNPOD_LLM_URL}")
    
    import time

    # 1. Try RunPod Serverless (Priority)
    # The URL in .env should be base endpoint: https://api.runpod.ai/v2/mp2w6kb0npg0tp
    if RUNPOD_API_KEY and RUNPOD_LLM_URL and "YOUR_POD_ID" not in RUNPOD_LLM_URL:
        try:
            logging.info("🚀 Sending Async request to RunPod Serverless...")
            
            # Normalize Base URL (Remove /runsync or /run)
            base_url = RUNPOD_LLM_URL.replace('/runsync', '').replace('/run', '').rstrip('/')
            
            # 1. Submit Job
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
                logging.error(f"❌ RunPod Submit Failed {res.status_code}: {res.text}")
                raise Exception("RunPod Submit Failed")
                
            job_id = res.json()['id']
            logging.info(f"⏳ Job Submitted: {job_id}. Polling status...")
            
            # 2. Poll Status
            status_url = f"{base_url}/status/{job_id}"
            start_time = time.time()
            
            while True:
                if time.time() - start_time > 300: # 5 min timeout
                    raise Exception("RunPod Job Timed Out")
                    
                status_res = requests.get(status_url, headers=headers, timeout=30)
                status_data = status_res.json()
                status = status_data.get('status')
                
                if status == 'COMPLETED':
                    output = status_data.get('output')
                    logging.info("✅ RunPod Job Completed!")
                    
                    # Process Output
                    if isinstance(output, dict):
                         if 'reaction' in output:
                             # Clean Markdown tokens if present
                             clean_str = output['reaction'].strip()
                             if clean_str.startswith('```'):
                                 clean_str = re.sub(r'^```(?:json)?\s*|\s*```$', '', clean_str, flags=re.MULTILINE)
                             clean_str = clean_str.strip()
                             
                             try:
                                 inner = json.loads(clean_str)
                             except:
                                 try:
                                     inner = ast.literal_eval(clean_str)
                                 except:
                                     # Regex Fallback
                                     emo_match = re.search(r'["\']emotion["\']\s*:\s*["\']((?:[^"\\]|\\.)*)["\']', clean_str)
                                     com_match = re.search(r'["\']comment["\']\s*:\s*["\']((?:[^"\\]|\\.)*)["\']', clean_str)
                                     if emo_match and com_match:
                                         inner = {"emotion": emo_match.group(1), "comment": com_match.group(1)}
                                     else:
                                         inner = None
                                     
                             if isinstance(inner, dict):
                                 content = json.dumps(inner, ensure_ascii=False)
                             else:
                                 content = output['reaction']
                         elif 'text' in output:
                             content = output['text']
                         elif 'response' in output:
                             content = output['response']
                         elif 'choices' in output:
                             # vLLM 형식: {"choices": [{"text": "...", "tokens": [...]}]}
                             choices = output['choices']
                             if isinstance(choices, list) and len(choices) > 0:
                                 choice = choices[0]
                                 if isinstance(choice, dict):
                                     content = choice.get('text', '')
                                     if not content and 'tokens' in choice:
                                         tokens = choice['tokens']
                                         content = ''.join(str(t) for t in tokens) if isinstance(tokens, list) else str(tokens)
                                     if not content:
                                         msg = choice.get('message', {})
                                         content = msg.get('content', '') if isinstance(msg, dict) else ''
                                 else:
                                     content = str(choice)
                             else:
                                 content = json.dumps(output, ensure_ascii=False)
                             content = content.strip()
                         else:
                             content = json.dumps(output, ensure_ascii=False)
                    elif isinstance(output, list):
                         # RunPod vLLM 실제 형태: [{'choices': [{'tokens': ['텍스트']}], 'usage': {...}}]
                         content = ''
                         if len(output) > 0:
                             first = output[0]
                             if isinstance(first, dict) and 'choices' in first:
                                 choices = first['choices']
                                 if isinstance(choices, list) and len(choices) > 0:
                                     choice = choices[0]
                                     if isinstance(choice, dict):
                                         if 'tokens' in choice:
                                             tokens = choice['tokens']
                                             content = ''.join(str(t) for t in tokens) if isinstance(tokens, list) else str(tokens)
                                         elif 'text' in choice:
                                             content = choice['text']
                             elif isinstance(first, dict) and 'text' in first:
                                 content = first['text']
                         if not content:
                             content = json.dumps(output, ensure_ascii=False)
                    elif isinstance(output, str):
                         # output이 문자열인 경우
                         content = output.strip()
                         if content.startswith('[{') or content.startswith('{'):
                             try:
                                 parsed = ast.literal_eval(content)
                                 if isinstance(parsed, list) and len(parsed) > 0:
                                     first = parsed[0]
                                     if isinstance(first, dict) and 'choices' in first:
                                         choices = first['choices']
                                         if isinstance(choices, list) and len(choices) > 0:
                                             choice = choices[0]
                                             if isinstance(choice, dict):
                                                 if 'tokens' in choice:
                                                     tokens = choice['tokens']
                                                     content = ''.join(str(t) for t in tokens) if isinstance(tokens, list) else str(tokens)
                                                 elif 'text' in choice:
                                                     content = choice['text']
                             except:
                                 pass
                    else:
                         content = str(output)
                    
                    # 최종 정제: 이스케이프 복원
                    content = content.replace('\\n', '\n').strip()
                    
                    return content
                    
                elif status in ['FAILED', 'CANCELLED']:
                    logging.error(f"❌ RunPod Job Failed: {status}")
                    raise Exception(f"RunPod Job {status}")
                
                # Wait before polling again
                time.sleep(2)
                
        except Exception as e:
            logging.error(f"❌ RunPod Async Failed: {e}")
            # Fallthrough to Local

    # 2. Local Ollama (Fallback)
    try:
        logging.info("⏳ Sending request to Local Ollama...")
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json" if options.get('format') == 'json' else "",
            "options": options
        }
        # Increased timeout for CPU (Long generation needs more time)
        # 180 -> 300 seconds (5 minutes)
        res = requests.post("http://localhost:11434/api/generate", json=payload, timeout=300)
        
        logging.info(f"✅ Ollama Response: {res.status_code}")
        if res.status_code == 200:
            return res.json().get('response', '').strip()
            
    except Exception as e:
         logging.error(f"❌ Local Ollama Failed: {e}")
         raise e
         
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
             # Try parse JSON
             try:
                 data = json.loads(raw)
                 comment = data.get('comment', '')
                 emotion = data.get('emotion', '')
                 score = data.get('score', 5)

                 # [Fix] Fallback for empty emotion
                 if not emotion:
                     if score >= 8: emotion = "행복"
                     elif score >= 6: emotion = "기쁨"
                     elif score >= 5: emotion = "평온"
                     elif score >= 3: emotion = "불안"
                     else: emotion = "우울"
                 
                 return comment, emotion, score
             except Exception as e:
                 print(f"⚠️ JSON Parse Failed. Error: {e} | Raw: {raw}")
                 # Try to salvage raw text if it looks like a comment
                 if len(raw) > 10 and "{" not in raw:
                     return raw, "분석중", 5
                 return raw, "분석중", 5
    except Exception as e:
        print(f"❌ AI Gen Error: {e}")
    return "당신의 마음을 깊이 응원합니다. (AI 분석 지연)", "대기중", 5


# Set up logging
logging.basicConfig(
    filename='ai_worker.log', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_analysis_process(diary_id, date, event, sleep, emotion_desc, emotion_meaning, self_talk):
    logging.info(f"🧵 [Thread] Starting Analysis for Diary {diary_id}...")
    print(f"🧵 [Thread] Starting Analysis for Diary {diary_id}...")
    
    # 1. Generate Comment & Emotion & Score
    full_text = f"날짜: {date}\n수면: {sleep}\n사건: {event}\n감정: {emotion_desc}\n의미: {emotion_meaning}\n스스로에게: {self_talk}"
    # Remove None or empty strings from formatting if needed, but simple string interpolation is fine
    
    comment, emotion, score = generate_ai_analysis(full_text)
    
    # ... (rest is same, but let's include it to be safe or use Context)
    print(f"🤖 AI Result - Score: {score}, Emotion: {emotion}, Comment: {comment[:20]}...")

    # 2. Encrypt
    enc_comment = crypto.encrypt(comment)
    enc_emotion = crypto.encrypt(emotion)
    
    # 3. Update DB
    # 3. Update DB
    try:
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            conn = psycopg2.connect(db_url)
        else:
            conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        # conn.autocommit = True # [Fix] Use manual commit for rollback safety
        cur = conn.cursor()
        
        # Ensure score is integer and within range
        try:
            score = int(score)
            score = max(1, min(10, score))
        except:
            score = 5

        # [Resilient Update Strategy]
        # Try 'mood_score' first (Legacy/Current Schema?)
        try:
            cur.execute(
                "UPDATE diaries SET ai_comment = %s, ai_emotion = %s, mood_score = %s WHERE id = %s", 
                (enc_comment, enc_emotion, score, diary_id)
            )
            conn.commit()
            print(f"✅ [Thread] Database Updated (mood_score)")
        except Exception as e:
            conn.rollback()
            print(f"⚠️ [Thread] 'mood_score' update failed, trying 'mood_intensity': {e}")
            
            # Try 'mood_intensity' (Models.py Schema)
            try:
                cur.execute(
                    "UPDATE diaries SET ai_comment = %s, ai_emotion = %s, mood_intensity = %s WHERE id = %s", 
                    (enc_comment, enc_emotion, score, diary_id)
                )
                conn.commit()
                print(f"✅ [Thread] Database Updated (mood_intensity)")
            except Exception as e2:
                conn.rollback()
                print(f"⚠️ [Thread] 'mood_intensity' update failed, fallback to basic update: {e2}")
                
                # Fallback: Update only AI fields
                cur.execute(
                    "UPDATE diaries SET ai_comment = %s, ai_emotion = %s WHERE id = %s", 
                    (enc_comment, enc_emotion, diary_id)
                )
                conn.commit()
                print(f"✅ [Thread] Database Updated (Basic)")
        
        print(f"✅ [Thread] Analysis Complete for Diary {diary_id}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ [Thread] Final DB Update Failed: {e}")

def start_analysis_thread(diary_id, date, event, sleep, emotion_desc, emotion_meaning, self_talk):
    print(f"🧵 [Main] Spawning Analysis Thread for Diary {diary_id}")
    logging.info(f"🧵 [Main] Spawning Analysis Thread for Diary {diary_id}")
    t = threading.Thread(target=run_analysis_process, args=(diary_id, date, event, sleep, emotion_desc, emotion_meaning, self_talk))
    t.start()
