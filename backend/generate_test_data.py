import os
from datetime import datetime, timedelta
import random
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from bson.objectid import ObjectId

# Configuration
MONGO_URI = 'mongodb://localhost:27017/mood_diary_db'

def get_seasonal_weather(date):
    month = date.month
    if month in [12, 1, 2]: # Winter
        return random.choice(['눈', '맑음', '흐림', '바람', '추움'])
    elif month in [3, 4, 5]: # Spring
        return random.choice(['맑음', '구름', '봄비', '미세먼지', '포근함'])
    elif month in [6, 7, 8]: # Summer
        return random.choice(['비', '맑음', '무더위', '태풍', '습함'])
    else: # Fall
        return random.choice(['맑음', '구름', '낙엽', '쌀쌀', '쾌청'])

def generate_long_text(topic):
    # Generates at least 3 paragraphs
    paragraphs = []
    
    sentences_pool = [
        "오늘 하루를 돌아보며 이 글을 적습니다.",
        "마음속에 담아두었던 생각들을 천천히 꺼내어 봅니다.",
        "시간이 지나면 잊혀질 감정들이지만, 이렇게 기록으로 남겨두고 싶습니다.",
        "가끔은 아무것도 하지 않고 쉬고 싶은 마음이 굴뚝같지만, 내일을 위해 힘을 냅니다.",
        "주변 사람들과의 관계 속에서 때로는 기쁨을, 때로는 슬픔을 느끼곤 합니다.",
        "내가 진정으로 원하는 것이 무엇인지 깊이 고민해보는 시간이었습니다.",
        "창밖을 보니 계절의 변화가 느껴져 기분이 묘해집니다.",
        "사소한 일에도 감사할 줄 아는 마음을 가지려고 노력했습니다.",
        "힘든 순간도 있었지만, 결국은 잘 이겨낼 것이라 믿습니다.",
        "오늘 느꼈던 이 감정은 나에게 어떤 의미로 남게 될까요?",
        "앞으로 더 나은 내가 되기 위해 어떤 노력을 해야 할지 생각해봅니다.",
        "조용한 밤, 혼자만의 시간을 가지며 하루를 정리합니다."
    ]
    
    for i in range(3): # 3 Paragraphs
        paragraph_sentences = [f"[{topic} - {i+1}번째 문단 시작]"]
        # Add 3-5 random sentences per paragraph
        indices = random.sample(range(len(sentences_pool)), k=random.randint(3, 5))
        for idx in indices:
            paragraph_sentences.append(sentences_pool[idx])
        paragraph_sentences.append(f"[{i+1}번째 문단 끝]")
        
        paragraphs.append(" ".join(paragraph_sentences))
        
    return "\n\n".join(paragraphs)

def run():
    # Connect to MongoDB
    try:
        client = MongoClient(MONGO_URI)
        db = client.get_database()
        users_col = db.users
        diaries_col = db.diaries
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    # 1. Check or Create User 'test'
    username = 'test'
    password = 'test$1234' # Simple password
    
    user = users_col.find_one({'username': username})
    
    if not user:
        print(f"Creating '{username}' user...")
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        user_id = users_col.insert_one({
            'username': username,
            'password_hash': hashed_password,
            'created_at': datetime.utcnow()
        }).inserted_id
        print(f"✅ User '{username}' created with ID: {user_id}")
    else:
        user_id = user['_id']
        print(f"✅ Found '{username}' user with ID: {user_id}")

    user_id_str = str(user_id)

    # 2. Generate 100 entries
    print("Generating 100 diary entries...")
    entries = []
    
    # Start from today and go back 100 days
    base_date = datetime.now().replace(hour=21, minute=30, second=0, microsecond=0)
    
    # Mood flow pattern to look realistic (sine wave-ish or clustered)
    # Using a random walk with boundaries
    current_mood = 3
    
    for i in range(100):
        # Calculate Date (Backwards from today)
        entry_date = base_date - timedelta(days=i)
        
        # Mood Logic: Random walk (change by -1, 0, +1)
        change = random.choice([-1, 0, 1, 0]) # Bias towards staying same
        current_mood += change
        if current_mood < 1: current_mood = 1
        if current_mood > 5: current_mood = 5
        
        weather = get_seasonal_weather(entry_date)
        
        entry = {
            'user_id': user_id_str, 
            'event': generate_long_text(f"{entry_date.strftime('%Y-%m-%d')}의 특별한 사건"),
            'emotion_desc': generate_long_text("오늘 느꼈던 구체적인 감정"),
            'emotion_meaning': generate_long_text("이 감정이 나에게 주는 의미"),
            'self_talk': generate_long_text("나 스스로에게 해주고 싶은 말"),
            'mood_level': current_mood,
            'weather': weather,
            'temperature': random.randint(-5, 30), # Just random range
            'ai_prediction': "AI 분석 결과: 긍정적이고 희망적인 흐름이 보입니다.",
            'ai_comment': "꾸준히 기록하는 모습이 정말 멋져요! 내일도 좋은 하루 되세요. 🍀",
            'created_at': entry_date
        }
        entries.append(entry)

    # 3. Insert into DB
    if entries:
        # Reverse list to insert chronologically if desired, but batch insert order doesn't strictly matter for storage
        # Inserting...
        result = diaries_col.insert_many(entries)
        print(f"✅ Successfully inserted {len(result.inserted_ids)} diary entries for user '{username}'.")
        print("You can now login with:")
        print(f"Username: {username}")
        print(f"Password: {password} (if newly created, otherwise use existing)")

if __name__ == '__main__':
    run()
