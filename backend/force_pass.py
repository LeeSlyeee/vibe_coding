from app import app, mongo
from bson.objectid import ObjectId
import sys

def force_pass_assessment(username):
    with app.app_context():
        # 1. 닉네임 또는 아이디로 사용자 찾기
        user = mongo.db.users.find_one({'$or': [{'username': username}, {'nickname': username}]})
        
        if not user:
            print(f"❌ User '{username}' not found!")
            return

        print(f"🔍 User Found: {user.get('username')} (ID: {user.get('_id')})")
        print(f"   Current Status: Assessment={user.get('assessment_completed')}, Linked={user.get('linked_center_code')}")

        # 2. 강제 업데이트
        result = mongo.db.users.update_one(
            {'_id': user['_id']},
            {'$set': {
                'assessment_completed': True,
                'risk_level': 1,
                'phq9_score': 0,
                # 만약 연동 코드가 있다면 확실하게 박아주기 (옵션)
                # 'linked_center_code': 'FORCED_BY_ADMIN' 
            }}
        )

        if result.modified_count > 0:
            print(f"✅ Successfully forced assessment PASS for '{username}'.")
        else:
            print(f"⚠️ No changes made (Already passed?).")

if __name__ == "__main__":
    target = "mechinxixi"
    if len(sys.argv) > 1:
        target = sys.argv[1]
    force_pass_assessment(target)
