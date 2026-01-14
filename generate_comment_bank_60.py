
import json
import os
import sys

# Add backend to path to import emotion_codes
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from backend.emotion_codes import EMOTION_CODE_MAP

def generate_bank():
    print("Generating comprehensive Comment Bank for 60 Emotions...")
    
    bank = {"keywords": {}}
    
    # Generic templates based on keyword/label
    for code, label in EMOTION_CODE_MAP.items():
        # E.g. "분노 (노여움/억울)"
        clean_label = label.split('(')[0].strip() # "분노"
        sub_label = label.split('(')[1].strip(')') if '(' in label else label # "노여움/억울"
        
        # Create a default empathetic message
        default_msg = f"'{sub_label}'의 감정을 느끼셨군요. "
        
        if "분노" in clean_label or "짜증" in clean_label or "혐오" in clean_label:
            default_msg += "화가 나는 건 당연한 반응이에요. 속상한 마음이 풀릴 때까지 제가 곁에 있을게요."
        elif "슬픔" in clean_label or "비참" in clean_label or "괴로움" in clean_label:
            default_msg += "많이 힘드셨죠. 토닥토닥, 오늘은 당신의 마음을 따뜻하게 안아주고 싶어요."
        elif "외로움" in clean_label:
            default_msg += "혼자라고 느끼지 마세요. 당신의 이야기에 귀 기울이는 제가 있잖아요."
        elif "무기력" in clean_label:
            default_msg += "손 하나 까딱하기 싫은 날이죠. 그럴 땐 아무것도 안 해도 괜찮아요. 충전의 시간이니까요."
        elif "불안" in clean_label or "걱정" in clean_label or "당황" in clean_label:
            default_msg += "마음이 조마조마하시겠어요. 천천히 심호흡 해보세요. 다 잘 될 거예요."
        elif "기쁨" in clean_label or "만족" in clean_label or "신남" in clean_label:
            default_msg += "와, 정말 기쁜 소식이네요! 저까지 행복해지는 기분이에요. 이 순간을 즐기세요!"
        elif "감사" in clean_label or "편안" in clean_label:
            default_msg += "평온한 마음이 느껴져서 참 좋네요. 오늘 밤은 푹 주무실 수 있을 거예요."
        else:
            default_msg += "당신의 감정을 솔직하게 마주한 모습이 용기 있어요. 항상 응원할게요."
            
        entry = {
            "default": default_msg,
            "emotion_keywords": [sub_label] # Use the sub-label as a keyword trigger too
        }
        
        # Use E-Code as key to ensure 1:1 mapping in code logic?
        # NO, ai_analysis.py logic uses 'keywords' loop. 
        # BUT for the 'keyword_comment' logic to work with 60 classes, we might want to map 
        # specific keywords (like "betrayal") to these buckets.
        # For now, let's use the code-mapped labels as keys.
        bank["keywords"][label] = entry

    # Path
    bank_path = os.path.join(os.getcwd(), 'backend', 'data', 'comment_bank_60.json')
    
    with open(bank_path, 'w', encoding='utf-8') as f:
        json.dump(bank, f, ensure_ascii=False, indent=2)
        
    print(f"Saved {len(bank['keywords'])} entries to {bank_path}")

if __name__ == '__main__':
    generate_bank()
