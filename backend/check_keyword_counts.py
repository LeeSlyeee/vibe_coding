from app import app
from models import db, EmotionKeyword

def check_counts():
    classes = ["행복해", "평온해", "그저그래", "우울해", "화가나"]
    with app.app_context():
        results = db.session.query(EmotionKeyword.emotion_label, db.func.count(EmotionKeyword.id)).group_by(EmotionKeyword.emotion_label).all()
        
        print("\n--- Emotion Keyword Counts ---")
        total = 0
        counts = {i: 0 for i in range(5)}
        
        for label, count in results:
            counts[label] = count
            total += count
            
        for i, label_name in enumerate(classes):
            print(f"{label_name} (ID: {i}): {counts[i]} keywords")
            
        print(f"Total Keywords: {total}")

if __name__ == "__main__":
    check_counts()
