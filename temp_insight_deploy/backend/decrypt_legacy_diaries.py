import os
import django
import sys
from cryptography.fernet import Fernet

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from haru_on.models import HaruOn

# Key from vibe_coding project (Step 685)
LEGACY_KEY = b'no-cI2OmQ0K2Eb7cNlfmndN159GET62e-YqVncAkjKg='
cipher_suite = Fernet(LEGACY_KEY)

def decrypt_text(text):
    if not text:
        return text
    if not isinstance(text, str):
        return text
    if not text.startswith('gAAAA'):
        return text
        
    try:
        # Decrypt returns bytes, decode to string
        return cipher_suite.decrypt(text.encode()).decode()
    except Exception as e:
        # print(f"Decryption failed for {text[:20]}...: {e}")
        return text

def decrypt_diaries():
    print("Starting decryption of imported diaries...")
    diaries = HaruOn.objects.all()
    count = 0
    updated = 0
    
    for diary in diaries:
        is_changed = False
        
        # 1. Decrypt Content
        original_content = diary.content
        decrypted_content = decrypt_text(original_content)
        if original_content != decrypted_content:
            diary.content = decrypted_content
            is_changed = True
            
        # 2. Decrypt Analysis Result Fields
        if diary.analysis_result and isinstance(diary.analysis_result, dict):
            new_analysis = diary.analysis_result.copy()
            analysis_changed = False
            
            for k, v in new_analysis.items():
                if isinstance(v, str) and v.startswith('gAAAA'):
                    decrypted_v = decrypt_text(v)
                    if v != decrypted_v:
                        new_analysis[k] = decrypted_v
                        analysis_changed = True
            
            if analysis_changed:
                diary.analysis_result = new_analysis
                is_changed = True
        
        if is_changed:
            diary.save()
            updated += 1
            
        count += 1
        if count % 100 == 0:
            print(f"Processed {count} diaries...")
            
    print(f"Decryption finished. Processed {count} diaries, Updated {updated} diaries.")

if __name__ == '__main__':
    decrypt_diaries()
