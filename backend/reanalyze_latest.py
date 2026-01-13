from app import app
from models import db, Diary
from ai_analysis import ai_analyzer

def reanalyze():
    with app.app_context():
        # Get latest diary
        diary = db.session.query(Diary).order_by(Diary.created_at.desc()).first()
        
        if not diary:
            print("No diary entries found to re-analyze.")
            return

        print(f"Found Diary ID {diary.id}")
        print(f"Content: {diary.event[:30]}... | {diary.emotion_desc[:20]}...")
        print(f"Old Prediction: {diary.ai_prediction}")
        
        # Re-predict
        text = f"{diary.event} {diary.emotion_desc}"
        new_prediction = ai_analyzer.predict(text)
        
        # Update
        diary.ai_prediction = new_prediction
        db.session.commit()
        
        print(f"New Prediction: {new_prediction}")

if __name__ == "__main__":
    reanalyze()
