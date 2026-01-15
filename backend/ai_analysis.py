import numpy as np
import os
import random
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config
import json
TRAINING_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'training_state.json')
try:
    from models import EmotionKeyword
    from emotion_codes import EMOTION_CODE_MAP
except ImportError:
    # Handle possible circular import dynamically if needed, or rely on caller context
    pass

# Try to import TensorFlow/Keras, but provide fallback if not installed
try:
    from tensorflow.keras.preprocessing.text import Tokenizer
    from tensorflow.keras.preprocessing.sequence import pad_sequences
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import Embedding, LSTM, Dense, Dropout, Input
    from tensorflow.keras.utils import to_categorical
    from tensorflow.keras.utils import to_categorical
    import pandas as pd
    TENSORFLOW_AVAILABLE = True
    
    # KoGPT-2 Imports
    from transformers import GPT2LMHeadModel, PreTrainedTokenizerFast
    import torch
except ImportError as e:
    TENSORFLOW_AVAILABLE = False
    print(f"Warning: AI Library not found. Error: {e}")
    print("Using simple keyword-based sentiment analysis.")

class EmotionAnalysis:
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.max_len = 50
        self.vocab_size = 0
        
        # 60 Ultra-Fine-Grained Emotion Classes
        # Sort codes to ensure consistent indexing (E10, E11, ... E69)
        self.sorted_codes = sorted(EMOTION_CODE_MAP.keys())
        self.classes = [EMOTION_CODE_MAP[code] for code in self.sorted_codes]
        self.code_to_idx = {code: i for i, code in enumerate(self.sorted_codes)}
        
        # We will load keywords from DB for fallback/learning
        self.db_engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        self.Session = sessionmaker(bind=self.db_engine)

        # Initial Training Data
        # Replaced hardcoded 5-class data with empty lists. 
        # We rely 100% on the 60-class Sentiment Dialogue Corpus.
        self.train_texts = []
        self.train_labels = np.array([], dtype=int)

        # Fallback Comment Bank
        self.comment_bank = {
            "행복해": [
                "오늘 하루 정말 행복하셨군요! 이 긍정적인 에너지가 내일도 이어지길 바랄게요. 😊",
                "듣기만 해도 기분이 좋아지는 이야기네요! 행복한 순간을 오래 간직하세요.",
                "웃음이 가득한 하루였네요. 내일도 이렇게 웃을 일이 많았으면 좋겠어요!",
                "정말 멋진 하루였군요! 스스로에게 칭찬 한마디 해주세요. 👍",
                "행복은 전염된다고 하죠. 당신의 행복이 주변까지 밝게 비출 거예요.",
                "기분 좋은 에너지가 가득하네요! 맛있는 거 드시면서 오늘을 기념해보세요.",
                "최고의 하루를 보내셨네요! 잠들기 전 행복했던 순간을 다시 떠올려보세요.",
                "오늘의 즐거움이 마음속에 오래오래 남기를 바라요. 💖",
                "세상이 당신을 축복하는 날이었나 봐요! 정말 기쁜 소식이에요.",
                "행복한 당신의 모습을 보니 저도 기분이 좋아집니다! 파이팅!"
            ],
            "평온해": [
                "마음이 편안하다니 다행이에요. 따뜻한 차 한 잔으로 하루를 마무리해보는 건 어떨까요? 🍵",
                "잔잔한 호수 같은 마음이네요. 이 평화로움이 계속되길 바라요.",
                "여유로운 하루를 보내셨군요. 복잡한 생각은 잠시 내려놓고 쉬어가세요.",
                "평범하지만 소중한 평온함이네요. 좋아하는 음악을 들으며 힐링해봐요. 🎵",
                "마음의 쉼표가 필요한 순간, 딱 적절한 휴식을 취하신 것 같아요.",
                "평화로운 마음으로 잠자리에 들 수 있겠네요. 좋은 꿈 꾸세요. 🌙",
                "조용한 행복이 깃든 하루였네요. 이런 날들이 쌓여 삶을 단단하게 만들어요.",
                "자연스러운 흐름에 몸을 맡긴 당신, 참 편안해 보여요.",
                "긴장이 풀리고 마음이 놓이는 기분, 정말 소중하죠.",
                "오늘의 평온함이 내일을 살아갈 힘이 되어줄 거예요."
            ],
            "그저그래": [
                "평범한 하루였군요. 내일은 좀 더 특별한 일이 생길지도 몰라요! 파이팅 💪",
                "별일 없는 하루도 소중하죠. 무탈하게 보낸 것에 감사해봐요.",
                "때로는 잔잔한 하루가 가장 큰 휴식이 되기도 한답니다.",
                "심심한 날이었다면, 내일은 작은 모험을 계획해보는 건 어떨까요?",
                "그저 그런 날도 지나고 보면 추억이 될 거예요. 편안한 밤 보내세요.",
                "특별한 일은 없었지만, 당신은 오늘도 당신의 자리를 잘 지켰어요.",
                "무난한 하루였네요. 내일은 좋아하는 간식을 먹으며 기분을 전환해볼까요?",
                "오늘은 잠시 쉬어가는 페이지라고 생각해요. 내일은 또 다른 이야기가 쓰일 거예요.",
                "감정의 기복 없이 평탄한 하루, 그것만으로도 충분히 괜찮아요.",
                "내일은 예상치 못한 즐거움이 기다리고 있을지도 몰라요!"
            ],
            "우울해": [
                "많이 힘드셨군요. 오늘 하루는 푹 쉬면서 자신을 토닥여주세요. 당신은 소중한 사람입니다. 💙",
                "마음이 무거운 날이네요. 울고 싶다면 실컷 울어도 괜찮아요. 제가 곁에 있을게요.",
                "괜찮지 않아도 괜찮아요. 오늘은 무리하지 말고 자기 자신만 생각하세요.",
                "당신의 슬픔이 깊은 만큼, 당신은 따뜻한 마음을 가진 사람일 거예요.",
                "어두운 밤이 지나면 반드시 해가 뜹니다. 잠시 웅크려 있어도 괜찮아요.",
                "힘든 하루를 버텨낸 당신, 정말 고생 많았어요. 따뜻한 이불 속에서 푹 주무세요.",
                "마음의 비가 그치기를 기다릴게요. 혼자라고 생각하지 마세요.",
                "지금 느끼는 감정도 당신의 일부예요. 부정하지 말고 가만히 안아주세요.",
                "맛있는 거라도 먹고 기운 차리셨으면 좋겠어요. 내일은 조금 더 나아질 거예요.",
                "당신은 혼자가 아니에요. 힘든 순간이 지나가길 함께 응원할게요."
            ],
            "화가나": [
                "속상한 일이 있으셨나 봐요. 잠시 심호흡을 하며 마음을 가라앉혀보면 어떨까요? 힘내세요! 🔥",
                "정말 화가 날 만한 상황이었군요. 그 감정을 억누르지 말고 건전하게 풀어보세요.",
                "열받는 하루였네요! 시원한 물 한 잔 마시고 털어버리세요.",
                "누구라도 화가 났을 거예요. 당신 잘못이 아니니 너무 자책하지 마세요.",
                "분노는 에너지가 될 수도 있어요. 운동이나 취미로 스트레스를 날려버려요! 🥊",
                "많이 억울하셨죠. 당신의 마음 다 이해해요.",
                "화가 날 때는 잠시 그 상황에서 벗어나 환기를 시키는 게 도움이 돼요.",
                "오늘의 나쁜 기분은 오늘로 끝내버려요. 내일은 기분 좋은 일만 있을 거예요.",
                "소리라도 한 번 크게 지르고 싶네요! 답답한 마음이 조금은 풀리길 바라요.",
                "당신의 평화를 방해한 것들이 밉네요. 오늘은 일찍 쉬면서 마음을 다스려봐요.",
                # New Additions
                "정말 화가 나시겠어요. 억울한 마음 이해해요.",
                "그런 일이 있었다니 저도 화가 나네요.",
                "속상한 마음을 어떻게 달래면 좋을까요? 잠시 쉬어가는 건 어떨까요.",
                "참지 말고 화를 표출하는 것도 방법이에요. 건강하게 해소해봐요.",
                "스트레스를 받을 만한 상황이군요. 너무 무리하지 마세요.",
                "마음을 가라앉히고 천천히 생각해보세요. 당신은 할 수 있어요.",
                "부당한 일을 당하셔서 많이 속상하시겠어요. 힘내세요.",
                "그 사람 때문에 당신의 소중한 기분을 망치지 마세요.",
                "화나는 감정은 당연한 반응이에요. 스스로를 다독여주세요.",
                "지금은 마음을 진정시키는 게 우선인 것 같아요. 따뜻한 차 한 잔 어때요?"
            ]
        }
        
        # Extend other categories with new comments
        self.comment_bank["행복해"].extend([
            "정말 행복하실 것 같아요. 저도 덩달아 기분이 좋아지네요!",
            "긍정적인 마음가짐이 참 좋아 보여요. 멋지십니다.",
            "노력의 결과가 좋아서 다행이에요. 축하드려요!",
            "즐거운 시간을 보내셨군요. 그 기분 오래 간직하세요.",
            "기분 좋은 일이 있으셨나 봐요. 행복한 에너지 감사합니다.",
            "축하해요! 앞으로도 좋은 일만 가득하길 바라요.",
            "성취감을 느끼셨다니 멋져요. 당신이 자랑스러워요.",
            "행복한 하루를 보내신 것 같아 저도 기쁘네요.",
            "원하시던 일이 이루어져서 다행이에요. 고생 많으셨어요.",
            "웃음이 끊이지 않는 하루가 되길 응원할게요!"
        ])
        
        self.comment_bank["평온해"].extend([
            "마음이 편안하시다니 다행이에요. 그 평온함이 지속되길.",
            "걱정 없이 푹 쉬시는 것도 중요하죠. 힐링하는 시간 되세요.",
            "산책을 하며 여유를 즐기셨군요. 자연 속에서 치유받으셨길.",
            "편안한 시간을 보내고 계시네요. 부러워요!",
            "안정된 마음이 계속되길 바라요. 오늘 하루도 수고했어요.",
            "차 한 잔하며 쉬는 시간은 정말 소중하죠. 따뜻한 시간 되세요.",
            "아무런 근심 없이 평화로운 상태시군요. 참 보기 좋아요.",
            "고요한 시간을 즐기는 것도 힐링이 되죠. 오롯이 나에게 집중해봐요.",
            "오늘 하루가 평온하게 마무리되길 바라요. 굿나잇!",
            "마음의 여유를 찾는 모습이 보기 좋아요. 항상 응원할게요."
        ])
        
        self.comment_bank["우울해"].extend([
            "마음이 많이 힘드신 것 같네요. 제가 들어드릴게요.",
            "무슨 일인지 좀 더 자세히 듣고 싶어요. 언제든 말씀해주세요.",
            "많이 괴로우시겠어요. 혼자 끙끙 앓지 마시고 털어놓아 보세요.",
            "혼자라고 생각하지 마시고 기운 내세요. 당신은 소중해요.",
            "상처받은 마음을 잘 추스르시길 바라요. 시간은 당신 편이에요.",
            "지금은 힘들지만 분명 나아질 거예요. 믿어 의심치 않아요.",
            "우울한 마음이 들 때는 잠시 쉬어가도 좋아요. 괜찮아요.",
            "당신의 잘못이 아니에요. 너무 자책하지 마세요.",
            "눈물을 흘리는 것도 감정 해소에 도움이 돼요. 펑펑 우셔도 돼요.",
            "제가 항상 곁에서 들어드릴게요. 힘든 하루 고생 많았어요."
        ])
        
        # Initialize attributes
        self.comment_tokenizer = None
        self.comment_model = None
        self.enc_model = None 
        self.dec_model = None
        self.comment_max_len = 20
        self.gpt_model = None
        self.gpt_tokenizer = None

    
        if TENSORFLOW_AVAILABLE:
            print("Initializing AI Emotion Analysis Model (5-Class LSTM)...")
            self.tokenizer = Tokenizer()
            
            if os.environ.get('SKIP_TRAINING'):
                print("Skipping training logic (SKIP_TRAINING active).")
                # Still need to load auxiliary data
                self.comment_bank = {}
                self.load_comment_bank()
                self.load_emotion_bank()
                # Try loading KoGPT-2 even if skipping training
                try:
                    print("Loading KoGPT-2 Model...")
                    self.gpt_tokenizer = PreTrainedTokenizerFast.from_pretrained("skt/kogpt2-base-v2", 
                        bos_token='</s>', eos_token='</s>', unk_token='<unk>', 
                        pad_token='<pad>', mask_token='<mask>')
                    self.gpt_model = GPT2LMHeadModel.from_pretrained('skt/kogpt2-base-v2')
                    self.gpt_model.eval()
                    print("KoGPT-2 Loaded successfully.")
                except Exception as e:
                    print(f"KoGPT-2 Load Failed: {e}")
                return

            # Check for saved model
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.model_path = os.path.join(base_dir, 'emotion_model.h5')
            self.tokenizer_path = os.path.join(base_dir, 'tokenizer.pickle')
            
            # Comment Model Paths
            self.comment_model_path = os.path.join(base_dir, 'comment_model.h5')
            self.comment_enc_model_path = os.path.join(base_dir, 'comment_enc_model.h5')
            self.comment_tokenizer_path = os.path.join(base_dir, 'comment_tokenizer.pickle')

            # Check Training Condition
            current_count = self._get_keyword_count()
            last_count = self._get_last_trained_count()
            diff = current_count - last_count
            
            print(f"📊 Training Check: Current Keywords={current_count}, Last Trained={last_count}, Diff={diff}")
            
            should_train = (diff >= 100)
            
            # Force train if models are missing?
            # User said "Otherwise just run server". But if models missing, we can't run AI.
            # However, fallback logic exists.
            # We will follow user strictly: Only train if diff >= 100.
            # But we must try to load if we don't train.
            
            model_exists = os.path.exists(self.model_path) and os.path.exists(self.tokenizer_path)

            if should_train:
                print(f"🚀 New data detected (+{diff} >= 100). Starting Full Training (LSTM + Seq2Seq)...")
                try:
                    self._load_and_train()
                    self._save_training_state(current_count)
                    print("✅ Training complete and state saved.")
                except Exception as e:
                    print(f"❌ Training failed: {e}")
                    # Try loading existing if training failed
                    if model_exists:
                        self._load_existing_models()
            
            elif model_exists:
                print("📦 Models found. Loading existing models...")
                self._load_existing_models()
                
            else:
                print("⚠️ No models found and new data < 100. Skipping training.")
                print("   The server will run in Basic Mode (Keyword Fallback).")
            
            print("AI Model initialized.")
            
            # Load Comment Bank (Safety Net)
            self.comment_bank = {}
            self.load_comment_bank()
            self.load_emotion_bank()
            
            # Load Polyglot-Ko (Phase 2)
            try:
                print("Loading Polyglot-Ko-1.3B Model...")
                from transformers import AutoTokenizer, AutoModelForCausalLM
                
                # Use Polyglot-Ko-1.3B
                model_name = "EleutherAI/polyglot-ko-1.3b"
                
                self.gpt_tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.gpt_model = AutoModelForCausalLM.from_pretrained(model_name)
                
                self.gpt_model.eval() # Set to evaluation mode
                print("Polyglot-Ko-1.3B Loaded successfully.")
            except Exception as e:
                print(f"Polyglot Load Failed: {e}")
                self.gpt_model = None

        else:
            print("Initializing Fallback Emotion Analysis (Keyword based - 5 classes)...")

    def _get_keyword_count(self):
        """Get total count of emotion keywords from DB"""
        session = self.Session()
        try:
            # Need to import inside as it might fail if table doesn't exist?
            # Actually models is imported at top level, but table creation happens later.
            # If table doesn't exist, this query will fail.
            from models import EmotionKeyword
            # Check if table exists (raw SQL for safety if ORM fails?)
            # But let's try ORM first.
            count = session.query(EmotionKeyword).count()
            return count
        except Exception as e:
            # Table likely doesn't exist yet
            return 0
        finally:
            session.close()

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
            
            # COMMENT MODEL LOADING
            if os.path.exists(self.comment_model_path) and os.path.exists(self.comment_tokenizer_path):
                print("Loading comment generation model...")
                self.comment_model = load_model(self.comment_model_path)
                with open(self.comment_tokenizer_path, 'rb') as ct:
                    self.comment_tokenizer = pickle.load(ct)
                print("Comment Model loaded.")
                self._rebuild_inference_models()
            else:
                print("Comment model not found (skipping auto-train as per policy).")
                
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
        # emotion_label format: "분노 (배신감) (85.0%)" or just "분노 (배신감)"
        if not self.emotion_bank:
            return None
            
        # Clean label to match key
        # Key in bank: "분노 (노여움/억울)"
        # Predicted Label: "분노 (노여움/억울)"
        
        # Remove confidence if present (e.g. " (85.0%)")
        # And ensure we match the key format "Name (Sub)"
        try:
            if '(' in emotion_label:
                # Take everything up to the second closing paren? Or just strip the last one (confidence)?
                # Our keys are "Name (Sub)".
                # Predicted might be "Name (Sub) (85%)" or "Name (Sub)"
                
                # Split by ' (' which usually separates label from confidence
                label_key = emotion_label.rsplit(' (', 1)[0]
                # If rsplit didn't find ' (', it returns the string itself if maxsplit used, 
                # but rsplit(' (', 1) might return just the string if not found? 
                # Actually, simple split is risky.
                
                # Safer: Just look for a key in our bank that matches the start of the string
                pass
            else:
                label_key = emotion_label
        except:
             label_key = emotion_label
        
        # Exact match attempt
        if label_key in self.emotion_bank:
            return self.emotion_bank[label_key].get('default')
            
        # Fuzzy match (e.g. just "분노" part?) - No, be precise.
        # Check stripping parens check? 
        for key in self.emotion_bank:
            if key in emotion_label:
                return self.emotion_bank[key].get('default')
        
        return None
        
    def generate_kogpt2_comment(self, user_input, emotion_label):
        """Phase 2: KoGPT-2 Generation (Priority 2)"""
        if not self.gpt_model or not self.gpt_tokenizer:
            return None
            
        try:
            # Handle user_input (str or dict)
            if isinstance(user_input, dict):
                event = user_input.get('event', '')
                emotion = user_input.get('emotion', '')
                self_talk = user_input.get('self_talk', '')
                
                # Few-Shot Prompting to guide the model
                # Few-Shot Prompting with Persona for Polyglot
                prompt = (
                    "역활: 당신은 다정하고 공감 능력이 뛰어난 심리 상담사입니다. 내담자의 일기를 읽고 따뜻한 위로와 공감의 말을 건네주세요. 답변은 2~3문장으로 간결하게 해주세요.\n\n"
                    "상황: 시험에 떨어져서 울었다.\n"
                    "감정: 슬픔 (좌절)\n"
                    "상담사: 정말 속상하시겠어요. 열심히 준비했을 텐데 결과가 좋지 않아 마음이 아프시죠. 하지만 이번 실패가 당신의 모든 것을 결정하지는 않아요. 오늘은 푹 쉬면서 스스로를 위로해주세요.\n\n"
                    f"상황: {event} {emotion} {self_talk}\n"
                    f"감정: {emotion_label}\n"
                    "상담사:"
                )
            else:
                text = str(user_input)
                prompt = (
                    "역활: 당신은 다정하고 공감 능력이 뛰어난 심리 상담사입니다. 내담자의 일기를 읽고 따뜻한 위로와 공감의 말을 건네주세요. 답변은 2~3문장으로 간결하게 해주세요.\n\n"
                    "일기: 오늘 하루종일 너무 힘들었다.\n"
                    "감정: 우울 (지침)\n"
                    "상담사: 오늘 하루 정말 고생 많으셨어요. 지친 몸과 마음을 편안하게 내려놓고 휴식을 취해보세요. 당신은 충분히 잘하고 있습니다.\n\n"
                    f"일기: {text}\n"
                    f"감정: {emotion_label}\n"
                    "상담사:"
                )
            
            input_ids = self.gpt_tokenizer.encode(prompt, return_tensors='pt')
            

            with torch.no_grad():
                gen_ids = self.gpt_model.generate(
                    input_ids,
                    max_length=len(input_ids[0]) + 50, # Shorter limit to reduce drift
                    do_sample=True,
                    temperature=0.6, # Focused
                    top_p=0.90,
                    repetition_penalty=1.2,
                    pad_token_id=self.gpt_tokenizer.pad_token_id,
                    eos_token_id=self.gpt_tokenizer.eos_token_id,
                    bos_token_id=self.gpt_tokenizer.bos_token_id,
                    use_cache=True
                )
                
            generated = self.gpt_tokenizer.decode(gen_ids[0])
            
            # Extract response
            if "상담사 답변:" in generated:
                response = generated.split("상담사 답변:")[-1].strip()
            elif "상담사:" in generated:
                 response = generated.split("상담사:")[-1].strip()
            else:
                response = generated
                
            # Post-process: Take first 2 sentences only to avoid hallucination
            sentences = response.split('.')
            clean_response = '. '.join(sentences[:2]).strip() + "."
            
            return clean_response
            
        except Exception as e:
            print(f"KoGPT Generation Error: {e}")
            return None


    def _rebuild_inference_models(self):
        # Reconstruct Encoder/Decoder from self.comment_model layers
        # This assumes a specific structure: [Input, Input] -> [Embedding, Embedding] -> [LSTM, LSTM] -> Dense
        try:
            from tensorflow.keras.models import Model
            from tensorflow.keras.layers import Input
            
            latent_dim = 256
            
            # Get layers by name or index. 
            # Structure from train_comment_model:
            # Inputs: input_1 (enc), input_2 (dec)
            # Embedding: embedding_1 (shared?) or separate. In code below, distinct.
            
            # Let's rely on layer names if possible, but default names change.
            # Best approach: Retain reference to layers if just trained, but here we loaded from disk.
            # We need to traverse the graph.
            
            # For robustness in this prototype, if rebuild fails, we just don't gen comments.
            # OR, we simply save the inference models separately. That's safer.
            pass # Placeholder, will implement save/load of separate inference models or rebuild logic
        except Exception as e:
            print(f"Rebuild error: {e}")

    def _load_and_train(self):
        # --- Load GoEmotions Data & Map Labels ---
        # DISABLE for 60-class upgrade: GoEmotions labels (0-27) do not map 1:1 to our 60 classes yet.
        # We rely solely on the Sentiment Dialogue Corpus for now.
        # (Removed old hardcoded mapping to 5 classes to prevent poisoning)


        # 2. Initialize Conversation Pairs (for Seq2Seq)
        self.conversation_pairs = []

        # 3. Load Sentiment Dialogue Corpus (Training & Validation)
        # Adds to self.train_texts & self.train_labels AND self.conversation_pairs
        self.load_sentiment_corpus()
        
        # 4. Load Data from Database (Fine-tuning)
        # DISABLE for 60-class upgrade: User Emoji (5-class) is incompatible with 60-class labels.
        # Future work: Map 5-class to "soft labels" or specific sub-classes.
        # db_texts, db_labels = self.load_db_data()
        # if db_texts:
        #     print(f"Integrating {len(db_texts)} samples from Database for Emotion Analysis...")
        #     self.train_texts.extend(db_texts)
        #     self.train_labels = np.concatenate((self.train_labels, np.array(db_labels)))
            
        print(f"Final Training Data Size: {len(self.train_texts)}")

        # 5. Train Initial Model
        self._train_initial_model()
        
        # 6. Train Comment Model (Seq2Seq)
        # Assuming DB data isn't needed for Comment Gen yet (Prompt didn't specify, just Analysis)
        # But wait, User said "AI분석을 진행해서... 적용해줘". 
        # Typically implies Emotion Analysis. Comment Gen needs (Q, A) pairs. 
        # DB data is Diarh (Monologue), not Dialogue. So it's best suited for Emotion Analysis.
        self.train_comment_model() # Train comment model after main model

    def _train_initial_model(self):
        # Increased Vocab size for larger dataset
        self.tokenizer.fit_on_texts(self.train_texts)
        self.vocab_size = len(self.tokenizer.word_index) + 1
        print(f"Emotion Vocab Size: {self.vocab_size}")
        
        sequences = self.tokenizer.texts_to_sequences(self.train_texts)
        X_train = pad_sequences(sequences, maxlen=self.max_len)
        y_train = self.train_labels
        
        self.model = Sequential()
        self.model.add(Embedding(self.vocab_size, 256, input_length=self.max_len)) 
        self.model.add(LSTM(256, dropout=0.3, recurrent_dropout=0.3)) 
        self.model.add(Dense(128, activation='relu')) 
        self.model.add(Dropout(0.4))
        self.model.add(Dense(len(self.classes), activation='softmax')) 
        
        self.model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        
        print("Training Emotion Classifier...")
        self.model.fit(X_train, y_train, epochs=5, batch_size=32, validation_split=0.1, verbose=1) 
        
        # Save Model & Tokenizer
        try:
            import pickle
            self.model.save(self.model_path)
            with open(self.tokenizer_path, 'wb') as handle:
                pickle.dump(self.tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"Model saved to {self.model_path}")
        except Exception as e:
            print(f"Error saving model: {e}") 

    def _train_with_data(self, texts, labels):
        """
        Train the model with custom provided data (for retraining script).
        
        Args:
            texts (list): List of text strings
            labels (list): List of label indices (0-59 for 60-class)
        """
        if not TENSORFLOW_AVAILABLE:
            print("TensorFlow not available. Cannot train.")
            return
        
        print(f"Training with {len(texts)} samples...")
        
        # Use existing tokenizer if loaded, or create new one
        if not self.tokenizer:
            self.tokenizer = Tokenizer()
        
        # Fit tokenizer on new data
        self.tokenizer.fit_on_texts(texts)
        self.vocab_size = len(self.tokenizer.word_index) + 1
        print(f"Vocabulary Size: {self.vocab_size}")
        
        # Prepare sequences
        sequences = self.tokenizer.texts_to_sequences(texts)
        X_train = pad_sequences(sequences, maxlen=self.max_len)
        y_train = np.array(labels)
        
        # Build model architecture
        self.model = Sequential()
        self.model.add(Embedding(self.vocab_size, 256, input_length=self.max_len))
        self.model.add(LSTM(256, dropout=0.3, recurrent_dropout=0.3))
        self.model.add(Dense(128, activation='relu'))
        self.model.add(Dropout(0.4))
        self.model.add(Dense(len(self.classes), activation='softmax'))
        
        self.model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        # Train
        print("Starting training...")
        history = self.model.fit(
            X_train, y_train,
            epochs=5,
            batch_size=32,
            validation_split=0.1,
            verbose=1
        )
        
        # Save
        try:
            import pickle
            self.model.save(self.model_path)
            with open(self.tokenizer_path, 'wb') as handle:
                pickle.dump(self.tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"✅ Model saved to {self.model_path}")
            print(f"✅ Tokenizer saved to {self.tokenizer_path}")
        except Exception as e:
            print(f"❌ Error saving model: {e}")
        
        return history



    def predict(self, text):
        if not text: return "분석 불가"

        if TENSORFLOW_AVAILABLE and self.model:
            try:
                sequences = self.tokenizer.texts_to_sequences([text])
                padded = pad_sequences(sequences, maxlen=self.max_len)
                prediction = self.model.predict(padded, verbose=0)[0]
                predicted_class_idx = np.argmax(prediction)
                confidence = prediction[predicted_class_idx]
                predicted_label = self.classes[predicted_class_idx]
                return f"{predicted_label} ({(confidence * 100):.1f}%)"
            except Exception as e:
                print(f"Prediction error: {e}")
                return self._fallback_predict(text)
        else:
            return self._fallback_predict(text)

    def _fallback_predict(self, text):
        # Load keywords from DB dynamically
        session = self.Session()
        try:
            from models import EmotionKeyword # Import here to avoid circular dep
            
            keywords = session.query(EmotionKeyword).all()
            
            scores = [0] * 5
            found_any = False
            
            for kw in keywords:
                if kw.keyword in text:
                    scores[kw.emotion_label] += kw.frequency
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
        finally:
            session.close()

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

    def generate_ai_comment(self, text):
        if not self.enc_model or not self.comment_tokenizer:
            return None
            
        try:
            # Preprocess
            seq = self.comment_tokenizer.texts_to_sequences([text])
            if not seq or not seq[0]: return None # Unknown words
            
            input_seq = pad_sequences(seq, maxlen=self.comment_max_len, padding='post')
            
            # Encode
            states_value = self.enc_model.predict(input_seq, verbose=0)
            
            # Generate
            target_seq = np.zeros((1,1))
            # Use \t Key
            target_seq[0, 0] = self.comment_tokenizer.word_index['\t']
            
            decoded_sentence = ''
            stop_condition = False
            
            while not stop_condition:
                output_tokens, h, c = self.dec_model.predict([target_seq] + states_value, verbose=0)
                
                # Sample with Temperature
                sampled_token_index = self.sample(output_tokens[0, -1, :], temperature=0.6)
                sampled_word = self.comment_tokenizer.index_word.get(sampled_token_index, '')
                
                if sampled_word == '\n' or len(decoded_sentence) > 50:
                    stop_condition = True
                else:
                    decoded_sentence += sampled_word
                
                # Update target seq
                target_seq = np.zeros((1, 1))
                target_seq[0, 0] = sampled_token_index
                
                # Update states
                states_value = [h, c]
                
        except Exception as e:
            print(f"Gen Error: {e}")
            return None
            
        return decoded_sentence.strip()

    def sample(self, preds, temperature=1.0):
        # Helper function to sample an index from a probability array
        preds = np.asarray(preds).astype('float64')
        preds = np.log(preds + 1e-10) / temperature
        exp_preds = np.exp(preds)
        preds = exp_preds / np.sum(exp_preds)
        probas = np.random.multinomial(1, preds, 1)
        return np.argmax(probas)


    def generate_comment(self, prediction_text, user_text=None):
        """
        Generate a supportive comment.
        Priority: 1. Keyword Bank (Safety Net) 2. AI Generation (Seq2Seq) 3. Fallback
        """
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

        # 2. Phase 2: KoGPT-2 Generation (High Priority for Context)
        if user_text:
            # Pass the full specific label to KoGPT for context-aware generation
            gpt_comment = self.generate_kogpt2_comment(user_text, emotion_label_only)
            if gpt_comment:
                return f"{gpt_comment}"

        # 3. Phase 1.5: Label-based Specific Advice (Fallback)
        label_comment = self.generate_label_comment(emotion_label_only)
        if label_comment:
             return label_comment

        try:
            label = prediction_text.split()[0] # e.g. "행복해"
            
            # 3. Try Legacy AI Generation (Seq2Seq) - Deprecated but kept as backup
            ai_generated = None
            if self.enc_model:
                try:
                    # Pass the label as context since we don't use full text for Seq2Seq yet
                    ai_generated = self.generate_ai_comment(label)
                except:
                    pass
            
            if ai_generated:
                return f"{ai_generated}"
            
            # 4. Fallback
            return "오늘 하루도 수고 많으셨어요."
            
        except Exception as e:
            print(f"Comment Gen Error: {e}")
            return "당신의 마음을 이해해요."


    def update_keywords(self, text, mood_level):
        """
        Learn new keywords from the text based on the user's provided mood_level.
        mood_level: 1-5 (User input)
        Mapping: 5->0(Happy), 4->1(Calm), 3->2(Neutral), 2->3(Depressed), 1->4(Angry)
        """
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

# Singleton instance
ai_analyzer = EmotionAnalysis()
