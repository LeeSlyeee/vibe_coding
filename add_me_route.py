import re

file_path = '/home/ubuntu/project/backend/app.py'

new_route = \"\"\"
@app.route('/api/v1/auth/me', methods=['GET'])
@jwt_required()
def get_my_info():
    try:
        user_id = get_jwt_identity()
        from bson.objectid import ObjectId
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({"msg": "User not found"}), 404
            
        return jsonify({
            "username": user.get('username'),
            "name": user.get('name', ""),
            "nickname": user.get('nickname', "")
        }), 200
    except Exception as e:
        print(f"Error in /auth/me: {e}")
        return jsonify({"msg": str(e)}), 500
\"\"\"

with open(file_path, 'r') as f:
    content = f.read()

# 이미 있는지 확인
if '/api/v1/auth/me' in content:
    print("⚠️ Route already exists.")
else:
    # login 함수 뒤에 추가
    # login 함수가 어디 있는지 찾는다
    idx = content.find('def login():')
    if idx != -1:
        # 함수 끝나는 지점 찾기 어려우니 그냥 파일 끝부분(__name__ 앞)에 넣는다.
        # 아니, import 문제 없으려면 위쪽이 좋은데.
        # 그냥 @app.route('/api/v1/auth/register' 앞에 넣자.
        target = "@app.route('/api/v1/auth/register'"
        replace_with = new_route + "\n\n" + target
        
        if target in content:
            content = content.replace(target, replace_with)
            print("✅ Route inserted before register endpoint.")
        else:
            # 못 찾으면 그냥 맨 뒤 (if __name__...) 앞에
            target = "if __name__ =="
            content = content.replace(target, new_route + "\n" + target)
            print("✅ Route inserted at EOF.")

    with open(file_path, 'w') as f:
        f.write(content)
        print("🚀 app.py patched.")
