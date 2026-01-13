
import os
from app import app, db
from models import Diary
from ai_analysis import ai_analyzer
import time

def update_all_diaries():
    print("Starting Deep Learning Analysis for ALL diaries...")
    print("Note: This might take a few minutes as we need to process 1000+ entries.")
    
    with app.app_context():
        # Ensure model is ready (it initializes on import, but let's confirm usage)
        # prediction logic handles fallback if TF missing, but we expect TF to be present now.
        
        diaries = Diary.query.all()
        total = len(diaries)
        print(f"Found {total} diary entries to analyze.")
        
        count = 0
        start_time = time.time()
        
        for entry in diaries:
            # Combine content for better context or just use event?
            # AI model was trained on short texts. 'event' + 'emotion_desc' might be good.
            # Let's use 'event' primarily as it's the main factual description.
            # "오늘은 친구와 맛집을 갔다."
            
            text_to_analyze = entry.event
            if entry.emotion_desc:
                text_to_analyze += " " + entry.emotion_desc
                
            # Predict Emotion
            prediction = ai_analyzer.predict(text_to_analyze)
            
            # Generate Comment
            # We pass the prediction string to generate_comment
            comment = ai_analyzer.generate_comment(prediction)
            
            # Update DB
            entry.ai_prediction = prediction
            entry.ai_comment = comment
            
            count += 1
            if count % 100 == 0:
                elapsed = time.time() - start_time
                print(f"Processed {count}/{total} entries... ({elapsed:.1f}s)")
                db.session.commit() # Commit in batches
                
        db.session.commit()
        print(f"Completed! Updated {count} entries.")

if __name__ == "__main__":
    # Ensure we don't skip training here
    if 'SKIP_TRAINING' in os.environ:
        del os.environ['SKIP_TRAINING']
        
    update_all_diaries()
