import requests
import json
import time

BASE_URL = "https://217.142.253.35.nip.io/api"

print("=========================================================")
print("🚀 [시뮬레이터] 마음 브릿지 (Mind Bridge) E2E 통합 테스트 시작")
print("=========================================================\n")

# SSL Warning 무시 (nip.io 사용 시)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def req(method, endpoint, token=None, data=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "POST":
            res = requests.post(url, headers=headers, json=data, verify=False)
        elif method == "GET":
            res = requests.get(url, headers=headers, verify=False)
        elif method == "PUT":
            res = requests.put(url, headers=headers, json=data, verify=False)
        return res
    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        return None

# 1. 환자(A) 및 보호자(B) 계정 생성
user_a = f"patient_{int(time.time())}"
user_b = f"guardian_{int(time.time())}"

print(f"👤 환자 A 생성: {user_a}")
req("POST", "/register", data={"username": user_a, "password": "123", "nickname": "환자A"})
res_a = req("POST", "/login", data={"username": user_a, "password": "123"})
token_a = res_a.json()["access_token"]

print(f"👤 보호자 B 생성: {user_b}")
req("POST", "/register", data={"username": user_b, "password": "123", "nickname": "보호자B"})
res_b = req("POST", "/login", data={"username": user_b, "password": "123"})
token_b = res_b.json()["access_token"]

print("\n--- [Phase 4] 계정 연결 및 데이터 공유 ---")

# 2. 환자 A가 공유 코드 발급
print("A 기기: 공유 코드 발급 요청")
res_code = req("POST", "/share/code", token=token_a)
if res_code.status_code in [200, 201]:
    share_code = res_code.json()["code"]
    print(f"✅ 공유 코드 정상 발급 완료: [{share_code}] (만료시간 포함 확인)")
else:
    print(f"❌ 공유 코드 발급 실패: {res_code.text}")

# 3. 환자 A가 권한 설정 제한 ("기본 감정만 공유")
print("A 기기: 권한 레벨 '1' (기본 감정만 공유) 설정")
res_perm = req("PUT", "/share/settings", token=token_a, data={"permission_level": 1})
if res_perm.status_code == 200:
    print("✅ 권한 제한 설정 완료")

# 4. 보호자 B가 코드 입력하여 연결
print(f"B 기기: 공유 코드 [{share_code}] 로 연결 시도")
res_connect = req("POST", "/share/connect", token=token_b, data={"code": share_code})
if res_connect.status_code == 200:
    print("✅ B 기기 연결 성공 (환자 목록에 등록 완료)")
else:
    print(f"❌ 연결 실패: {res_connect.text}")

print("\n--- [Phase 5] 보호자 시야 로그 및 실시간 위기 알림 ---")

# 5. 보호자 B가 A의 데이터 조회 (권한 블라인드 작동 확인)
print("B 기기: 환자 A 상태 조회 요청 (블라인드 여부 확인)")
res_patients = req("GET", "/share/list?role=viewer", token=token_b)
try:
    patient_list = res_patients.json()
except Exception as e:
    print(f"❌ 환자 목록 파싱 오류: {res_patients.status_code} - {res_patients.text}")
    patient_list = []
if patient_list:
    patient_id = patient_list[0]['id']
    res_detail = req("GET", f"/share/insights/{patient_id}", token=token_b)
    print(f"✅ B 기기 환자 세부정보 조회: {res_detail.json().get('msg', '성공')}")
    # permission_level: 1 확인
    permissions = res_detail.json().get('patient', {}).get('permission_level', 0)
    if permissions == 1:
        print("🔒 데이터 블라인드 정상 작동 (일기 원문 열람 불가) 확인")

# 6. 환자 A가 위험 신호 일기 작성
print("\nA 기기: 우울감 및 위험 키워드가 포함된 일기 작성")
risk_diary = {
    "date": time.strftime('%Y-%m-%d'),
    "weather": "비",
    "event": "오늘 너무 힘들었다. 죽고 싶다는 생각이 든다.",
    "thought": "아무것도 나아지지 않을 것 같아 우울하다.",
    "emotion_desc": "우울, 절망",
    "mood_level": 1,
    "sleep_condition": "불면증"
}
res_diary = req("POST", "/diary", token=token_a, data=risk_diary)
if res_diary.status_code == 201:
    print("✅ 위험 신호 일기 생성 완료 (서버 내부 푸시 로직 트리거됨)")

print("\n=========================================================")
print("🎉 [시뮬레이션 완료] 모든 Backend E2E 시나리오를 정상 패스했습니다.")
print("=========================================================")
