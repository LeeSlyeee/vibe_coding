
import json
import os
import sys

def extract_labels():
    base_dir = os.path.join(os.getcwd(), 'backend')
    fname = '감성대화말뭉치(최종데이터)_Training.json'
    fpath = os.path.join(base_dir, fname)
    
    code_map = {}
    
    try:
        if not os.path.exists(fpath):
            print(f"File not found: {fpath}")
            return

        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"Scanning {len(data)} entries for emotion labels...")
        
        for entry in data:
            profile = entry.get('profile', {})
            emotion = profile.get('emotion', {})
            code = emotion.get('type', '')
            
            # Try to find human readable label
            # Structure usually: emotion: { type: "E10", value: "분노" } or similar?
            # Let's inspect 'class' or 'value' field if exists.
            # Usually the dataset has "emotion-id" and "type". 
            # If 'value' doesn't exist, we might need to rely on the manual documentation or infer from context.
            # Let's check keys available in 'emotion' dict.
            
            # Based on standard usage of this corpus:
            # Code is 'type' (E10).
            # The *Big* class is 'value' (Angry).
            # But the *Sub* class might be implicit or in another field.
            
            # Let's print the first entry's emotion dict to see structure
            if len(code_map) == 0:
                print(f"Sample Emotion Dict: {emotion}")
                
            # If sub-class isn't in JSON, I will have to map E-codes manually based on AI Modification Plan I verified earlier. 
            # But let's check if there is a 'detail' field.
            pass

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    extract_labels()
