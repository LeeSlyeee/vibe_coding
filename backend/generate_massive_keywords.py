import random
from app import app
from models import db, EmotionKeyword

def generate_keywords():
    print("Generating 30,000 unique keywords...")
    
    # 1. Base Roots per Emotion
    roots = {
        0: ["행복", "기쁨", "즐거움", "신남", "설렘", "만족", "뿌듯", "감동", "사랑", "희망", "웃음", "쾌활", "유쾌", "상쾌", "짜릿", "환상", "대박", "좋아", "멋져", "최고"],
        1: ["평온", "편안", "휴식", "여유", "차분", "안정", "고요", "조용", "나른", "포근", "따뜻", "무난", "힐링", "산책", "명상", "잠", "꿈", "바람", "휴일", "주말"],
        2: ["그저", "보통", "평범", "무난", "쏘쏘", "그닥", "애매", "적당", "심심", "지루", "똑같", "반복", "습관", "일상", "어제", "내일", "그냥", "글쎄", "몰라", "아무"],
        3: ["우울", "슬픔", "눈물", "고통", "상처", "후회", "자책", "비참", "절망", "포기", "외로움", "고독", "쓸쓸", "지침", "피곤", "무기력", "답답", "한숨", "걱정", "불안"],
        4: ["화", "분노", "짜증", "열받", "폭발", "격분", "증오", "미움", "싸움", "다툼", "욕", "저주", "불쾌", "억울", "어이", "황당", "환장", "미쳐", "돌아", "박살"]
    }
    
    # 2. Prefixes (Intensifiers/Modifiers)
    prefixes = [
        "", "정말", "진짜", "너무", "완전", "겁나", "핵", "개", "참", "매우", "엄청", "상당히", "꽤", "좀", "많이", 
        "무지", "되게", "아주", "극도로", "심히", "왕", "짱", "갓", "킹", "슈퍼", "초", "울트라", "대따", "허벌나게", "오지게",
        "확", "막", "걍", "굳이", "특히", "유독", "오늘따라", "이제", "방금", "항상", "늘", "맨날", "자꾸"
    ]
    
    # 3. Suffixes (Endings/Auxiliaries)
    suffixes = [
        "", "하다", "했다", "해", "했어", "하네", "한듯", "함", "하냐", "하군", "하구나", "한가", "할까", "하겠지",
        "해요", "했어요", "합니다", "했습니다", "하네요", "한대", "한데", "하지", "하죠", "하길", "하자", "할래",
        "거야", "건가", "것같아", "일까", "인가", "이네", "이다", "이었어", "였다", "였네", "이군요", "이구나"
    ]
    
    # Additional Random Chars to force uniqueness if needed
    random_chars = ["!", "!!", "~", "...", "..", "ㅋ", "ㅋㅋ", "ㅎㅎ", "ㅠㅠ", ";;", "?", "?!"]

    new_keywords = []
    seen = set()
    
    # Pre-load existing to avoid dups
    with app.app_context():
        existing = db.session.query(EmotionKeyword.keyword).all()
        for r in existing:
            seen.add(r[0])
            
    target_count = 30000
    
    while len(new_keywords) < target_count:
        # Pick emotion
        emotion_id = random.randint(0, 4)
        root = random.choice(roots[emotion_id])
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        
        # Construct word
        # Strategy: Prefix + Root + Suffix
        # Sometimes join with space, sometimes no space for variety
        if random.random() > 0.5:
            word = f"{prefix}{root}{suffix}"
        else:
            word = f"{prefix} {root}{suffix}".strip()
            
        # Add random punctuation occasionally
        if random.random() > 0.7:
             word += random.choice(random_chars)
             
        word = word.strip()
        
        if len(word) < 2: continue
        if word in seen: continue
        
        seen.add(word)
        new_keywords.append({
            "keyword": word,
            "emotion_label": emotion_id,
            "frequency": random.randint(1, 100) # Give random frequency
        })
        
        if len(new_keywords) % 5000 == 0:
            print(f"Generated {len(new_keywords)}...")

    print("Inserting into DB...")
    
    with app.app_context():
        # Insert in chunks
        chunk_size = 1000
        for i in range(0, len(new_keywords), chunk_size):
            chunk = new_keywords[i:i+chunk_size]
            db.session.bulk_insert_mappings(EmotionKeyword, chunk)
            db.session.commit()
            print(f"Inserted chunk {i//chunk_size + 1}/{len(new_keywords)//chunk_size + 1}")
            
    print("Done!")

if __name__ == "__main__":
    generate_keywords()
