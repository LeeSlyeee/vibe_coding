
import sys
import os
import random
from datetime import datetime, timedelta


# Add backend to sys.path to allow imports
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Move script execution context to backend
# Or simply import assuming we are in root and backend is a package

try:
    from backend.app import app, db
    from backend.models import Diary
    from backend.ai_brain import EmotionAnalysis
except ImportError:
    # Fallback if running directly inside backend
    from app import app, db
    from models import Diary
    from ai_brain import EmotionAnalysis

# 1. Procedural Generation Components


# Enhanced lists for longer, richer sentences

times = [
    "햇살이 따스하게 비추는 아침 일찍,", "어둠이 짙게 깔린 늦은 밤,", "나른함이 몰려오는 오후 3시쯤,", 
    "모두가 잠든 고요한 새벽 2시에,", "퇴근 후 지친 몸을 이끌고 집에 오는 길에,", "주말의 여유로운 아침 식사 후에,"
]

activities = [
    "공원을 천천히 산책하다가 문득,", "오랫동안 읽지 않던 책을 꺼내 읽다가,", "밀린 업무를 처리하느라 정신없이 보내다가,", 
    "오랜 친구와 깊은 대화를 나누다가,", "혼자 조용히 영화를 감상하다가,", "창밖으로 지나가는 사람들을 멍하니 바라보다가,", 
    "먼지 쌓인 옛 일기장을 우연히 펼쳐보다가,", "나를 위해 정성스럽게 요리를 하다가,", 
    "카페에 앉아 씁쓸한 커피를 마시다가,", "땀이 날 정도로 열심히 운동을 하고 나서,", 
    "이어폰을 꽂고 좋아하는 음악을 듣다가,", "방 구석구석을 깨끗이 청소하다가,"
]

events = [
    "예전에는 미처 알지 못했던 소중한 사실을 깨달았다.", "그토록 고민하던 문제가 생각보다 쉽게 해결되었다.", 
    "사소한 오해로 인해 친구와 말다툼을 하게 되었다.", "기다리고 기다리던 반가운 소식이 전해졌다.", 
    "길가에 핀 이름 모를 꽃이 눈에 들어왔다.", "아끼던 물건을 실수로 떨어뜨려 깨뜨리고 말았다.", 
    "생각지도 못한 누군가에게서 따뜻한 선물을 받았다.", "나도 모르게 상대방에게 상처 주는 말을 뱉어버렸다.", 
    "열심히 준비했던 일이 예상치 못한 방향으로 흘러갔다.", "몇 달을 미뤄왔던 숙제를 드디어 끝마쳤다.", 
    "갑자기 쏟아지는 소나기에 흠뻑 젖어버렸다.", "하늘을 붉게 물들이는 아름다운 노을을 한참동안 바라보았다.", 
    "용기를 내어 부모님께 사랑한다는 말을 전했다.", "낯선 사람의 작은 친절에 마음이 따뜻해졌다.", 
    "꽉 막힌 도로 위에서 하염없이 시간을 흘려보냈다.", "달콤한 케이크 한 조각으로 기분을 달랬다.", 
    "거울 속에 비친 내 얼굴이 오늘따라 낯설게 느껴졌다.", "바쁜 일상 속에 잊고 지냈던 약속이 떠올랐다."
]

# Using conjunctions to lengthen sentences
conjunctions = ["그리고나서", "그런데 갑자기", "그 순간,", "잠시 후,", "그러자 문득"]

# Map emotions to mood levels (5: Happy, 4: Calm, 3: Neutral, 2: Sad, 1: Angry)
emotion_map = {
    "가슴 깊은 곳에서부터 벅차오르는 기쁨을 느꼈다.": 5,
    "말로 설명할 수 없는 텅 빈 듯한 허전함이 밀려왔다.": 2,
    "머리 끝까지 화가 치밀어 올라 주체할 수 없었다.": 1,
    "세상이 무너져 내리는 듯한 깊은 절망감을 맛보았다.": 2,
    "내 주변의 모든 것들이 새삼스레 감사하게 느껴졌다.": 5,
    "알 수 없는 불안감이 마음 한구석을 계속 맴돌았다.": 2,
    "오랫동안 묵혀왔던 체증이 내려가는 듯 홀가분했다.": 4,
    "내 자신이 너무나도 작고 초라하게 느껴져 견딜 수 없었다.": 2,
    "나도 모르게 누군가에게 큰 잘못을 한 것 같아 미안했다.": 2,
    "새로운 시작에 대한 설렘으로 가슴이 두근거렸다.": 5,
    "믿었던 사람에게 배신을 당한 것 같아 참담한 심정이었다.": 1,
    "손가락 하나 까딱하기 싫을 만큼 무기력해졌다.": 2,
    "세상에 나 혼자만 남겨진 듯한 사무치는 외로움을 느꼈다.": 2,
    "차가웠던 마음이 누군가의 온기로 녹아내리는 기분이었다.": 4
}

emotions = list(emotion_map.keys())

