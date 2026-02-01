import re

file_path = '/home/ubuntu/project/backend/standalone_ai_chat.py'

new_prompt = \"\"\"
[시스템 프롬프트 업데이트: 일기장 인터뷰 모드]
당신은 사용자의 하루를 회고하고 마음을 치유하는 전문 심리상담 AI '마음 톡'입니다.
목표: 사용자가 대화를 통해 자연스럽게 '일기(Diary)'를 완성할 수 있도록 유도하세요.

[핵심 전략: 일기장 인터뷰]
1. **사건 파악**: 사용자가 오늘 겪은 일을 육하원칙(언제, 어디서, 누구와, 무엇을)에 따라 구체적으로 말하게 하세요.
2. **감정 심화**: 그 사건에서 어떤 '감정'을 느꼈는지 콕 집어 물어보세요. (예: "그때 억울하셨나요, 아니면 오히려 홀가분하셨나요?")
3. **생각 정리**: 그 감정의 원인이 무엇인지 깊이 생각해보게 하세요. (예: "왜 그런 기분이 들었을까요?")
4. **마무리 조언**: 대화가 무르익으면 따뜻한 위로와 심리학적 조언을 건네세요.

[대화 톤]
- 다정하고 예의 바른 '해요체'를 사용하세요.
- 질문은 한 번에 하나씩만 하세요. (취조하듯 묻지 마세요)
- 사용자의 말에 충분히 공감한 뒤에 질문하세요. (공감 70%, 질문 30%)
\"\"\"

with open(file_path, 'r') as f:
    content = f.read()

# 복잡한 정규식보다는 'system_prompt = \"\"\"' 부분을 찾아서 그 다음 \"\"\"까지 교체
# 하지만 기존 파일 내용이 정확하지 않으므로, 그냥 'system_prompt = .*' 부분을 통째로 안전하게 교체하는 방식을 쓴다.

# 간단하게: 'system_prompt = """' 부터 그 다음 '"""' 까지를 찾아서 교체
start_marker = 'system_prompt = \"\"\"'
end_marker = '\"\"\"'

# 찾기
start_idx = content.find(start_marker)
if start_idx != -1:
    next_quote_idx = content.find(end_marker, start_idx + len(start_marker))
    if next_quote_idx != -1:
        # 기존 내용 잘라내기
        original_prompt_end = next_quote_idx + len(end_marker)
        
        # 새 내용 삽입
        new_content = content[:start_idx] + 'system_prompt = \"\"\"' + new_prompt + content[original_prompt_end:] # end_marker included twice? No.
        # Wait, simple string replacement is safer.
        pass

# 더 쉬운 방법: 그냥 파일 전체를 다시 쓴다. (코드가 짧으니까)
# 하지만 기존 import나 함수 구조를 유지해야 하므로 위험함.

# 정규식으로 교체 시도
content = re.sub(r'system_prompt = \"\"\"[\s\S]*?\"\"\"', 'system_prompt = \"\"\"' + new_prompt + '\"\"\"', content)

with open(file_path, 'w') as f:
    f.write(content)

print("🚀 Prompt updated successfully.")
