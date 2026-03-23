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

# [Task Version Lock] 동시 수정으로 인한 과거 데이터의 덮어쓰기 현상(Race Condition) 방어 로직
_active_tasks = {}
_task_lock = threading.Lock()

# PG Config — [Fix#11] 환경변수 필수, 기본값에서 비밀번호 하드코딩 제거
DB_NAME = os.environ.get("DB_NAME", "vibe_db")
DB_USER = os.environ.get("DB_USER", "vibe_user")
DB_PASS = os.environ.get("DB_PASS", "")  # [Fix#11] 비밀번호 하드코딩 제거 (환경변수 필수)
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")


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
                             except Exception:
                                 try:
                                     inner = ast.literal_eval(clean_str)
                                 except Exception:
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
                             except Exception:
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
             # Make sure markdown wrappers are stripped
             clean_raw = raw.strip()
             if clean_raw.startswith('```'):
                 clean_raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', clean_raw, flags=re.MULTILINE).strip()
                 
             # Try parse JSON
             try:
                 data = json.loads(clean_raw)
                 comment = data.get('comment', '')
                 emotion = data.get('emotion', '')
                 raw_score = data.get('score', 5)
                 
                 try:
                     score = int(raw_score)
                 except (ValueError, TypeError):
                     score = 5

                 # [Fix] 프롬프트 예시 텍스트가 그대로 반환된 경우 garbage 판정 → fallback
                 GARBAGE_PATTERNS = [
                     "위로의 메시지", "핵심감정단어", "분위기 파악", "다음 분위기",
                     "감정단어하나", "조언", "메시지...", "...", "example"
                 ]
                 is_garbage = (
                     not comment or
                     not emotion or
                     any(p in str(comment) for p in GARBAGE_PATTERNS) or
                     any(p in str(emotion) for p in GARBAGE_PATTERNS) or
                     len(str(comment).strip()) < 10
                 )
                 if is_garbage:
                     print(f"⚠️ [GarbageFilter] AI가 프롬프트 예시를 그대로 반환했습니다. Fallback 적용. comment='{comment[:30]}', emotion='{emotion}'")
                     return "당신의 마음을 깊이 응원합니다. (AI 분석 지연)", "대기중", 5

                 # [Fix] Fallback for empty emotion
                 if not emotion:
                     if score >= 8: emotion = "행복"
                     elif score >= 6: emotion = "기쁨"
                     elif score >= 5: emotion = "평온"
                     elif score >= 3: emotion = "불안"
                     else: emotion = "우울"
                 
                 return comment, emotion, score
             except Exception as e:
                 print(f"⚠️ JSON Parse Failed. Error: {e} | Raw: {clean_raw}")
                 # Try to salvage raw text if it looks like a comment
                 if len(clean_raw) > 10 and "{" not in clean_raw:
                     return clean_raw, "분석중", 5
                 return clean_raw, "분석중", 5
    except Exception as e:
        print(f"❌ AI Gen Error: {e}")
    return "당신의 마음을 깊이 응원합니다. (AI 분석 지연)", "대기중", 5


