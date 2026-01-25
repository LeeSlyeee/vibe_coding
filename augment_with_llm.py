import csv
import time
import os
# pip install openai 필요 (사용자가 직접 설치해야 함)
try:
    from openai import OpenAI
except ImportError:
    print("OpenAI 패키지가 설치되지 않았습니다. 'pip install openai'를 실행해주세요.")
    exit()

# ==========================================
# [설정] 여기에 API 키를 입력하거나 환경변수로 설정하세요.
api_key = os.environ.get("OPENAI_API_KEY")
# ==========================================
client = OpenAI(
    api_key=api_key,
)

INPUT_CSV = 'chatbot_data.csv'
OUTPUT_CSV = 'chatbot_data_upgraded.csv'

SYSTEM_PROMPT = """
당신은 따뜻하고 전문적인 심리상담사 '마음온'입니다.
주어진 내담자의 고민(Question)에 대해 기존 답변(Legacy Answer)을 참고하되,
훨씬 더 공감하고 정서적인 위로가 담긴 3문장 이상의 답변으로 다시 작성해주세요.
- 말투: 부드럽고 정중한 "해요"체
- 내용: 내담자의 감정을 먼저 읽어주고(공감), 상황을 재해석해주거나 위로를 건네세요.
"""

def upgrade_answer(question, legacy_answer):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # 가성비 좋은 모델 사용
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"내담자 고민: {question}\n기존 답변: {legacy_answer}\n\n새로운 답변:"}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error: {e}")
        return legacy_answer # 에러 시 기존 답변 유지

def main():
    # 진행 상황 파악을 위해 라인 수 계산
    total_lines = sum(1 for _ in open(INPUT_CSV, 'r', encoding='utf-8'))
    
    with open(INPUT_CSV, 'r', encoding='utf-8') as f_read, \
         open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f_write:
        
        reader = csv.DictReader(f_read)
        writer = csv.writer(f_write)
        
        # 헤더 작성
        writer.writerow(['Q', 'A', 'label', 'Original_A'])
        
        count = 0
        for row in reader:
            # 비용 절약을 위해 일단 'Label 1' (부정 감정, 이별 등)만 변환 추천
            if row['label'] == '1':
                new_answer = upgrade_answer(row['Q'], row['A'])
                writer.writerow([row['Q'], new_answer, row['label'], row['A']])
                print(f"[{count}/{total_lines}] 변환 완료: {row['Q'][:10]}...")
                # Rate Limit 방지를 위한 대기 (필요 시 조절)
                time.sleep(0.1)
            else:
                # 라벨 0, 2는 그대로 복사하거나 필요 시 변환
                writer.writerow([row['Q'], row['A'], row['label'], row['A']])
            
            count += 1
            
            # 테스트용: 주석 해제 시 5개만 하고 멈춤
            # if count >= 5: break

    print(f"완료! 저장된 파일: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
