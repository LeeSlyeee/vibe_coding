
import json
import os
import random
import sys

def sample_text():
    base_dir = os.path.join(os.getcwd(), 'backend')
    fname = '감성대화말뭉치(최종데이터)_Training.json'
    fpath = os.path.join(base_dir, fname)
    
    code_samples = {}
    
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"Scanning {len(data)} entries...")
        
        for entry in data:
            profile = entry.get('profile', {})
            emotion = profile.get('emotion', {})
            code = emotion.get('type', '')
            
            content = entry.get('talk', {}).get('content', {})
            text = content.get('HS01', '')
            
            if code and text:
                if code not in code_samples:
                    code_samples[code] = []
                
                if len(code_samples[code]) < 3:
                     code_samples[code].append(text)
                     
    except Exception as e:
        print(f"Error: {e}")
        
    print("-" * 50)
    sorted_codes = sorted(code_samples.keys())
    for code in sorted_codes:
        samples = code_samples[code]
        print(f"[{code}]")
        for i, s in enumerate(samples):
            print(f"  {i+1}. {s}")
        print("")

if __name__ == '__main__':
    sample_text()
