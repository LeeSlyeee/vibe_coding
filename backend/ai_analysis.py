import numpy as np
import os
import random
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config
try:
    from models import EmotionKeyword
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
    import pandas as pd
    TENSORFLOW_AVAILABLE = True
except ImportError as e:
    TENSORFLOW_AVAILABLE = False
    print(f"Warning: TensorFlow not found. Error: {e}")
    print("Using simple keyword-based sentiment analysis.")

class EmotionAnalysis:
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.max_len = 50
        self.vocab_size = 0
        
        # 5 Emotion Classes
        self.classes = ["행복해", "평온해", "그저그래", "우울해", "화가나"]
        
        # We will load keywords from DB for fallback/learning
        self.db_engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        self.Session = sessionmaker(bind=self.db_engine)

        # Initial Training Data (Hybrid: Hardcoded + GoEmotions)
        self.train_texts = [
            # 0. 행복해
            "너무 재밌네요", "최고예요", "오늘 정말 행복했다", "기분이 아주 좋습니다", "즐거운 하루",
            "보람찬 하루", "성취감을 느꼈다", "뿌듯하다", "사랑합니다", "친구들과 즐거운 시간",
            "맛있는거 먹어서 신난다", "합격해서 기쁘다", "선물을 받아서 좋다", "웃음이 멈추지 않는다", "신나는 음악",
            
            # 1. 평온해
            "마음이 편안하다", "조용한 하루", "여유로운 저녁", "산책을 하니 상쾌하다", "차 한잔의 여유",
            "아무 걱정 없이 쉬었다", "명상을 했다", "잠을 푹 잤다", "잔잔한 음악을 들었다", "평화롭다",
            "따뜻한 햇살", "바람이 시원하다", "책을 읽으며 힐링", "차분해지는 기분", "안정된 느낌",

            # 2. 그저그래
            "그저 그런 하루", "평범한 일상", "특별한 일은 없었다", "그냥 그랬다", "무난한 하루",
            "별일 없었다", "똑같은 하루", "지루하지도 재미있지도 않다", "쏘쏘", "보통이다",
            "글쎄 잘 모르겠다", "나쁘지 않다", "적당하다", "그럭저럭", "할만 했다",

            # 3. 우울해
            "오늘 너무 슬펐다", "우울해요", "마음이 아프다", "외롭다", "지친다",
            "눈물이 난다", "힘든 하루였어요", "실수해서 속상하다", "후회된다", "아무것도 하기 싫다",
            "좌절감을 느꼈다", "상처받았다", "그리워요", "무기력하다", "가슴이 답답하다",

            # 4. 화가나
            "화가 난다", "짜증나요", "정말 열받는다", "기분이 나쁘다", "싸웠다",
            "억울하다", "미워 죽겠다", "분노가 치민다", "어이없다", "용서할 수 없다",
            "답답해서 미치겠다", "신경질이 난다", "폭발할 것 같다", "기분 잡쳤다", "말도 안 된다"
        ]
        
        # Hardcoded Labels
        labels_list = [0]*15 + [1]*15 + [2]*15 + [3]*15 + [4]*15
        self.train_labels = np.array(labels_list)

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
                "당신의 평화를 방해한 것들이 밉네요. 오늘은 일찍 쉬면서 마음을 다스려봐요."
            ]
        }
        
        # Initialize attributes
        self.comment_tokenizer = None
        self.comment_model = None
        self.enc_model = None 
        self.dec_model = None
        self.comment_max_len = 20

        if TENSORFLOW_AVAILABLE:
            print("Initializing AI Emotion Analysis Model (5-Class LSTM)...")
            self.tokenizer = Tokenizer()
            
            if os.environ.get('SKIP_TRAINING'):
                print("Skipping training logic (SKIP_TRAINING active).")
                return
            
            # --- Load GoEmotions Data & Map Labels ---
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                csv_path = os.path.join(base_dir, 'goemotions_korean_train.csv')
                
                if os.path.exists(csv_path):
                    print(f"Loading extended dataset from {csv_path}...")
                    df = pd.read_csv(csv_path)
                    
                    # Ensure strings
                    df['text'] = df['text'].astype(str)
                    
                    # Mapping Dictionary (28 -> 5)
                    # 0: 행복해, 1: 평온해, 2: 그저그래, 3: 우울해, 4: 화가나
                    # GoEmotions: 0-27
                    label_map = {
                        0: 0, 1: 0, 5: 0, 13: 0, 15: 0, 17: 0, 18: 0, 20: 0, 21: 0, 23: 0, # Happpy...
                        4: 1, 8: 1, 22: 1, # Calm/Positive
                        6: 2, 7: 2, 26: 2, 27: 2, # Neutral/Ambiguous
                        9: 3, 12: 3, 16: 3, 19: 3, 24: 3, 25: 3, # Depressed/Sad
                        2: 4, 3: 4, 10: 4, 11: 4, 14: 4 # Angry/Fees/Disgust
                    }
                    
                    # Function to map labels
                    def map_emotion(label_str):
                        try:
                            # Labels in CSV might be "0", or "2,15" (multilabel)
                            # We take the first label for simplicity in this single-label project
                            first_label = int(str(label_str).split(',')[0])
                            return label_map.get(first_label, 2) # Default to Neutral if map fails
                        except:
                            return 2

                    df['target'] = df['labels'].apply(map_emotion)
                    
                    # Merge with hardcoded data
                    new_texts = df['text'].tolist()
                    new_labels = df['target'].tolist()
                    
                    self.train_texts.extend(new_texts)
                    # Combine numpy arrays
                    self.train_labels = np.concatenate((self.train_labels, np.array(new_labels)))
                    
                    print(f"Total training samples: {len(self.train_texts)}")
                else:
                    print("GoEmotions CSV not found. Using small hardcoded dataset.")
            except Exception as e:
                print(f"Error loading GoEmotions: {e}. Using small hardcoded dataset.")

            self._train_initial_model()
            
            # Setup for Comment Generation (Lazy load or init)
            # ... (Existing code)
            
            print("AI Model initialized.")
        else:
            print("Initializing Fallback Emotion Analysis (Keyword based - 5 classes)...")

    def _train_initial_model(self):
        # Increased Vocab size for larger dataset
        self.tokenizer.fit_on_texts(self.train_texts)
        self.vocab_size = len(self.tokenizer.word_index) + 1
        print(f"Emotion Vocab Size: {self.vocab_size}")
        
        sequences = self.tokenizer.texts_to_sequences(self.train_texts)
        X_train = pad_sequences(sequences, maxlen=self.max_len)
        y_train = self.train_labels
        
        self.model = Sequential()
        self.model.add(Embedding(self.vocab_size, 128, input_length=self.max_len)) 
        self.model.add(LSTM(128, dropout=0.2, recurrent_dropout=0.2)) # Increased capacity & dropout
        self.model.add(Dense(64, activation='relu')) 
        self.model.add(Dropout(0.3))
        self.model.add(Dense(5, activation='softmax')) 
        
        self.model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        
        # Train for fewer epochs if dataset is huge, or more? 
        # 40k samples -> 5 epochs is enough for a prototype to see convergence without waiting too long
        print("Training Emotion Classifier...")
        self.model.fit(X_train, y_train, epochs=5, batch_size=32, validation_split=0.1, verbose=1) 


    def predict(self, text):
        if not text: return "분석 불가"

        if TENSORFLOW_AVAILABLE and self.model:
            try:
                sequences = self.tokenizer.texts_to_sequences([text])
                padded = pad_sequences(sequences, maxlen=self.max_len)
                prediction = self.model.predict(padded)[0]
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
            # Fetch all keywords
            # Optimized: Could cache this and update periodically, but for now fetch on specific calls if not heavy
            # Actually, fetching all keywords every time is slow. Let's do a simple query or cache.
            # Since this is a prototype, fetching is fine for small DB.
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

    def train_comment_model(self):
        """
        Train a Seq2Seq model using ChatbotData.csv
        """
        if not TENSORFLOW_AVAILABLE: return

        print("Training Comment Generation Model (Seq2Seq)...")
        try:
            import os
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(base_dir, 'ChatbotData.csv')
            df = pd.read_csv(data_path)
            # Limit data for speed in prototype? Or use all. 12k is fine.
            df = df.sample(frac=1).reset_index(drop=True) # Shuffle
            
            questions = df['Q'].astype(str).tolist()
            answers = df['A'].apply(lambda x: 'sos ' + str(x) + ' eos').tolist()
            
            # Shared Tokenizer
            self.comment_tokenizer = Tokenizer()
            self.comment_tokenizer.fit_on_texts(questions + answers)
            
            vocab_size = len(self.comment_tokenizer.word_index) + 1
            print(f"Vocab Size: {vocab_size}")

            # Encoder Data
            tokenized_Q = self.comment_tokenizer.texts_to_sequences(questions)
            encoder_input_data = pad_sequences(tokenized_Q, maxlen=self.comment_max_len, padding='post')
            
            # Decoder Data
            tokenized_A = self.comment_tokenizer.texts_to_sequences(answers)
            decoder_input_data = pad_sequences(tokenized_A, maxlen=self.comment_max_len, padding='post')
            
            # Decoder Target (Shifted-by-one)
            # Use the padded decoder_input_data to ensure consistent length
            decoder_target_data = np.zeros_like(decoder_input_data, dtype="float32")
            decoder_target_data[:, :-1] = decoder_input_data[:, 1:]
            
            decoder_target_data = np.expand_dims(decoder_target_data, -1)

            # Model Architecture
            latent_dim = 256
            
            # Encoder
            encoder_inputs = Input(shape=(None,))
            enc_emb = Embedding(vocab_size, latent_dim)(encoder_inputs)
            encoder_lstm = LSTM(latent_dim, return_state=True)
            encoder_outputs, state_h, state_c = encoder_lstm(enc_emb)
            encoder_states = [state_h, state_c]
            
            # Decoder
            decoder_inputs = Input(shape=(None,))
            dec_emb_layer = Embedding(vocab_size, latent_dim)
            dec_emb = dec_emb_layer(decoder_inputs)
            decoder_lstm = LSTM(latent_dim, return_sequences=True, return_state=True)
            decoder_outputs, _, _ = decoder_lstm(dec_emb, initial_state=encoder_states)
            decoder_dense = Dense(vocab_size, activation='softmax')
            decoder_outputs = decoder_dense(decoder_outputs)
            
            self.comment_model = Model([encoder_inputs, decoder_inputs], decoder_outputs)
            self.comment_model.compile(optimizer='rmsprop', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
            
            print("Fitting Seq2Seq Model ( This may take time )...")
            # Epochs=20 for better results, but 5 for speed in strict mode plan
            self.comment_model.fit([encoder_input_data, decoder_input_data], decoder_target_data,
                                   batch_size=64, epochs=5, validation_split=0.2)
                                   
            print("Comment Model Trained.")
            
            # Store Inference Models
            self.enc_model = Model(encoder_inputs, encoder_states)
            
            dec_state_input_h = Input(shape=(latent_dim,))
            dec_state_input_c = Input(shape=(latent_dim,))
            dec_states_inputs = [dec_state_input_h, dec_state_input_c]
            
            dec_emb2 = dec_emb_layer(decoder_inputs)
            dec_outputs2, state_h2, state_c2 = decoder_lstm(dec_emb2, initial_state=dec_states_inputs)
            dec_states2 = [state_h2, state_c2]
            dec_outputs2 = decoder_dense(dec_outputs2)
            
            self.dec_model = Model([decoder_inputs] + dec_states_inputs, [dec_outputs2] + dec_states2)
            
        except Exception as e:
            print(f"Error training comment model: {e}")

    def generate_ai_comment(self, text):
        if not self.enc_model or not self.comment_tokenizer:
            return None
            
        try:
            # Preprocess
            seq = self.comment_tokenizer.texts_to_sequences([text])
            input_seq = pad_sequences(seq, maxlen=self.comment_max_len, padding='post')
            
            # Encode
            states_value = self.enc_model.predict(input_seq)
            
            # Generate
            target_seq = np.zeros((1,1))
            target_seq[0, 0] = self.comment_tokenizer.word_index['sos']
            
            decoded_sentence = ''
            stop_condition = False
            
            while not stop_condition:
                output_tokens, h, c = self.dec_model.predict([target_seq] + states_value)
                
                # Sample a token
                sampled_token_index = np.argmax(output_tokens[0, -1, :])
                sampled_word = self.comment_tokenizer.index_word.get(sampled_token_index, '')
                
                if sampled_word == 'eos' or len(decoded_sentence) > 50:
                    stop_condition = True
                else:
                    decoded_sentence += ' ' + sampled_word
                
                # Update target seq
                target_seq = np.zeros((1, 1))
                target_seq[0, 0] = sampled_token_index
                
                # Update states
                states_value = [h, c]
                
            return decoded_sentence.strip()
            
        except Exception as e:
            print(f"Gen Error: {e}")
            return None

    def generate_comment(self, prediction_text):
        """
        Generate a supportive comment.
        Priority: 1. AI Generation (Seq2Seq) 2. Random Selection (Fallback)
        """
        if not prediction_text or "분석 불가" in prediction_text:
            return "당신의 이야기를 더 들려주세요. 항상 듣고 있을게요."

        try:
            label = prediction_text.split()[0] # e.g. "행복해"
            
            # 1. Try AI Generation
            # We want to feed the *label* or the *original text*?
            # Ideally the original diary text. But here we only have prediction_text.
            # However, `prediction_text` is just "Label score".
            # The prompt implies generating comment based on "prediction" or "diary"?
            # Function signature is `generate_comment(self, prediction_text)`.
            # We will use the 'Label' as the input prompt to the chatbot model (simple approach)
            # OR we can assume we might pass the full text later.
            # For now, let's use the Label as the input. e.g. "나 지금 행복해" (simulated)
            
            ai_generated = None
            if self.enc_model:
                # Synthesize a prompt from label
                prompt = f"나 지금 {label}" 
                ai_generated = self.generate_ai_comment(prompt)
                
            if ai_generated and len(ai_generated) > 2:
                return f"{ai_generated} (AI)"
            
            # 2. Fallback (Random Selection)
            if label in self.comment_bank:
                return random.choice(self.comment_bank[label])
            else:
                return "당신의 감정을 소중히 간직하세요."
        except Exception as e:
            print(f"Comment Gen Error: {e}")
            return "당신의 감정을 소중히 간직하세요."

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
