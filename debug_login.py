
import requests
from pymongo import MongoClient
import sys

# 색상 코드
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def debug_account(username, password):
    print(f"🔍 Debugging Account: {username}")
    
    # 1. DB 직접 확인
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client['mood_diary_db'] # DB 이름 확인 필요 (기본값 가정)
        
        user = db.users.find_one({"username": username})
        
        if not user:
            print(f"{RED}❌ User '{username}' NOT FOUND in Database!{RESET}")
            # 전체 유저 리스트 출력
            print("\n📋 Existing Users:")
            for u in db.users.find():
                print(f" - {u.get('username')}")
            return
            
        print(f"{GREEN}✅ User '{username}' Found in DB.{RESET}")
        print(f"   - ID: {user['_id']}")
        print(f"   - Hash: {user['password_hash'][:10]}...") 
        
        # 2. 비밀번호 검증 (werkzeug 사용)
        from werkzeug.security import check_password_hash
        is_valid = check_password_hash(user['password_hash'], password)
        
        if is_valid:
            print(f"{GREEN}✅ Password Verification SUCCESS! (Hash Matches){RESET}")
        else:
            print(f"{RED}❌ Password Verification FAILED! (Hash Mismatch){RESET}")
            print(f"   - Input Password: {password}")
            
    except Exception as e:
        print(f"{RED}❌ DB Error: {e}{RESET}")

if __name__ == "__main__":
    debug_account("test", "12qw")