reflections = [
    "오랜만에 느끼는 이 감정을 있는 그대로 받아들이기로 했다.", "다음부터는 좀 더 신중하게 행동해야겠다고 다짐했다.", 
    "비록 오늘은 힘들었지만, 내일은 분명 더 나은 하루가 될 것이다.", "이 또한 지나가리라 믿으며 마음을 다잡았다.", 
    "이제는 남이 아닌 나 자신을 좀 더 아껴주고 사랑해야겠다.", "이 순간의 소중함을 영원히 잊지 않고 기억하고 싶다.", 
    "결국 내 행복은 내 마음가짐에 달려있다는 것을 다시금 깨달았다.", "피할 수 없는 고통이라면 차라리 즐기는 게 낫지 않을까.", 
    "지금 겪는 이 시련도 훗날 나를 성장시키는 거름이 될 것이다.", "누구에게나 일어날 수 있는 일이니, 너무 자책하지 말자.", 
    "세상에 힘든 건 나뿐만이 아니라는 사실에 묘한 위로를 받았다.", "소소한 행복들이 모여 결국 큰 기쁨을 만든다는 걸 알게 되었다."
]

self_talks = [
    "괜찮아, 넌 잘하고 있어.", "오늘도 정말 수고 많았어.", "실수해도 괜찮아, 다시 시작하면 돼.",
    "너는 사랑받을 자격이 충분해.", "조금만 더 힘내자.", "지나간 일에 너무 연연하지 마.",
    "너의 속도대로 가면 돼.", "충분히 슬퍼하고 다시 일어서자.", "너는 혼자가 아니야.",
    "내일은 오늘보다 더 빛날 거야.", "스스로를 믿어봐."
]

def generate_sentence():
    t = random.choice(times)
    a = random.choice(activities)
    e = random.choice(events)
    c = random.choice(conjunctions)
    em_text = random.choice(emotions) # Pick the key
    r = random.choice(reflections)
    
    # Return both text and the mapped mood level
    mood = emotion_map[em_text]
    
    # Combine into a longer, more structured story
    # Structure: Time + Activity + Event. + Conjunction + Emotion + Reflection
    full_text = f"{t} {a} {e} {c} {em_text} {r}"
    return full_text, mood

def generate_entries(n=100):
    ai = EmotionAnalysis()
    
    with app.app_context():
        # Get user (default ID 1)
        # Check if user exists, if not, careful
        # Assuming user exists as per previous context
        
        print(f"Generating {n} unique diary entries...")
        
        generated_count = 0
        seen_texts = set()
        
        while generated_count < n:
            text, mood = generate_sentence() # Receive both
            
            # Ensure uniqueness
            if text in seen_texts:
                continue
            seen_texts.add(text)
            
            # Generate random sub-fields driven by the main text logic
            # For variety, let's mix parts. 
            # Actually, let's make `text` the 'event' + 'emotion_desc'.
            # 'emotion_meaning' and 'self_talk' can be derived or randomized carefully.
            
            # Breakdown
            # event = t + a + e
            # emotion_desc = em
            # emotion_meaning = r
            # self_talk = random
            
            # Breakdown using conjunctions
            # full_text = t + a + e + c + em + r
            # Simplified split logic:
            
            sentences_split = text.split(". ")
            if len(sentences_split) >= 2:
                 event_part = sentences_split[0] + "." # t + a + e
                 # Remainder: c + em + r
                 # emotion_part: c + em
                 # meaning_part: r
                 
                 rest = ". ".join(sentences_split[1:])
                 # Find last sentence for meaning
                 last_split = rest.rsplit(". ", 1)
                 if len(last_split) > 1:
                     emotion_part = last_split[0] + "."
                     meaning_part = last_split[1]
                 else:
                     emotion_part = rest
                     meaning_part = ""
            else:
                 event_part = text
                 emotion_part = ""
                 meaning_part = ""
            
            st = random.choice(self_talks)
            
            # mood is already determined by generate_sentence matching the emotion text!
            # mood = random.randint(1, 5) # Random mood level
            
            # Create timestamp (spread over last 3 months)
            days_ago = random.randint(0, 90)
            created_at = datetime.now() - timedelta(days=days_ago)

            diary = Diary(
                user_id=1,
                event=event_part,
                emotion_desc=emotion_part,
                emotion_meaning=meaning_part,
                self_talk=st,
                mood_level=mood,
                created_at=created_at
            )
            
            # AI Analysis Trigger
            # Combine text for analysis
            full_input = f"{event_part} {emotion_part} {meaning_part} {st}"
            prediction = ai.predict(full_input)
            
            # Generate Comment
            # AI uses prediction text to generate comment
            # Note: ai_brain.generate_comment does not exist. It has generate_kogpt2_comment.
            
            # Extract label string if prediction is like "Label (80%)"
            label = prediction
            
            comment = ai.generate_kogpt2_comment(full_input, label)
            if not comment:
                 # Fallback
                 comment = ai.generate_keyword_comment(full_input) or "힘내세요."
            
            diary.ai_prediction = prediction
            diary.ai_comment = comment
            
            db.session.add(diary)
            generated_count += 1
            
            if generated_count % 10 == 0:
                print(f"Generated {generated_count}/{n}...")
        
        db.session.commit()
        print("Successfully inserted 100 entries with AI analysis.")

if __name__ == "__main__":
    generate_entries(1000)