# Set up logging
logging.basicConfig(
    filename='ai_worker.log', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_analysis_process(diary_id, date, event, sleep, emotion_desc, emotion_meaning, self_talk, task_version=None):
    logging.info(f"🧵 [Thread] Starting Analysis for Diary {diary_id}...")
    print(f"🧵 [Thread] Starting Analysis for Diary {diary_id}...")
    
    # 1. Generate Comment & Emotion & Score
    full_text = f"날짜: {date}\n수면: {sleep}\n사건: {event}\n감정: {emotion_desc}\n의미: {emotion_meaning}\n스스로에게: {self_talk}"
    
    # [NativeRAG] 과거 기억 검색하여 프롬프트에 주입
    user_id = None
    mood_level = 3
    try:
        # diary_id로 user_id와 mood_level을 찾아야 함
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            tmp_conn = psycopg2.connect(db_url)
        else:
            tmp_conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        try:
            tmp_cur = tmp_conn.cursor()
            tmp_cur.execute("SELECT user_id, mood_level FROM diaries WHERE id = %s", (diary_id,))
            row = tmp_cur.fetchone()
            tmp_cur.close()
        finally:
            tmp_conn.close()
        
        if row:
            user_id = row[0]
            mood_level = row[1] if row[1] is not None else 3
            
            # [Fix] RAG 검색 시 event뿐만 아니라 전체 내용을 통합 검색하여 사각지대(Blind Spot) 방지
            search_query = " ".join(filter(None, [event, emotion_desc, emotion_meaning, self_talk]))
            if not search_query.strip():
                search_query = "일기 내용 없음"
                
            from memory_manager import recall_memories
            past_context = recall_memories(user_id, search_query, limit=5, exclude_diary_id=diary_id)
            if past_context:
                full_text = f"{past_context}\n\n【오늘의 일기】\n{full_text}"
                print(f"🧠 [NativeRAG] 유저 {user_id}의 과거 기억 주입 완료")
    except Exception as mem_err:
        print(f"⚠️ [NativeRAG] 기억 검색 스킵: {mem_err}")
    
    comment = "분석 중 오류가 발생했습니다."
    emotion = "기타"
    score = 5
    
    try:
        result = generate_ai_analysis(full_text)
        if isinstance(result, tuple) and len(result) >= 3:
            # 안전하게 None 방어
            comment = str(result[0] or "분석 중 오류가 발생했습니다.")
            emotion = str(result[1] or "기타")
            raw_score = result[2]
            try:
                score = int(raw_score)
                score = max(1, min(10, score))
            except (ValueError, TypeError):
                pass
    except Exception as ai_err:
        print(f"❌ [Thread] AI Analysis failed, using fallback: {ai_err}")
    
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
            
        try:
            cur = conn.cursor()
            
            # [Race Condition Prevention] 현재 쓰레드가 가장 최신의 태스크인지 확인
            if task_version is not None:
                with _task_lock:
                    if _active_tasks.get(diary_id) != task_version:
                        print(f"🚫 [Thread] 일기 {diary_id}에 대해 더 최신 수정(Task)이 감지되었습니다. 이전 AI 분석 덮어쓰기를 중단합니다.")
                        return
                    else:
                        # DB 업데이트가 안전하므로 락 리스트에서 비웁니다
                        del _active_tasks[diary_id]
                        
            # Ensure score is integer and within range
            try:
                score = int(score)
                score = max(1, min(10, score))
            except (ValueError, TypeError):
                score = 5

            # [Resilient Update Strategy]
            affected_rows = 0
            try:
                cur.execute(
                    "UPDATE diaries SET ai_comment = %s, ai_emotion = %s, mood_score = %s WHERE id = %s", 
                    (enc_comment, enc_emotion, score, diary_id)
                )
                affected_rows = cur.rowcount
                conn.commit()
                print(f"✅ [Thread] Database Updated (mood_score)")
            except Exception as e:
                conn.rollback()
                print(f"⚠️ [Thread] 'mood_score' update failed, trying 'mood_intensity': {e}")
                
                try:
                    cur.execute(
                        "UPDATE diaries SET ai_comment = %s, ai_emotion = %s, mood_intensity = %s WHERE id = %s", 
                        (enc_comment, enc_emotion, score, diary_id)
                    )
                    affected_rows = cur.rowcount
                    conn.commit()
                    print(f"✅ [Thread] Database Updated (mood_intensity)")
                except Exception as e2:
                    conn.rollback()
                    print(f"⚠️ [Thread] 'mood_intensity' update failed, fallback to basic update: {e2}")
                    
                    cur.execute(
                        "UPDATE diaries SET ai_comment = %s, ai_emotion = %s WHERE id = %s", 
                        (enc_comment, enc_emotion, diary_id)
                    )
                    affected_rows = cur.rowcount
                    conn.commit()
                    print(f"✅ [Thread] Database Updated (Basic)")
            
            if affected_rows == 0:
                print(f"🚫 [Thread] 일기 {diary_id}가 이미 삭제되었거나 존재하지 않습니다. RAG 저장을 취소합니다. (Zombie Resurrection 방지)")
                cur.close()
                return

            print(f"✅ [Thread] Analysis Complete for Diary {diary_id}")
            cur.close()
        finally:
            conn.close()
            
        # [KILLER FEATURE] AI 분석 완료 푸시 전송 (보호자에게 리포트 전송)
        if user_id is not None and comment and "오류가 발생" not in comment and emotion not in ["기타", "대기중"]:
            try:
                from push_service import notify_guardians_ai_report
                from app import app
                print(f"💌 [Push] 트리거: 보호자에게 AI 분석 결과 전송 (User: {user_id})")
                with app.app_context():
                    notify_guardians_ai_report(user_id, comment)
            except Exception as pe:
                print(f"⚠️ [Push] AI 리포트 푸시 알림 발송 중 에러: {pe}")
        
        # [NativeRAG] AI 분석 코멘트까지 포함하여 장기 기억에 저장
        if user_id is not None:
            if "오류가 발생" in comment or emotion in ["기타", "대기중"]:
                print("⚠️ [NativeRAG] Fallback(오류) 응답 발생으로 인해, RAG 저장(기억 오염 방지)을 생략합니다.")
            else:
                try:
                    from memory_manager import store_diary_memory
                    combined_emotion = f"사용자입력감정:{emotion_desc} / AI진단감정:{emotion}" if emotion_desc else emotion
                    
                    # [Fix] RAG 저장 시에도 event뿐만 아니라 모든 사용자 입력 맥락을 보존
                    integrated_text = " ".join(filter(None, [event, emotion_meaning, self_talk]))
                    
                    store_diary_memory(
                        diary_id=diary_id,
                        user_id=user_id,
                        diary_text=integrated_text,
                        mood_level=mood_level,
                        emotion_desc=combined_emotion,
                        ai_comment=comment,
                        diary_date=date
                    )
                except Exception as store_err:
                    print(f"⚠️ [NativeRAG] 메모리 저장 실패: {store_err}")
                
    except Exception as e:
        print(f"❌ [Thread] Final DB Update Failed: {e}")

def start_analysis_thread(diary_id, date, event, sleep, emotion_desc, emotion_meaning, self_talk):
    # 동일한 일기에 대한 중복/지연 업데이트 방지 체계 (Task Versioning)
    with _task_lock:
        task_version = _active_tasks.get(diary_id, 0) + 1
        _active_tasks[diary_id] = task_version

    print(f"🧵 [Main] Spawning Analysis Thread for Diary {diary_id} (v{task_version})")
    logging.info(f"🧵 [Main] Spawning Analysis Thread for Diary {diary_id} (v{task_version})")
    t = threading.Thread(target=run_analysis_process, args=(diary_id, date, event, sleep, emotion_desc, emotion_meaning, self_talk, task_version))
    t.start()
