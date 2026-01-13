from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import EmotionKeyword
from config import Config

# Setup direct DB connection for initial seeding
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

keywords_data = {
    0: ["행복", "좋", "즐거", "기쁨", "최고", "신나", "사랑", "보람", "뿌듯", "웃음", "재밌", "감사"],
    1: ["평온", "편안", "조용", "여유", "차분", "쉬", "힐링", "안정", "따뜻", "낮잠"],
    2: ["그저", "보통", "평범", "무난", "별일", "쏘쏘", "그냥", "적당", "글쎄"],
    3: ["우울", "슬퍼", "외롭", "지쳐", "힘들", "눈물", "상처", "후회", "좌절", "아프", "속상"],
    4: ["화가", "짜증", "분노", "열받", "미워", "억울", "어이없", "신경질", "싸웠", "답답"]
}

def seed_keywords():
    try:
        count = 0
        for label, words in keywords_data.items():
            for word in words:
                # Check if exists
                exists = session.query(EmotionKeyword).filter_by(keyword=word).first()
                if not exists:
                    new_kw = EmotionKeyword(keyword=word, emotion_label=label, frequency=10) # Initial high freq
                    session.add(new_kw)
                    count += 1
        session.commit()
        print(f"Seeded {count} new keywords.")
    except Exception as e:
        session.rollback()
        print(f"Error seeding: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_keywords()
