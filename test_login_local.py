
import requests
import json

# 테스트할 계정 정보 (기존에 사용하시던 계정이 있다면 수정해주세요, 없다면 가상의 정보로 테스트)
# 만약 계정을 모르신다면, 회원가입부터 시도해야 할 수도 있습니다.
# 여기서는 가장 일반적인 테스트 계정으로 시도하거나, 
# 사용자가 제공하지 않았으므로 DB에서 사용자를 찾아보는 로직을 추가합니다.

def test_login_local():
    base_url = "http://127.0.0.1:5001/api"
    
    # 1. DB에서 사용자 한 명 찾기 (pymongo 직접 연결)
    try:
        from pymongo import MongoClient
        from config import Config
        # Config 가져오기 (파일 경로에 따라 조정 필요할 수 있음)
        # 여기서는 하드코딩된 로컬 접속 시도
        client = MongoClient("mongodb://localhost:27017/")
        db = client['mood_diary_db'] # DB 이름 확인 필요
        
        user = db.users.find_one()
        if not user:
            print("❌ DB에 사용자가 한 명도 없습니다. 회원가입이 필요합니다.")
            return

        print(f"👤 Found User in DB: {user.get('username')}")
        
        # 비밀번호는 해시되어 있어서 알 수 없음. 
        # 이 테스트는 '서버가 요청을 받는지' 확인하는 용도 + '알고 있는 계정' 테스트용.
        # 사용자가 "로그인을 했는데" 라고 했으므로, 본인의 아이디/비번을 입력했을 것임.
        # 여기서는 임의의 잘못된 비번으로라도 요청을 보내서 401이 뜨는지(서버 도달), 404/500이 뜨는지 확인.
        
        test_username = user.get('username')
        test_password = "wrong_password_test" # 일부러 틀린 비번
        
        payload = {"username": test_username, "password": test_password}
        
        print(f"🚀 Sending Login Request for {test_username}...")
        response = requests.post(f"{base_url}/login", json=payload)
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 401:
            print("✅ 서버가 정상적으로 동작 중입니다 (401 Unauthorized 반환됨).")
            print("   => 즉, '아이디가 없거나 비밀번호가 틀린' 경우입니다.")
        elif response.status_code == 200:
            print("✅ 로그인 성공 (어라? 비밀번호가 우연히 맞았거나 테스트 계정임)")
        else:
            print(f"⚠️ 예상치 못한 응답 코드: {response.status_code}")

    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_login_local()
