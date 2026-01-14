
import os
import sys
import time

# Ensure backend directory is in path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.app import app, db
from backend.models import Diary
from backend.ai_analysis import EmotionAnalysis

def batch_process():
    print("Initializing AI for batch processing...")
    # Initialize a dedicated analyzer
    # This will load the fine-tuned emotion_model.h5 and comment models
    ai = EmotionAnalysis()
    
    with app.app_context():
        # Fetch all diary IDs to process
        # Processing objects directly might be memory intensive if we keep them all in session
        # but 10k is manageable. 
        total_count = db.session.query(Diary).count()
        print(f"Found {total_count} diary entries to process.")
        
        diaries = db.session.query(Diary).all()
        
        print("Starting batch update...")
        start_time = time.time()
        processed = 0
        batch_size = 50
        
        for diary in diaries:
            # Construct context from diary data
            combined_text = f"{diary.event} {diary.emotion_desc} {diary.self_talk}"
            
            # Pass dictionary for intelligent KoGPT-2 prompting
            context_data = {
                "event": diary.event,
                "emotion": diary.emotion_desc,
                "self_talk": diary.emotion_meaning
            }
            
            # 1. Real AI Prediction
            # This uses the fine-tuned LSTM model
            try:
                prediction = ai.predict(combined_text)
                diary.ai_prediction = prediction
            except Exception as e:
                print(f"Prediction error ID {diary.id}: {e}")
            
            # 2. Real AI Comment
            # This uses the Seq2Seq model (KoGPT-2)
            try:
                comment = ai.generate_comment(prediction, context_data)
                diary.ai_comment = comment
            except Exception as e:
                print(f"Comment error ID {diary.id}: {e}")
            
            # 3. Learn Keywords
            # This populates the EmotionKeyword table
            try:
                if diary.mood_level:
                    ai.update_keywords(combined_text, diary.mood_level)
            except Exception as e:
                print(f"Keyword learn error ID {diary.id}: {e}")
                
            processed += 1
            
            # Print progress and commit in chunks
            if processed % batch_size == 0:
                db.session.commit()
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                remaining = (total_count - processed) / rate if rate > 0 else 0
                print(f"Processed {processed}/{total_count} ({rate:.1f} entries/sec) - Est. remaining: {remaining/60:.1f} min")

        # Final commit
        db.session.commit()
        print(f"Batch processing complete! Updated {processed} entries.")

if __name__ == '__main__':
    batch_process()
