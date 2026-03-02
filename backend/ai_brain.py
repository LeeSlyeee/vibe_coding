import numpy as np
import os
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config
import json
import requests
import re
import time
import ast # Added for safe literal eval
TRAINING_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'training_state.json')

try:
    from emotion_codes import EMOTION_CODE_MAP
except ImportError:
    print("Warning: Could not import EMOTION_CODE_MAP from emotion_codes")
    EMOTION_CODE_MAP = {}

# TensorFlow/Keras Import (Optional)
try:
    raise ImportError("Disabled to prevent mutex crash on macOS")
    if False and os.getenv("ENABLE_TF"): # Disabled by default to fix Mac M1/M2 mutex crash
        from tensorflow.keras.preprocessing.text import Tokenizer
    from tensorflow.keras.preprocessing.sequence import pad_sequences
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import Embedding, LSTM, Dense, Dropout, Input
    from tensorflow.keras.utils import to_categorical
    import pandas as pd
    TENSORFLOW_AVAILABLE = True
    print("AI Brain: TensorFlow Available.")
except ImportError as e:
    TENSORFLOW_AVAILABLE = False
    print(f"AI Brain: Local Emotion Model support skipped ({e}).")



class EmotionAnalysis:
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.max_len = 50
        self.vocab_size = 0
        
        # 60 Ultra-Fine-Grained Emotion Classes
        self.sorted_codes = sorted(EMOTION_CODE_MAP.keys())
        self.classes = [EMOTION_CODE_MAP[code] for code in self.sorted_codes]
        self.code_to_idx = {code: i for i, code in enumerate(self.sorted_codes)}
        
        # We will load keywords from DB for fallback/learning
        try:
            from pymongo import MongoClient
            from config import Config
            self.mongo_client = MongoClient(Config.MONGO_URI)
            self.db = self.mongo_client.get_database() # Uses default db from URI
            print("AI Brain: Connected to MongoDB.")
        except Exception as e:
            print(f"AI Brain: MongoDB Connection Failed: {e}")
            self.db = None

        self.train_texts = []
        self.train_labels = np.array([], dtype=int)
        
        self.comment_bank = {} # Will load from file

        
        # Initialize attributes
        # Removed Polyglot-Ko attributes

               
        # === Tensorflow / LSTM Model Logic ===
        if TENSORFLOW_AVAILABLE:
            self.tokenizer = Tokenizer()
            # Check for saved model
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.model_path = os.path.join(base_dir, 'emotion_model.h5')
            self.tokenizer_path = os.path.join(base_dir, 'tokenizer.pickle')
            
            # Check Training Condition
            current_count = self._get_keyword_count()
            last_count = self._get_last_trained_count()
            diff = current_count - last_count
            
            print(f"📊 Training Check: Current Keywords={current_count}, Last Trained={last_count}, Diff={diff}")
            
            should_train = (diff >= 100)
            model_exists = os.path.exists(self.model_path) and os.path.exists(self.tokenizer_path)

            if should_train:
                print("⚠️ Should train, but skipping for now to rely on Local LLM/Fallback.")
                self._save_training_state(current_count)
            elif model_exists:
                print("📦 Models found. Loading existing models...")
                self._load_existing_models()
                print("✅ Emotion Model loaded.")
            else:
                print("⚠️ No models found. Using Keyword Fallback.")
            
            print("AI Model initialization finished.")

        else: # TENSORFLOW NOT AVAILABLE
             print("Initializing Fallback Emotion Analysis (Keyword based - 5 classes)...")

        # Load Comment Bank (Safety Net) - Always load this
        self.load_comment_bank()
        self.load_emotion_bank()

    def _sanitize_context(self, text):
        """
        Privacy Guard: Removes potential sensitive information before sending to external API.
        - Truncates long text
        - Focuses on sentiment-carrying words
        """
        if not text: return ""
        # Simple privacy protection: Remove common patterns (emails, phone numbers)
        import re
        text = re.sub(r'[\w\.-]+@[\w\.-]+', '[EMAIL]', text)
        text = re.sub(r'\d{2,3}-\d{3,4}-\d{4}', '[PHONE]', text)
        
        # To further protect privacy, we could use the local emotion results 
        # instead of raw text, but for 'insight' we need some context.
        # We limit the length to prevent sending too much detail.
        return text[:100].strip() + "..." if len(text) > 100 else text

    def _get_keyword_count(self):

        """Get total count of emotion keywords from DB (MongoDB)"""
        if self.db is None:
            return 0
        try:
            count = self.db.emotion_keywords.count_documents({})
            return count
        except Exception as e:
            print(f"Error counting keywords: {e}")
            return 0

    def _get_last_trained_count(self):
        """Read last trained count from JSON"""
        if os.path.exists(TRAINING_STATE_FILE):
            try:
                with open(TRAINING_STATE_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('last_keyword_count', 0)
            except:
                return 0
        return 0

    def _save_training_state(self, count):
        """Save current keyword count to JSON"""
        try:
            with open(TRAINING_STATE_FILE, 'w') as f:
                json.dump({'last_keyword_count': count}, f)
        except Exception as e:
            print(f"Error saving training state: {e}")

    def _load_existing_models(self):
        """Helper to load existing models"""
        try:
            import pickle
            from tensorflow.keras.models import load_model
            
            self.model = load_model(self.model_path)
            
            with open(self.tokenizer_path, 'rb') as handle:
                self.tokenizer = pickle.load(handle)
                
            self.vocab_size = len(self.tokenizer.word_index) + 1
            print("Emotion Model loaded.")
                
        except Exception as e:
            print(f"Error loading models: {e}.")
            # Assuming fallback will take over

    def load_comment_bank(self):
        """Load curated advice from JSON"""
        try:
            import json
            base_dir = os.path.dirname(os.path.abspath(__file__))
            bank_path = os.path.join(base_dir, 'data', 'comment_bank.json')
            if os.path.exists(bank_path):
                with open(bank_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.comment_bank = data.get('keywords', {})
                print(f"Loaded {len(self.comment_bank)} keyword categories from Comment Bank.")
            else:
                print("Comment Bank file not found. Skipping.")
        except Exception as e:
            print(f"Error loading comment bank: {e}")

    def generate_keyword_comment(self, user_input):
        """Phase 1: Hybrid Keyword System (Priority 1)"""
        if not self.comment_bank or not user_input:
            return None
            
        # Extract text if input is dict
        if isinstance(user_input, dict):
            text = f"{user_input.get('event', '')} {user_input.get('emotion', '')} {user_input.get('self_talk', '')}"
        else:
            text = str(user_input)
            
        for category, content in self.comment_bank.items():
            # Safety check: content must be a dict
            if not isinstance(content, dict):
                continue
                
            if category in text:
                return content.get('default', "마음이 전해집니다.")
                
            keywords = content.get('emotion_keywords', [])
            for k in keywords:
                if k in text:
                    return content.get('default', "마음이 전해집니다.")
        return None

    def load_emotion_bank(self):
        """Load 60-class emotion advice"""
        try:
            import json
            base_dir = os.path.dirname(os.path.abspath(__file__))
            bank_path = os.path.join(base_dir, 'data', 'emotion_comment_bank.json')
            if os.path.exists(bank_path):
                with open(bank_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.emotion_bank = data.get('keywords', {}) # Structure reuse
                print(f"Loaded {len(self.emotion_bank)} emotion categories.")
            else:
                self.emotion_bank = {}
        except Exception as e:
            print(f"Error loading emotion bank: {e}")
            self.emotion_bank = {}

    def generate_label_comment(self, emotion_label):
        """Phase 1.5: Label-Based Retrieval (Priority 2)"""
        if not self.emotion_bank:
            return None
            
        try:
            if '(' in emotion_label:
                label_key = emotion_label.rsplit(' (', 1)[0]
                pass
            else:
                label_key = emotion_label
        except:
             label_key = emotion_label
        
        # Exact match attempt
        if label_key in self.emotion_bank:
            return self.emotion_bank[label_key].get('default')
            
        # Fuzzy match 
        for key in self.emotion_bank:
            if key in emotion_label:
                return self.emotion_bank[key].get('default')
        
        return None
        



    
    def generate_pre_write_insight(self, recent_diaries, weather=None, weather_stats=None):
        """
        Generates a warm insight using Local Gemma 2 (Ollama).
        """
        import requests
        import json

        print(f"🔍 [Insight] Request received. Recent diaries count: {len(recent_diaries)}, Weather: {weather}")
        
        if not recent_diaries:
            return "오늘의 첫 기록을 시작해보세요! 솔직한 마음을 담으면 됩니다."

        try:
            # Construct Prompt
            diary_context = ""
            for d in recent_diaries:
                sanitized_event = self._sanitize_context(d.get('event',''))
                diary_context += f"- [{d.get('date','')}] 기분:{d.get('mood','')} / 내용:{sanitized_event}\n"

            weather_info = f"오늘의 날씨: {weather}" if weather else "오늘의 날씨 정보 없음"
            stats_info = f" (과거 이 날씨에 당신은 주로 {weather_stats} 감정을 느끼셨네요)" if weather_stats else ""

            prompt_text = (
                "당신은 사용자의 지난 일기 기록과 오늘의 날씨, 그리고 '과거 날씨별 감정 패턴'을 분석하여 따뜻한 한 문장의 조언을 건네는 감정 케어 도우미입니다.\n\n"
                f"### {weather_info}{stats_info}\n"
                "### 사용자의 최근 1주일 흐름\n"
                f"{diary_context}\n"
                "### 지시사항\n"
                "1. 반드시 '한 문장'으로 작성하세요.\n"
                "2. [필수] 오늘의 날씨나 계절감을 언급하며 시작하세요. (예: '비가 오는 날엔...', '맑은 햇살처럼...')\n"
                "3. 최근 1주일간의 감정 흐름이 좋은지 나쁜지를 반드시 반영하여 개인화된 조언을 하세요.\n"
                "4. '오늘 하루 응원합니다' 같은 뻔한 말은 금지입니다.\n"
                "5. 40자~80자 내외로 부드러운 존댓말(해요체)을 사용하세요.\n\n"
                "마음온 조언(날씨와 감정 흐름이 통합된 한 문장):"
            )

            # Ollama Payload
            payload = {
                "model": "maumON-gemma", # Use Custom Model Name
                "prompt": prompt_text,
                "stream": False,
                "options": {
                    "temperature": 0.5,
                    "num_predict": 60 
                }
            }
            
            print(f"🦙 [Insight] Requesting Ollama (Maum-On Gemma)...")
            url = "http://localhost:11434/api/generate"
            
            # Timeout Increased to 60s (OCI CPU might be slow or busy)
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code != 200:
                print(f"❌ Ollama Insight Error {response.status_code}: {response.text}")
                return None
                
            result = response.json()
            response_text = result.get('response', '').strip()
            
            # Cleanup quotes if model adds them
            if response_text.startswith('"') and response_text.endswith('"'):
                response_text = response_text[1:-1]
                
            print(f"✅ [Insight] Gemma Success: {response_text}")
            return response_text

        except Exception as e:
            print(f"❌ [Insight] Inference Failed: {str(e)}")
            return None

    def analyze_diary_with_local_llm(self, text, history_context=None, user_risk_level=1):
        # [Local AI Mode] Uses Local Ollama (Gemma 2) for Analysis.
        import requests
        import json
        
        # Local Ollama URL
        print(f"🦙 [Local AI] Requesting Ollama (Maum-On Gemma)...", end=" ", flush=True)
        try:
            url = "http://localhost:11434/api/generate"
            
            # Context Injection
            context_section = ""
            if history_context:
                context_section = (
                    f"### [참고: 내담자의 과거 기록]\n"
                    f"{history_context}\n"
                    f"(지침: 위 과거 기록의 흐름을 참고하여, 맥락이 이어지는 깊이 있는 공감 멘트를 작성해줘.)\n\n"
                )

            # Risk Level Context
            risk_desc = "안정(Normal)"
            if user_risk_level >= 4: risk_desc = "매우 위험(Severe Risk)"
            elif user_risk_level == 3: risk_desc = "위험(Moderate Risk)"
            
            # [Phase 4] 3단계 위기 분류 시스템
            CRISIS_LEVEL_3 = ["죽고", "자살", "뛰어내", "목을", "손목", "유서", "마지막", "끝내고", "자해", "목숨"]
            CRISIS_LEVEL_2 = ["사라지고", "없어지고", "살기 싫", "의미 없", "끝내", "망했", "수면제", "칼", "약 먹", "다 끝"]
            CRISIS_LEVEL_1 = ["힘들", "지치", "우울", "불안", "두렵", "외로", "무서", "포기", "눈물"]
            
            found_l3 = [k for k in CRISIS_LEVEL_3 if k in text]
            found_l2 = [k for k in CRISIS_LEVEL_2 if k in text]
            found_l1 = [k for k in CRISIS_LEVEL_1 if k in text]
            
            if found_l3:
                crisis_level = 3
                found_keywords = found_l3
            elif found_l2:
                crisis_level = 2
                found_keywords = found_l2
            elif found_l1:
                crisis_level = 1
                found_keywords = found_l1
            else:
                crisis_level = 0
                found_keywords = []
            
            is_urgent_risk = crisis_level >= 2
            
            danger_note = ""
            if crisis_level >= 3:
                print(f"🚨 [Analysis] LEVEL 3 CRISIS: {found_keywords}")
                danger_note = f"\n[긴급 위험 Level 3: 내담자가 '{found_keywords}'와 같은 매우 위험한 표현을 사용했습니다. 반드시 안전 확인 질문을 하고 전문 상담 기관(1393) 연결을 안내하세요. '힘내세요', '긍정적으로 생각하세요' 같은 표현은 절대 사용하지 마세요.]"
            elif crisis_level >= 2:
                print(f"⚠️ [Analysis] LEVEL 2 RISK: {found_keywords}")
                danger_note = f"\n[주의 Level 2: 내담자가 '{found_keywords}'와 같은 간접적 위험 표현을 사용했습니다. Followup을 YES로 하고 부드럽게 안전을 확인하세요. 섣부른 조언이나 '힘내세요' 같은 표현은 피하세요.]"
            elif crisis_level >= 1:
                print(f"💛 [Analysis] LEVEL 1 CONCERN: {found_keywords}")
                danger_note = ""  # Level 1은 AI에게 특별 지시 불요, 기본 공감 대응

            prompt_text = (
                f"너는 감정 분석 전문가야. 다음 내담자의 일기를 읽고 분석해줘.\n"
                f"내담자의 현재 상태: {risk_desc} (Level {user_risk_level})\n"
                f"{context_section}"
                f"{danger_note}\n"
                f"### [오늘의 일기 데이터]:\n{text}\n\n"
                f"### [분석 지침]:\n"
                f"1. 내담자의 '수면 상태'와 '감정'의 연관성을 깊이 있게 분석해줘.\n"
                f"2. 만약 내담자가 '죽고 싶다' 등 위험한 표현을 했거나({found_keywords}), 감정이 오랫동안 가라앉아 있다면 '추가 질문'을 생성해줘.\n"
                f"3. 단순히 내용을 요약하지 말고, 전문적인 감정 분석 코멘트를 해줘.\n\n"
                f"### [필수 답변 형식]:\n"
                f"Emotion: ('행복', '우울', '분노', '평온', '불안', '당황' 중 하나, 반드시 한국어로)\n"
                f"Confidence: (0~100 숫자만)\n"
                f"NeedFollowup: (YES 또는 NO)\n"
                f"Question: (NeedFollowup이 YES일 때만, 내담자에게 물어볼 추가 질문 1문장. 아니면 'None')\n"
                f"Comment: (수면 상태를 언급하며 100자 이내의 따뜻한 한국어 위로)\n"
                f"반드시 위 형식만 지켜서 답변해."
            )
            
            payload = {
                "model": "maumON-gemma",
                "prompt": prompt_text,
                "stream": False,
                "options": {
                    "temperature": 0.3, 
                    "num_predict": 160 # Optimized for Speed (OCI CPU)
                }
            }
            
            # Timeout 60s
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code != 200:
                print(f"❌ Ollama Error {response.status_code}: {response.text}")
                return None, None
                
            result = response.json()
            response_text = result.get('response', '').strip()
            print(f"🔍 Raw Output: {response_text}")
            
            # Use Regex to parse Korean output
            import re
            
            # 1. Emotion (Korean)
            emotion_match = re.search(r"Emotion:\s*([^\n]+)", response_text)
            emotion_str = emotion_match.group(1).strip().replace("'", "").replace('"', "") if emotion_match else "평온"
            
            # 2. Confidence
            conf_match = re.search(r"Confidence:\s*(\d+)", response_text)
            confidence = int(conf_match.group(1)) if conf_match else 80

            # 3. Followup
            need_followup_match = re.search(r"NeedFollowup:\s*([^\n]+)", response_text, re.IGNORECASE)
            
            # 4. Comment
            comment_match = re.search(r"Comment:\s*(.*)", response_text, re.DOTALL)
            comment = comment_match.group(1).strip() if comment_match else response_text[:100]
            
            if comment.startswith('"') and comment.endswith('"'): comment = comment[1:-1]
            
            # Final Formatting
            formatted_prediction = f"'{emotion_str} ({confidence}%)'"
            
            return formatted_prediction, comment
                
        except Exception as e:
            print(f"❌ Local AI Error: {e}")
            return None, None

    def predict(self, text):
        import time
        start_time = time.time()
        
        if not text: 
            return {"emotion": "분석 불가", "comment": "내용이 없습니다."}

        emotion_result = "분석 불가"
        
        # [User Request] Gemma-First Analysis
        try:
            llm_emotion, llm_comment = self.analyze_diary_with_local_llm(text)
            if llm_emotion:
                 emotion_result = llm_emotion
            else:
                 emotion_result = self._fallback_predict(text)
            
            # Store comment for next step
            self.temp_llm_comment = llm_comment
        except:
            emotion_result = self._fallback_predict(text)
            self.temp_llm_comment = None
            
        # 2. Comment Generation
        comment_result = getattr(self, 'temp_llm_comment', None)
        
        # Final Fallback
        if not comment_result:
            comment_result = self.generate_keyword_comment(text) or "오늘 하루도 정말 수고하셨어요."
            
        print(f"✨ [Timer] Total AI Analysis took: {time.time() - start_time:.3f}s")
        return {
            "emotion": emotion_result,
            "comment": comment_result
        }

    def _fallback_predict(self, text):
        # Load keywords from MongoDB
        if self.db is None:
             return "분석 불가"

        try:
            # Fetch all keywords from Mongo
            keywords = list(self.db.emotion_keywords.find())
            
            scores = [0] * 5
            found_any = False
            
            for kw in keywords:
                if kw['keyword'] in text:
                    scores[kw['emotion_label']] += kw['frequency']
                    found_any = True
            
            if found_any:
                max_score = max(scores)
                total_score = sum(scores)
                confidence = (max_score / total_score * 100) if total_score > 0 else 85.0
                best_idx = scores.index(max_score)
                return f"{self.classes[best_idx]} ({confidence:.1f}%)"
            else:
                return "그저그래 (40.0%)" 
        except Exception as e:
            print(f"Fallback error: {e}")
            return "분석 불가"

    def generate_comment(self, prediction_text, user_text=None):
        # Generate a supportive comment.
        # Priority: 1. Keyword Bank (Safety Net) 2. AI Generation (Seq2Seq) 3. Fallback
        if user_text:
             # Try Local LLM First if available (or assume it was already tried in predict)
             # But here this method is likely legacy or fallback. 
             pass


        # 1. Phase 1: Keyword Safety Net (Highest Priority)
        if user_text:
            keyword_comment = self.generate_keyword_comment(user_text)
            if keyword_comment:
                 return keyword_comment

        if not prediction_text or "분석 불가" in prediction_text:
            return "당신의 이야기를 더 들려주세요. 항상 듣고 있을게요."

        # Extract strict label (remove confidence score)
        # e.g. "분노 (배신감) (85.0%)" -> "분노 (배신감)"
        try:
             emotion_label_only = prediction_text.rsplit(' (', 1)[0]
        except:
             emotion_label_only = prediction_text.split()[0]



        # 3. Phase 1.5: Label-based Specific Advice (Fallback)
        label_comment = self.generate_label_comment(emotion_label_only)
        if label_comment:
             return label_comment

        try:
            label = prediction_text.split()[0] # e.g. "행복해"
            
            # 4. Fallback
            return "오늘 하루도 수고 많으셨어요."
            
        except Exception as e:
            print(f"Comment Gen Error: {e}")
            return "당신의 마음을 이해해요."

    def _call_llm(self, prompt, options=None):
        """
        Hybrid/Async LLM Caller for Brain (RunPod Priority)
        """
        if options is None: options = {}
        
        # RunPod Config
        try:
            from config import Config
            RUNPOD_API_KEY = Config.RUNPOD_API_KEY
            RUNPOD_LLM_URL = Config.RUNPOD_LLM_URL
        except:
            RUNPOD_API_KEY = os.environ.get('RUNPOD_API_KEY')
            RUNPOD_LLM_URL = os.environ.get('RUNPOD_LLM_URL')

        # 1. RunPod Serverless (Priority)
        if RUNPOD_API_KEY and RUNPOD_LLM_URL and "YOUR_POD_ID" not in RUNPOD_LLM_URL:
            try:
                print("🚀 [Brain] Sending Async request to RunPod...")
                
                # Normalize Base URL
                base_url = RUNPOD_LLM_URL.replace('/runsync', '').replace('/run', '').rstrip('/')
                submit_url = f"{base_url}/run"
                
                headers = {
                    "Authorization": f"Bearer {RUNPOD_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "input": {
                        "prompt": prompt,
                        "max_tokens": options.get('num_predict', 2048),
                        "temperature": options.get('temperature', 0.7),
                        "stream": False
                    }
                }
                
                res = requests.post(submit_url, json=payload, headers=headers, timeout=30)
                if res.status_code != 200:
                    print(f"❌ RunPod Submit Failed: {res.text}")
                    raise Exception("RunPod Submit Failed")
                    
                job_id = res.json()['id']
                print(f"⏳ [Brain] Job Submitted: {job_id}. Polling...")
                
                status_url = f"{base_url}/status/{job_id}"
                start_time = time.time()
                
                while True:
                    if time.time() - start_time > 600: # 10 min timeout for reports
                         raise Exception("RunPod Timeout")
                         
                    status_res = requests.get(status_url, headers=headers, timeout=30)
                    status_data = status_res.json()
                    status = status_data.get('status')
                    
                    if status == 'COMPLETED':
                        output = status_data.get('output')
                        print("✅ [Brain] RunPod Job Completed!")
                        
                        # Process Output
                        if isinstance(output, dict):
                             # Try to get text field
                             if 'reaction' in output:
                                 clean_str = output['reaction'].strip()
                                 # Clean Markdown
                                 if clean_str.startswith('```'):
                                     clean_str = re.sub(r'^```(?:json)?\s*|\s*```$', '', clean_str, flags=re.MULTILINE)
                                 return clean_str.strip()
                             elif 'text' in output:
                                 return output['text']
                             elif 'response' in output:
                                 return output['response']
                             else:
                                 return json.dumps(output, ensure_ascii=False)
                        else:
                             return str(output)
                             
                    elif status in ['FAILED', 'CANCELLED']:
                        print(f"❌ RunPod Job Failed: {status}")
                        raise Exception(f"RunPod Failed: {status}")
                        
                    time.sleep(2)
                    
            except Exception as e:
                print(f"❌ RunPod Async Failed: {e}")
                # Fallthrough

        # 2. Local Ollama (Fallback)
        try:
            print("🦙 [Brain] Fallback to Local Ollama...")
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": options.get('model', 'gemma2:2b'),
                "prompt": prompt,
                "stream": False,
                "options": options
            }
            response = requests.post(url, json=payload, timeout=600)
            if response.status_code == 200:
                result = response.json().get('response', '')
                return result
        except Exception as e:
             print(f"❌ Local AI Failed: {e}")
             
        return None
    def generate_comprehensive_report(self, diary_summary):
        """
        Generates a detailed 10-paragraph psychological report using Hybrid AI (RunPod Priority).
        """
        print("🧠 [Brain] Generating Comprehensive Report...")
        
        prompt_text = (
            "## SYSTEM: You represent a thoughtful, empathetic counselor with 20 years of experience. You must ANSWER IN KOREAN ONLY.\n"
            "당신은 20년 경력의 베테랑 감정 분석 전문가입니다. 아래 내담자(사용자)의 일기 기록과 통계를 자세히 읽고 분석해주세요.\n\n"
            f"### [사용자 데이터]\n{diary_summary}\n\n"
            "### [작성 지침]\n"
            "1. **언어**: 반드시 **한국어(Korean)**로만 작성하세요. 영어는 절대 사용하지 마세요.\n"
            "2. **형식**: 사용자에게 보내는 '심층 감정 분석 리포트' 형식으로 작성하세요.\n"
            "3. **분량**: 반드시 **서론-본론(분석)-결론(제언)**의 흐름을 갖춘 **총 10문단 이상의 긴 글**이어야 합니다.\n"
            "4. **어조**: 전문적인 감정 분석 용어를 사용하되, 따뜻하고 이해하기 쉬운 언어로 풀어주세요.\n\n"
            "### [리포트 구조]\n"
            "1부. **마음의 지도 (현상 분석)** (5문단)\n"
            "   - 내담자가 주로 사용하는 감정 언어와 내면의 상태 분석\n"
            "   - 반복되는 스트레스 패턴이나 감정의 트리거 파악\n"
            "   - 숨겨진 긍정적인 자원이나 강점 발굴\n\n"
            "2부. **나아가야 할 길 (미래 제언)** (5문단)\n"
            "   - 현재 상태에서 실천할 수 있는 구체적인 감정 케어 방법 3가지 (마음챙김, 자기 기록 등 활용)\n"
            "   - 감정의 파도를 다스리는 생활 습관 제안\n"
            "   - 마음온으로서 전하는 진심 어린 격려와 희망의 메시지\n\n"
            "**주의사항: 이 분석은 참고용이며 전문 의료 서비스를 대체하지 않습니다.**\n"
            "**중요: 모든 답변은 완벽한 한국어로 작성되어야 합니다. 번역투가 아닌 자연스러운 한국어를 사용하세요.**\n"
            "지금 바로 한국어로 리포트 작성을 시작하세요."
        )
        
        try:
            options = {
                "model": "gemma2:2b", # For fallback
                "temperature": 0.7,
                "num_predict": 4096, # Max length for report
                "repeat_penalty": 1.1,
                "top_k": 40,
                "top_p": 0.9
            }
            
            result = self._call_llm(prompt_text, options)
            
            if result:
                return result
            else:
                return "죄송합니다. AI가 리포트를 작성하는 도중 연결이 끊겼습니다."

        except Exception as e:
            print(f"❌ Report Generation Error: {e}")
            return "리포트 생성 시스템에 오류가 발생했습니다."

    def generate_long_term_insight(self, report_history):
        """
        [Meta-Analysis] Analyzes multiple past reports to find long-term patterns.
        """
        import requests
        print(f"🧠 [Brain] Generating Long-Term Insight from {len(report_history)} reports...")
        
        if not report_history:
            return "분석할 과거 리포트 데이터가 충분하지 않습니다."
            
        try:
            url = "http://localhost:11434/api/generate"
            
            # Construct context from history
            history_context = ""
            for i, r in enumerate(report_history):
                date = r.get('date', 'Unknown Date')
                content = r.get('content', '')[:500] # Truncate to save context window
                history_context += f"### [리포트 {i+1} - {date}]\n{content}...\n\n"
                
            prompt_text = (
                "## SYSTEM: You represent a wise psychologist specializing in long-term therapy. Answer in KOREAN ONLY.\n"
                "당신은 내담자의 '과거 감정 분석 리포트들'을 종합하여 장기적인 변화와 흐름을 분석하는 '메타 분석가'입니다.\n"
                "아래 제공된 과거 리포트 기록들을 읽고, 내담자의 감정 상태가 시간의 흐름에 따라 어떻게 변화했는지 분석해주세요.\n\n"
                f"{history_context}\n"
                "### [작성 지침]\n"
                "1. **언어**: 반드시 **한국어**로 작성하세요.\n"
                "2. **구조**:\n"
                "   - **변화의 흐름**: 감정이나 태도가 어떻게 변해왔는지 (긍정적/부정적 변화)\n"
                "   - **반복되는 패턴**: 시간이 지나도 여전히 해결되지 않고 반복되는 문제점\n"
                "   - **장기 제언**: 앞으로의 1개월을 위한 핵심 조언\n"
                "3. **분량**: 3~4문단 내외로 깊이 있게 작성하세요.\n\n"
                "메타 분석 결과:"
            )
            
            payload = {
                "model": "gemma2:2b",
                "prompt": prompt_text,
                "stream": False,
                "options": {
                    "temperature": 0.6,
                    "num_predict": 2048
                }
            }
            
            response = requests.post(url, json=payload, timeout=300)
            
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                return "메타 분석 생성에 실패했습니다."
                
        except Exception as e:
            print(f"❌ Long-Term Insight Error: {e}")
            return "분석 중 오류가 발생했습니다."


    def update_keywords(self, text, mood_level):
        # Learn new keywords from the text based on the user's provided mood_level.
        if not text: return

        # Map mood_level to label
        # mood_level is expected to be int
        try:
            mood_val = int(mood_level)
            mapping = {5: 0, 4: 1, 3: 2, 2: 3, 1: 4}
            target_label = mapping.get(mood_val)
            
            if target_label is None:
                return # Invalid mood level
        except:
            return

        session = self.Session()
        try:
            from models import EmotionKeyword
            
            # Simple Tokenization (Space-based)
            # In a real KR app, use Mecab/Konlpy. Here we split by space.
            words = text.split()
            
            for w in words:
                # Basic cleaning
                w = w.strip('.,?!~"\'')
                if len(w) < 2: continue # Skip single chars
                
                # Check if exists
                existing = session.query(EmotionKeyword).filter_by(keyword=w).first()
                
                if existing:
                    # If exists, increment frequency if label matches
                    # If label differs, maybe decrease freq or ignore? 
                    # Let's just track co-occurrence. Complex logic omitted for simplicity.
                    if existing.emotion_label == target_label:
                        existing.frequency += 1
                else:
                    # NEW WORD -> LEARN IT!
                    print(f"Learning new keyword: {w} -> {self.classes[target_label]}")
                    new_kw = EmotionKeyword(
                        keyword=w,
                        emotion_label=target_label,
                        frequency=1
                    )
                    session.add(new_kw)
            
            session.commit()
            
            # If Model is active, we might want to update tokenizer or retrain eventually.
            # Rerunning Tokenizer.fit_on_texts would be needed. 
            # For this session, we won't retrain the LSTM live (too slow), but the Fallback logic will immediately benefit.
            
        except Exception as e:
            print(f"Learning error: {e}")
            session.rollback()
        finally:
            session.close()

