import csv
import json
import random

# 입력 및 출력 파일 경로
input_csv = 'chatbot_data.csv'
output_train = 'data/train.jsonl'
output_valid = 'data/valid.jsonl'
output_sample = 'data/sample_view.json'

# 시스템 프롬프트 (페르소나 정의)
SYSTEM_PROMPT = "당신은 사용자에게 공감하고 따뜻한 위로를 건네는 AI 심리상담사 '마음온'입니다. 사용자의 이야기에 귀 기울이고, 짧고 기계적인 답변보다는 정서적인 지지를 보내주세요."

def convert_csv_to_jsonl(csv_path):
    data = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 라벨 1(이별/부정)과 0(일상) 위주로 사용. 2(사랑)는 제외하거나 적게 사용.
            # 상담 목적이므로 1번(부정 감정) 데이터를 우선시.
            if row['label'] == '2': 
                continue
                
            question = row['Q']
            answer = row['A']
            
            # 데이터 포맷 (Chat Message 형식)
            entry = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": answer}
                ]
            }
            data.append(entry)
    
    return data

def save_jsonl(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        for entry in data:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

# 1. 데이터 변환
all_data = convert_csv_to_jsonl(input_csv)
print(f"총 데이터 개수: {len(all_data)}개")

# 2. 데이터 셔플 및 분할 (Train 90% / Valid 10%)
random.shuffle(all_data)
split_idx = int(len(all_data) * 0.9)
train_data = all_data[:split_idx]
valid_data = all_data[split_idx:]

# 3. 저장
import os
os.makedirs('data', exist_ok=True)

save_jsonl(train_data, output_train)
save_jsonl(valid_data, output_valid)

# 4. 사용자가 볼 수 있게 샘플 저장
with open(output_sample, 'w', encoding='utf-8') as f:
    json.dump(train_data[:5], f, ensure_ascii=False, indent=2)

print(f"학습 데이터 생성 완료: {output_train} ({len(train_data)}개)")
print(f"검증 데이터 생성 완료: {output_valid} ({len(valid_data)}개)")
