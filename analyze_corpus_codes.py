
import json
import os
import sys

def analyze_codes():
    base_dir = os.path.join(os.getcwd(), 'backend')
    files = [
        '감성대화말뭉치(최종데이터)_Training.json',
        '감성대화말뭉치(최종데이터)_Validation.json'
    ]
    
    emotion_counts = {}
    total_count = 0
    
    print(f"Scanning files in {base_dir}...")
    
    for fname in files:
        fpath = os.path.join(base_dir, fname)
        if not os.path.exists(fpath):
            print(f"File not found: {fpath}")
            continue
            
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            print(f"Loaded {fname}: {len(data)} entries.")
            
            for entry in data:
                # Extract emotion type code (e.g., "E10") and user text
                profile = entry.get('profile', {})
                emotion = profile.get('emotion', {})
                etype = emotion.get('type', '')
                
                # Verify valid text exists
                content = entry.get('talk', {}).get('content', {})
                text = content.get('HS01', '')
                
                if etype and text:
                    if etype not in emotion_counts:
                        emotion_counts[etype] = 0
                    emotion_counts[etype] += 1
                    total_count += 1
                    
        except Exception as e:
            print(f"Error reading {fname}: {e}")

    print(f"\nTotal Valid Samples: {total_count}")
    print(f"Unique Emotion Codes Found: {len(emotion_counts)}")
    print("-" * 30)
    
    # Sort by Code (E10, E11...)
    sorted_codes = sorted(emotion_counts.keys())
    for code in sorted_codes:
        print(f"{code}: {emotion_counts[code]} samples")

if __name__ == '__main__':
    analyze_codes()
