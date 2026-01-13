import numpy as np
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
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Embedding, LSTM, Dense, Dropout
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("Warning: TensorFlow not found. Using simple keyword-based sentiment analysis.")

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

        # Initial Training Data (Hardcoded for LSTM initialization)
        #Ideally this should also come from DB, but keeping it simple for now
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
        labels_list = [0]*15 + [1]*15 + [2]*15 + [3]*15 + [4]*15
        self.train_labels = np.array(labels_list)

        if TENSORFLOW_AVAILABLE:
            print("Initializing AI Emotion Analysis Model (5-Class LSTM)...")
            self.tokenizer = Tokenizer()
            self._train_initial_model()
            print("AI Model initialized.")
        else:
            print("Initializing Fallback Emotion Analysis (Keyword based - 5 classes)...")

    def _train_initial_model(self):
        self.tokenizer.fit_on_texts(self.train_texts)
        self.vocab_size = len(self.tokenizer.word_index) + 1
        sequences = self.tokenizer.texts_to_sequences(self.train_texts)
        X_train = pad_sequences(sequences, maxlen=self.max_len)
        y_train = self.train_labels
        
        self.model = Sequential()
        self.model.add(Embedding(self.vocab_size, 64, input_length=self.max_len)) 
        self.model.add(LSTM(64)) 
        self.model.add(Dense(32, activation='relu')) 
        self.model.add(Dense(5, activation='softmax')) 
        self.model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        self.model.fit(X_train, y_train, epochs=50, verbose=0) 

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

    def generate_comment(self, prediction_text):
        """
        Generate a supportive comment based on the prediction label.
        prediction_text format: "Label (Confidence%)" e.g., "행복해 (90.0%)"
        """
        if not prediction_text or "분석 불가" in prediction_text:
            return "당신의 이야기를 더 들려주세요. 항상 듣고 있을게요."

        try:
            # Extract label (split by space)
            label = prediction_text.split()[0]
            
            comments = {
                "행복해": "오늘 하루 정말 행복하셨군요! 이 긍정적인 에너지가 내일도 이어지길 바랄게요. 😊",
                "평온해": "마음이 편안하다니 다행이에요. 따뜻한 차 한 잔으로 하루를 마무리해보는 건 어떨까요? 🍵",
                "그저그래": "평범한 하루였군요. 내일은 좀 더 특별한 일이 생길지도 몰라요! 파이팅 💪",
                "우울해": "많이 힘드셨군요. 오늘 하루는 푹 쉬면서 자신을 토닥여주세요. 당신은 소중한 사람입니다. 💙",
                "화가나": "속상한 일이 있으셨나 봐요. 잠시 심호흡을 하며 마음을 가라앉혀보면 어떨까요? 힘내세요! 🔥"
            }
            
            return comments.get(label, "당신의 감정을 소중히 간직하세요.")
        except:
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
