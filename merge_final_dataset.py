import csv
import json
import random

# 파일 경로 정의
UPGRADED_CSV = 'chatbot_data_upgraded.csv' # LLM 변환 완료된 파일 (Label 1)
ORIGINAL_CSV = 'chatbot_data.csv'          # 원본 파일 (Label 0, 2 활용)
FINAL_TRAIN = 'data/final_train.jsonl'
FINAL_VALID = 'data/final_valid.jsonl'

SYSTEM_PROMPT = "당신은 따뜻하고 전문적인 AI 심리상담사 '마음온'입니다. 사용자의 힘든 감정에 깊이 공감해주고, 다정하고 구체적인 위로의 말을 건네주세요."

def create_final_dataset():
    dataset = []
    
    # 1. 고품질 상담 데이터 (Label 1: 이별/부정 - LLM 변환본) 로드
    # 아직 변환 중일 경우를 대비해 존재하는 만큼만 읽음
    if os.path.exists(UPGRADED_CSV):
        print(f"Loading upgraded data from {UPGRADED_CSV}...")
        with open(UPGRADED_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('A'): # 답변이 있는 경우만
                    dataset.append({
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": row['Q']},
                            {"role": "assistant", "content": row['A']}
                        ]
                    })
    else:
        print("Warning: Upgraded CSV not found yet. (변환 작업 진행 중)")

    print(f"  - 고품질 상담 데이터: {len(dataset)}개 로드됨")

    # 2. 일상 대화 데이터 (Label 0) 추가 - 원본에서 선별
    # 너무 짧은 단답형은 제외하고, 길이가 좀 되는 것 위주로 선별하거나
    # 혹은 데이터 다양성을 위해 일정 비율만 섞음 (예: 2000개)
    count_label_0 = 0
    with open(ORIGINAL_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        label_0_data = []
        for row in reader:
            if row['label'] == '0':
                # 너무 짧은 답변 필터링 (선택 사항)
                if len(row['A']) > 5: 
                    label_0_data.append(row)
    
    # 일상 대화 2000개 랜덤 샘플링 (너무 많으면 상담 성향이 희석될 수 있음)
    random.shuffle(label_0_data)
    selected_label_0 = label_0_data[:2000]
    
    for row in selected_label_0:
        dataset.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": row['Q']},
                {"role": "assistant", "content": row['A']} # 원본 답변 사용 (짧을 수 있음)
            ]
        })
        count_label_0 += 1

    print(f"  - 일상 대화 데이터: {count_label_0}개 추가됨")
    
    # 3. 데이터 셔플 및 분할
    random.shuffle(dataset)
    total_len = len(dataset)
    split_idx = int(total_len * 0.95) # 학습 95%, 검증 5%
    
    train_data = dataset[:split_idx]
    valid_data = dataset[split_idx:]
    
    # 4. 저장
    os.makedirs('data', exist_ok=True)
    
    with open(FINAL_TRAIN, 'w', encoding='utf-8') as f:
        for entry in train_data:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
    with open(FINAL_VALID, 'w', encoding='utf-8') as f:
        for entry in valid_data:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print("="*40)
    print(f"최종 학습 데이터 생성 완료!")
    print(f"Train: {len(train_data)}건 / Valid: {len(valid_data)}건")
    print(f"저장 경로: {FINAL_TRAIN}")
    print("="*40)

import os
if __name__ == "__main__":
    create_final_dataset()
