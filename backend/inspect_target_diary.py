
import os
import pymongo
from app import app, mongo, crypto_manager

def inspect_recent_diaries():
    with app.app_context():
        # Find last 5 diaries for user
        diaries = mongo.db.diaries.find({"user_id": "slyeee"}).sort("created_at", -1).limit(5)
        
        print("Checking recent diaries for 'slyeee'...")
        found = False
        
        for diary in diaries:
            print(f"--- Date: {diary.get('created_at')} ---")
            
            try:
                content = crypto_manager.decrypt(diary.get('content'))
                print(f"Content: {content[:50]}...") # Print first 50 chars
                
                if "리부트 프로젝트" in content:
                    print(">>> TARGET DIARY FOUND <<<")
                    found = True
                    
                    # Inspect AI Fields
                    ai_analysis_enc = diary.get('ai_analysis')
                    ai_comment_enc = diary.get('ai_comment')
                    ai_prediction_enc = diary.get('ai_prediction')
                    
                    print(f"Encrypted ai_analysis: {ai_analysis_enc}")
                    
                    if ai_analysis_enc:
                        try:
                            ai_analysis = crypto_manager.decrypt(ai_analysis_enc)
                            print(f"Decrypted ai_analysis: {ai_analysis}")
                        except:
                            print(f"Decrypted ai_analysis: [Failed] {ai_analysis_enc}")
                    else:
                        print("ai_analysis: None")
                        
                    if ai_comment_enc:
                        try:
                            ai_comment = crypto_manager.decrypt(ai_comment_enc)
                            print(f"Decrypted ai_comment: {ai_comment}")
                        except:
                            print("Decrypted ai_comment: [Failed]")
                    
                    if ai_prediction_enc:
                        try:
                            ai_prediction = crypto_manager.decrypt(ai_prediction_enc)
                            print(f"Decrypted ai_prediction: {ai_prediction}")
                        except:
                            print("Decrypted ai_prediction: [Failed]")
                    
                    # Also printing ai_advice locally
                    ai_advice_enc = diary.get('ai_advice')
                    if ai_advice_enc:
                        try:
                            ai_advice = crypto_manager.decrypt(ai_advice_enc)
                            print(f"Decrypted ai_advice: {ai_advice}")
                        except:
                            print("Decrypted ai_advice: [Failed]")

            except Exception as e:
                print(f"Error decrypting content: {e}")
                
        if not found:
            print("Target diary not found in last 5 entries.")

if __name__ == "__main__":
    inspect_recent_diaries()
