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
TRAINING_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'training_state.json')

try:
    from emotion_codes import EMOTION_CODE_MAP
except ImportError:
    print("Warning: Could not import EMOTION_CODE_MAP from emotion_codes")
    EMOTION_CODE_MAP = {}

# TensorFlow/Keras Import (Optional)
try:
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
    def __init__(self, light_mode=False):
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
        # [User Request] Switch to Full LLM (Gemma) Mode. Disabling LSTM loading.
        self.use_lstm = False 
        
        if self.use_lstm and TENSORFLOW_AVAILABLE and not light_mode:
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

        else: 
             print("Initializing Gemma-based Emotion Analysis (LSTM Disabled)...")

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
                return content.get('default', "힘내세요.")
                
            keywords = content.get('emotion_keywords', [])
            for k in keywords:
                if k in text:
                    return content.get('default', "힘내세요.")
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
                "당신은 사용자의 지난 일기 기록과 오늘의 날씨, 그리고 '과거 날씨별 감정 패턴'을 분석하여 따뜻한 한 문장의 조언을 건네는 심리 상담사입니다.\n\n"
                f"### {weather_info}{stats_info}\n"
                "### 사용자의 최근 1주일 흐름\n"
                f"{diary_context}\n"
                "### 지시사항\n"
                "1. 반드시 '한 문장'으로 작성하세요.\n"
                "2. [필수] 오늘의 날씨나 계절감을 언급하며 시작하세요. (예: '비가 오는 날엔...', '맑은 햇살처럼...')\n"
                "3. 최근 1주일간의 감정 흐름이 좋은지 나쁜지를 반드시 반영하여 개인화된 조언을 하세요.\n"
                "4. '오늘 하루 응원합니다' 같은 뻔한 말은 금지입니다.\n"
                "5. 40자~80자 내외로 부드러운 존댓말(해요체)을 사용하세요.\n\n"
                "상담사 조언(날씨와 감정 흐름이 통합된 한 문장):"
            )

            # Ollama Payload
            payload = {
                "model": "maum-on-gemma",
                "prompt": prompt_text,
                "stream": False,
                # No 'format': 'json' here because we want free text
                "options": {
                    "temperature": 0.5,
                    "num_predict": 100 
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

    def generate_chat_reaction(self, user_text):
        """
        Generates a rich, empathetic reaction to the user's chat input.
        """
        if not user_text: return None
        
        sanitized = self._sanitize_context(user_text)
        
        prompt_text = (
            f"내담자의 말: \"{sanitized}\"\n\n"
            "너는 다정하고 통찰력 있는 심리 상담사야. 내담자의 말을 듣고 **풍부한 공감과 긍정적인 피드백**을 해줘.\n"
            "지시사항:\n"
            "1. 내담자의 감정이나 행동을 구체적으로 언급하며 '그렇군요', '정말 ~하셨겠어요'라고 공감해.\n"
            "2. 그 행동이나 감정이 얼마나 소중한지, 또는 잘 대처했는지 칭찬해줘. (피드백)\n"
            "3. 말투는 따뜻하고 부드러운 '해요체'를 써.\n"
            "4. 질문은 하지 마. (다음 질문은 정해져 있어)\n"
            "5. 2~3문장으로 100자 이내로 작성해.\n\n"
            "리액션:"
        )
        
        try:
            payload = {
                "model": "maum-on-gemma",
                "prompt": prompt_text,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 150
                }
            }
            
            url = "http://localhost:11434/api/generate"
            response = requests.post(url, json=payload, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                reaction = result.get('response', '').strip()
                if reaction.startswith('"') and reaction.endswith('"'):
                    reaction = reaction[1:-1]
                return reaction
            return None
        except Exception as e:
            print(f"❌ Reaction Gen Error: {e}")
            # Fallback Reactions (Safety Net)
            fallbacks = [
                "그렇군요. 이야기해주셔서 정말 고마워요. 😌",
                "저런, 그런 일이 있으셨군요. 마음이 쓰이네요. 🥺",
                "정말 공감이 가요. 💭",
                "네, 계속 이야기해주세요. 제가 듣고 있어요. 👂",
                "어떤 기분인지 조금은 알 것 같아요. 💫"
            ]
            return random.choice(fallbacks)

    def _rebuild_inference_models(self):
        # Seq2Seq Removed
        pass

    # Function moved to end of file to fix indentation 

    def train_comment_model(self):
        # Seq2Seq Removed
        pass

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
            # This is inefficient for large datasets but ok for small keywords bank
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

    def load_sentiment_corpus(self):
        """
        Load 'Sentiment Dialogue Corpus' (Training & Validation).
        Use Full 60-Class Granularity (E10 ~ E69).
        """
        import json
        
        files = [
            '감성대화말뭉치(최종데이터)_Training.json',
            '감성대화말뭉치(최종데이터)_Validation.json'
        ]
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        import glob
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Use glob to avoid Unicode normalization issues (NFC vs NFD) on macOS
        files = glob.glob(os.path.join(base_dir, "*Training.json")) + glob.glob(os.path.join(base_dir, "*Validation.json"))
        
        if not files:
             print("No corpus files found via glob!")
        
        for fpath in files:
            fname = os.path.basename(fpath)
            # fpath is already absolute from glob
             
            print(f"Loading corpus: {fname}...")
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                new_texts = []
                new_labels = []
                
                for entry in data:
                    try:
                        etype = entry.get('profile', {}).get('emotion', {}).get('type', '')
                        
                        # Only use codes defined in our map (E10-E69)
                        if etype in self.code_to_idx:
                            # Extract user text
                            content = entry.get('talk', {}).get('content', {})
                            text = content.get('HS01', '')
                            system_text = content.get('SS01', '')
                            
                            if text:
                                label_idx = self.code_to_idx[etype]
                                new_texts.append(text)
                                new_labels.append(label_idx)
                                
                                # Store for comment training if pair exists
                                if system_text:
                                    self.conversation_pairs.append((text, system_text))
                                    
                    except Exception as e:
                        continue
                        
                # Add to training set
                self.train_texts.extend(new_texts)
                self.train_labels = np.concatenate((self.train_labels, np.array(new_labels)))
                
                print(f"Added {len(new_texts)} samples from {fname}")
                
            except Exception as e:
                print(f"Error loading corpus {fname}: {e}")


    def load_db_data(self):
        """
        Load data from the Diary table to fine-tune the model.
        Returns:
            X (list): Combined text (event + emotion_desc + self_talk)
            y (list): Emotion labels (0-4)
        """
        print("Loading data from Database...")
        session = self.Session()
        X = []
        y = []
        try:
            from models import Diary
            diaries = session.query(Diary).all()
            
            # Mood Level to Label Mapping
            # 5(Happy)->0, 4(Calm)->1, 3(Neutral)->2, 2(Depressed)->3, 1(Angry)->4
            mapping = {5: 0, 4: 1, 3: 2, 2: 3, 1: 4}
            
            for d in diaries:
                if not d.mood_level: continue
                
                label = mapping.get(d.mood_level)
                if label is None: continue
                
                # Combine text fields for rich context
                text = f"{d.event} {d.emotion_desc} {d.self_talk}"
                X.append(text)
                y.append(label)
                
            print(f"Loaded {len(X)} samples from Database.")
            return X, y
            
        except Exception as e:
            print(f"Error loading DB data: {e}")
            return [], []
        finally:
            session.close()





    def train_comment_model(self):
        """
        Train a Seq2Seq model using ChatbotData.csv AND Sentiment Dialogue Corpus
        """
        if not TENSORFLOW_AVAILABLE: return

        print("Training Comment Generation Model (Seq2Seq)...")
        try:
            import os
            import pickle
            
            # 1. Load ChatbotData.csv
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(base_dir, 'ChatbotData.csv')
            questions = []
            answers = []
            
            if os.path.exists(data_path):
                df = pd.read_csv(data_path)
                # Take a sample to keep training time reasonable, or all? 
                # Let's take mixed sample.
                df = df.sample(frac=1).reset_index(drop=True)
                questions = df['Q'].astype(str).tolist()[:5000] # Cap at 5000 for speed
                # Char-level: Use \t for Start, \n for End
                answers = df['A'].apply(lambda x: '\t' + str(x) + '\n').tolist()[:5000]
            
            # 2. Add Sentiment Dialogue Corpus
            if hasattr(self, 'conversation_pairs'):
                print(f"Integrating {len(self.conversation_pairs)} pairs from Sentiment Corpus...")
                # Sample 5000 from here too to balance
                import random
                pairs = self.conversation_pairs
                if len(pairs) > 5000:
                    pairs = random.sample(pairs, 5000)
                
                for q, a in pairs:
                    questions.append(str(q))
                    answers.append('\t' + str(a) + '\n')
            
            print(f"Total Comment Training Samples: {len(questions)}")

            # Shared Tokenizer (Character Level for better Korean convergence without Mecab)
            # Filters: Don't filter \t and \n as they are our tokens!
            self.comment_tokenizer = Tokenizer(char_level=True, filters='!"#$%&()*+,-./:;<=>?@[\\]^`{|}~') 
            self.comment_tokenizer.fit_on_texts(questions + answers)
            
            vocab_size = len(self.comment_tokenizer.word_index) + 1
            print(f"Comment Vocab Size (Char-level): {vocab_size}")

            # Encoder Data
            tokenized_Q = self.comment_tokenizer.texts_to_sequences(questions)
            encoder_input_data = pad_sequences(tokenized_Q, maxlen=self.comment_max_len, padding='post')
            
            # Decoder Data
            tokenized_A = self.comment_tokenizer.texts_to_sequences(answers)
            decoder_input_data = pad_sequences(tokenized_A, maxlen=self.comment_max_len, padding='post')
            
            # Decoder Target (Shifted-by-one)
            decoder_target_data = np.zeros_like(decoder_input_data, dtype="float32")
            decoder_target_data[:, :-1] = decoder_input_data[:, 1:]
            decoder_target_data = np.expand_dims(decoder_target_data, -1)

            # Model Architecture
            latent_dim = 256
            
            # Encoder
            encoder_inputs = Input(shape=(None,), name='enc_input')
            enc_emb_layer = Embedding(vocab_size, latent_dim, name='enc_embedding')
            enc_emb = enc_emb_layer(encoder_inputs)
            encoder_lstm = LSTM(latent_dim, return_state=True, name='enc_lstm')
            encoder_outputs, state_h, state_c = encoder_lstm(enc_emb)
            encoder_states = [state_h, state_c]
            
            # Decoder
            decoder_inputs = Input(shape=(None,), name='dec_input')
            dec_emb_layer = Embedding(vocab_size, latent_dim, name='dec_embedding')
            dec_emb = dec_emb_layer(decoder_inputs)
            decoder_lstm = LSTM(latent_dim, return_sequences=True, return_state=True, name='dec_lstm')
            decoder_outputs, _, _ = decoder_lstm(dec_emb, initial_state=encoder_states)
            decoder_dense = Dense(vocab_size, activation='softmax', name='dec_dense')
            decoder_outputs = decoder_dense(decoder_outputs)
            
            self.comment_model = Model([encoder_inputs, decoder_inputs], decoder_outputs)
            self.comment_model.compile(optimizer='rmsprop', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
            
            print("Fitting Seq2Seq Model (Char-level)...")
            self.comment_model.fit([encoder_input_data, decoder_input_data], decoder_target_data,
                                   batch_size=64, epochs=15, validation_split=0.2, verbose=1)
                                   
            print("Comment Model Trained. Saving...")
            
            # Save Main Model
            self.comment_model.save(self.comment_model_path)
            
            # Save Tokenizer
            with open(self.comment_tokenizer_path, 'wb') as handle:
                pickle.dump(self.comment_tokenizer, handle)

            # Construct & Save Inference Models
            self.enc_model = Model(encoder_inputs, encoder_states)
            self.enc_model.save(os.path.join(base_dir, 'comment_enc_model.h5'))
            
            dec_state_input_h = Input(shape=(latent_dim,), name='dec_input_h')
            dec_state_input_c = Input(shape=(latent_dim,), name='dec_input_c')
            dec_states_inputs = [dec_state_input_h, dec_state_input_c]
            
            dec_emb2 = dec_emb_layer(decoder_inputs)
            dec_outputs2, state_h2, state_c2 = decoder_lstm(dec_emb2, initial_state=dec_states_inputs)
            dec_states2 = [state_h2, state_c2]
            dec_outputs2 = decoder_dense(dec_outputs2)
            
            self.dec_model = Model([decoder_inputs] + dec_states_inputs, [dec_outputs2] + dec_states2)
            self.dec_model.save(os.path.join(base_dir, 'comment_dec_model.h5'))
            
            print("Inference models saved.")
            
        except Exception as e:
            print(f"Error training comment model: {e}")

    def _rebuild_inference_models(self):
        """Rebuild inference models from loaded main model or load separate files"""
        try:
            from tensorflow.keras.models import load_model
            base_dir = os.path.dirname(os.path.abspath(__file__))
            enc_path = os.path.join(base_dir, 'comment_enc_model.h5')
            dec_path = os.path.join(base_dir, 'comment_dec_model.h5')
            
            if os.path.exists(enc_path) and os.path.exists(dec_path):
                self.enc_model = load_model(enc_path)
                self.dec_model = load_model(dec_path)
                print("Inference models loaded successfully.")
            else:
                print("Inference model files missing. Comment generation may fail.")
        except Exception as e:
            print(f"Error loading inference models: {e}")

    # Seq2Seq Generation helpers removed



    def analyze_diary_with_local_llm(self, text, history_context=None):
        # [Local AI Mode] Uses Local Ollama (Gemma 2) for Analysis.
        # Free, Unlimited, Private.
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

            # Extract Sleep Info if available in text (which logic passes as simple text usually? No, caller passes string)
            # Actually, caller passes combined string. Let's assume input text has structure or we rely on the text content.
            # But the user asked to tune analysis based on required sleep input.
            # Let's see how 'analyze_diary_logic' calls this. It calls with `full_text`.
            # We should probably update the prompt to explicitly look for sleep mentions if possible, or just emphasize it.
            
            # Better: The prompt format below.
            
            prompt_text = (
                f"너는 심리 상담 전문가야. 다음 내담자의 일기를 읽고 분석해줘.\n"
                f"{context_section}"
                f"### [오늘의 일기 데이터]:\n{text}\n\n"
                f"### [분석 지침]:\n"
                f"1. 내담자의 '수면 상태(잠)'와 '감정'의 연관성을 깊이 있게 분석해줘. (예: 잠을 못 자서 예민한지, 푹 자서 개운한지)\n"
                f"2. 단순한 공감을 넘어, 수면 패턴이 감정에 미친 영향을 언급하며 위로해줘.\n\n"
                f"### [답변 형식]:\n"
                f"Emotion: (happy, sad, angry, neutral, panic 중 하나)\n"
                f"Confidence: (0~100 숫자만)\n"
                f"Comment: (수면 상태를 언급하며 50자 이내의 따뜻한 한국어 위로)\n"
                f"반드시 위 형식만 지켜서 답변해."
            )
            
            payload = {
                "model": "maum-on-gemma",
                "prompt": prompt_text,
                "stream": False,
                # "format": "json"  <-- REMOVED: Cause of hanging
                "options": {
                    "temperature": 0.3, # Low temp for stability
                    "num_predict": 150
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
            
            # Regex Parsing
            import re
            
            # 1. Emotion
            emotion_match = re.search(r"Emotion:\s*([a-zA-Z]+)", response_text, re.IGNORECASE)
            emotion_str = emotion_match.group(1).lower() if emotion_match else "neutral"
            
            # 2. Confidence
            conf_match = re.search(r"Confidence:\s*(\d+)", response_text)
            confidence = int(conf_match.group(1)) if conf_match else 80
            
            # 3. Comment
            comment_match = re.search(r"Comment:\s*(.*)", response_text, re.DOTALL)
            comment = comment_match.group(1).strip() if comment_match else "오늘 하루도 수고 많으셨어요."
            
            # Remove any trailing quotes if model added them
            if comment.startswith('"') and comment.endswith('"'):
                comment = comment[1:-1]

            # Map to Korean
            emotion_map = {
                "happy": "행복해", "joy": "행복해", 
                "sad": "우울해", "depressed": "우울해", 
                "neutral": "평온해", "calm": "평온해", "soso": "그저그래",
                "angry": "화가나", "annoyed": "화가나", 
                "panic": "우울해", "anxious": "우울해"
            }
            
            korean_emotion = emotion_map.get(emotion_str, "평온해")
            formatted_prediction = f"'{korean_emotion} ({confidence}%)'"
            
            return formatted_prediction, comment
                
        except Exception as e:
            print(f"❌ Local AI Error: {e}")
            return None, None

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


    def generate_comprehensive_report(self, diary_summary):
        """
        Generates a detailed 10-paragraph psychological report using Local Gemma 2.
        """
        import requests
        print("🧠 [Brain] Generating Comprehensive Report...")
        
        try:
            url = "http://localhost:11434/api/generate"
            
            prompt_text = (
                "## SYSTEM: You represent a thoughtful, empathetic counselor with 20 years of experience. You must ANSWER IN KOREAN ONLY.\n"
                "당신은 20년 경력의 베테랑 심리 상담사입니다. 아래 내담자(사용자)의 일기 기록과 통계를 자세히 읽고 분석해주세요.\n\n"
                f"### [사용자 데이터]\n{diary_summary}\n\n"
                "### [작성 지침]\n"
                "1. **언어**: 반드시 **한국어(Korean)**로만 작성하세요. 영어는 절대 사용하지 마세요.\n"
                "2. **형식**: 사용자에게 보내는 '심층 심리 분석 리포트' 형식으로 작성하세요.\n"
                "3. **분량**: 반드시 **서론-본론(진단)-결론(처방)**의 흐름을 갖춘 **총 10문단 이상의 긴 글**이어야 합니다.\n"
                "4. **어조**: 전문적인 심리학 용어를 사용하되, 따뜻하고 이해하기 쉬운 언어로 풀어주세요.\n\n"
                "### [리포트 구조]\n"
                "1부. **마음의 지도 (현상 진단)** (5문단)\n"
                "   - 내담자가 주로 사용하는 감정 언어와 내면의 상태 분석\n"
                "   - 반복되는 스트레스 패턴이나 감정의 트리거 파악\n"
                "   - 숨겨진 긍정적인 자원이나 강점 발굴\n\n"
                "2부. **나아가야 할 길 (미래 처방)** (5문단)\n"
                "   - 현재 상태에서 실천할 수 있는 구체적인 심리 기법 3가지 (ACT, CBT 등 활용)\n"
                "   - 감정의 파도를 다스리는 생활 습관 제안\n"
                "   - 상담사로서 전하는 진심 어린 격려와 희망의 메시지\n\n"
                "**중요: 모든 답변은 완벽한 한국어로 작성되어야 합니다. 번역투가 아닌 자연스러운 한국어를 사용하세요.**\n"
                "지금 바로 한국어로 리포트 작성을 시작하세요."
            )
            
            payload = {
                "model": "gemma2:2b",
                "prompt": prompt_text,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 4096, # Maximum length
                    "repeat_penalty": 1.1,
                    "top_k": 40,
                    "top_p": 0.9
                }
            }
            
            # Timeout 600s (10 mins) - Increased for OCI environment
            response = requests.post(url, json=payload, timeout=600)
            
            if response.status_code == 200:
                result = response.json().get('response', '')
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
                "당신은 내담자의 '과거 심리 분석 리포트들'을 종합하여 장기적인 변화와 흐름을 분석하는 '메타 분석가'입니다.\n"
                "아래 제공된 과거 리포트 기록들을 읽고, 내담자의 심리 상태가 시간의 흐름에 따라 어떻게 변화했는지 분석해주세요.\n\n"
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

# Standalone Function: Bypasses EmotionAnalysis class init for stability
def generate_analysis_reaction_standalone(user_text, mode='reaction'):
    print(f"DEBUG: generate_analysis_reaction_standalone called. Mode={mode}, Text={user_text[:20]}...")
    if not user_text: return None
    import re
    import requests
    import random
    
    # 1. Sanitize
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '[EMAIL]', user_text)
    sanitized = text[:300]
    
    # 2. Prompt Switching
    if mode == 'question':
        # Follow-up Question Prompt
        prompt_text = (
            f"내담자의 말: \"{sanitized}\"\n\n"
            "내담자가 너무 짧고 단답형으로 대답했어. 대화를 더 깊게 이끌어내기 위해 **자연스러운 꼬리 질문**을 하나 던져줘.\n"
            "지시사항:\n"
            "1. 내담자의 말을 반복하기보다, 그 이면의 이유나 구체적인 내용을 물어봐.\n"
            "2. '그렇군요' 같은 짧은 공감 후 바로 질문해.\n"
            "3. 말투는 다정하고 궁금해하는 '해요체'를 써.\n"
            "4. 100자 이내로.\n\n"
            "꼬리 질문:"
        )
    else:
        # Standard Reaction Prompt
        prompt_text = (
            f"내담자의 말: \"{sanitized}\"\n\n"
            "너는 깊은 통찰력을 지닌 따뜻한 심리 상담사야. 내담자의 말을 듣고 **상황을 분석**하고 **지지하는 코멘트**를 해줘.\n"
            "지시사항:\n"
            "1. 먼저 내담자의 말 속에 숨겨진 감정이나 욕구를 분석해서 언급해줘. (예: '기대감과 동시에 걱정도 있으신 것 같군요.')\n"
            "2. 그 다음, 그 감정이 타당함을 지지해주고 따뜻하게 격려해줘.\n"
            "3. 말투는 전문적이고 부드러운 '해요체'를 써.\n"
            "4. 질문은 하지 마.\n"
            "5. 150자 이내로.\n\n"
            "분석 및 리액션:"
        )
    
    try:
        payload = {
            "model": "maum-on-gemma",
            "prompt": prompt_text,
            "stream": False,
            "options": {
                "temperature": 0.7, 
                "num_predict": 180
            }
        }
        res = requests.post("http://localhost:11434/api/generate", json=payload, timeout=60)
        
        if res.status_code == 200:
            result = res.json().get('response', '').strip()
            if result.startswith('"') and result.endswith('"'):
                result = result[1:-1]
            if result: return result
            
    except Exception as e:
        print(f"❌ Standalone AI Error: {e}")
        
    # 3. Fallback (Mode Specific)
    if mode == 'question':
        fallbacks = [
            "그렇군요. 혹시 조금 더 자세히 이야기해주실 수 있나요? 궁금해요.",
            "저런, 특별한 이유가 있었는지 듣고 싶어요.",
            "짧게 말씀하시니 더 깊은 속마음이 궁금해지네요. 편하게 털어놓아주세요.",
            "그 일이 내담자님께 어떤 의미였는지 조금만 더 들려주세요."
        ]
    else:
        fallbacks = [
            "말씀하신 내용에서 깊은 고민과 진심이 느껴지네요. 잘하고 계십니다.",
            "상황을 차분히 들여다보면, 그 안에서 스스로의 성장을 발견하실 수 있을 거예요.",
            "지금 느끼시는 감정은 매우 자연스러운 반응이에요. 스스로를 믿어보세요.",
            "이야기를 들어보니, 그동안 마음속에 담아두셨던 생각들이 많으셨던 것 같아 마음이 쓰이네요."
        ]
        
    return random.choice(fallbacks)

