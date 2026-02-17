import os
import sys
import django

# Setup Django Environment
sys.path.append('/home/ubuntu/project/temp_insight_deploy/backend')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from haru_on.models import HaruOn
from analysis_worker import start_analysis_thread, generate_ai_analysis, crypto

def fix_all_scores():
    print("🚀 [Remote Fix] Starting Score Re-calculation...")
    
    # 1. Find diaries with 0 score or no analysis
    # HaruOn model fields: mood_score (int)
    targets = HaruOn.objects.filter(mood_score__lte=0) | HaruOn.objects.filter(mood_score__isnull=True)
    
    # Also check if analysis_result is empty but content exists
    # targets2 = HaruOn.objects.exclude(content="").filter(analysis_result__isnull=True)
    
    # Combine (Using list to avoid distinct issues if any)
    diaries = list(targets)
    print(f"🔍 Found {len(diaries)} diaries with 0 or NULL score.")
    
    for d in diaries:
        print(f"🧵 Processing Diary ID {d.id} ({d.created_at})...")
        
        ar = d.analysis_result or {}
        
        # Prepare text for AI
        content = d.content
        sleep = ar.get('sleep') or ar.get('sleep_condition') or ""
        emotion = ar.get('emotion') or ar.get('emotion_desc') or ""
        meaning = ar.get('meaning') or ar.get('emotion_meaning') or ""
        talk = ar.get('selftalk') or ar.get('self_talk') or ""
        
        full_text = f"날짜: {d.created_at}\n수면: {sleep}\n사건: {content}\n감정: {emotion}\n의미: {meaning}\n스스로에게: {talk}"
        
        try:
            # Call AI directly (sync) to update now
            comment, emotion_word, score = generate_ai_analysis(full_text)
            
            # Update Score
            try:
                s = int(score)
                s = max(1, min(10, s))
            except:
                s = 5
                
            d.mood_score = s
            
            # Update Analysis Result JSON if empty
            if not d.analysis_result:
                d.analysis_result = {
                    "ai_comment": comment,
                    "ai_emotion": emotion_word,
                    "score": s
                }
            else:
                d.analysis_result['score'] = s
                # d.analysis_result['ai_comment'] = comment # Maybe preserve existing?
            
            d.save()
            print(f"✅ Updated Diary {d.id} -> Score: {s}")
            
        except Exception as e:
            print(f"❌ Analysis Failed for Diary {d.id}: {e}")

if __name__ == "__main__":
    fix_all_scores()
