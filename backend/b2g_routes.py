from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from bson.objectid import ObjectId

b2g_bp = Blueprint('b2g_bp', __name__)

# 우리는 app.py의 mongo 인스턴스를 사용해야 합니다.
# 순환 참조를 피하기 위해 함수 내부에서 import하거나, current_app을 사용합니다.
from flask import current_app
from config import get_korea_time

def get_db():
    # flask_pymongo의 래퍼가 아닌, 직접 db 객체에 접근
    # medication_routes.py와 동일한 패턴 사용
    from app import mongo
    return mongo.db

import requests

# ----------------- 1. Verify Center Code (Proxy Pattern) -----------------
@b2g_bp.route('/centers/verify-code/', methods=['POST'])
@b2g_bp.route('/api/centers/verify-code/', methods=['POST'])
@b2g_bp.route('/api/v1/centers/verify-code/', methods=['POST'])
def verify_code():
    db = get_db()
    data = request.json
    # Frontend sends 'center_code', old logic might send 'code'
    code = (data.get('center_code') or data.get('code', '')).strip().upper()
    
    # Strategy: Local First -> Then Proxy to InsightMind (Port 8000)
    
    # 1. Local Lookup
    center = db.centers.find_one({"code": code})
    
    if center:
        return jsonify({
            "valid": True,
            "center": {
                "name": center.get("name"),
                "region": center.get("region", "Unknown"),
                "id": str(center.get("_id")) 
            },
            "center_id": str(center.get("_id"))
        }), 200
        
    # 2. Proxy Lookup (InsightMind Server)
    try:
        # Assuming InsightMind Django is on 8000 and has the same endpoint structure?
        # Or maybe it has a different endpoint? Usually it's /api/v1/centers/verify-code/
        # Let's try to pass the request.
        print(f"🔄 Proxying verification for {code} to InsightMind(150.230.7.76.nip.io)...")
        res = requests.post("https://150.230.7.76.nip.io/api/v1/centers/verify-code/", json={"code": code}, timeout=3, verify=False)
        
        if res.status_code == 200:
            ext_data = res.json()
            if ext_data.get("valid"):
                # WOW! Found in InsightMind.
                # We must CACHE this center locally so we can link to it in OUR DB.
                # InsightMind response likely has 'center' object.
                ext_center = ext_data.get("center", {})
                
                # Check duplication again just in case
                if not db.centers.find_one({"code": code}):
                    new_center_id = db.centers.insert_one({
                        "code": code,
                        "name": ext_center.get("name", "External Center"),
                        "region": ext_center.get("region", "External"),
                        "external_id": ext_center.get("id"), # Original ID
                        "source": "InsightMind_Proxy",
                        "created_at": get_korea_time()
                    }).inserted_id
                    
                    print(f"✅ Cached External Center: {ext_center.get('name')} -> {new_center_id}")
                    
                    # Return OUR ID
                    return jsonify({
                        "valid": True,
                        "center": {
                            "name": ext_center.get("name", "External Center"),
                            "region": ext_center.get("region", "External"),
                            "id": str(new_center_id)
                        },
                        "center_id": str(new_center_id)
                    }), 200
    except Exception as e:
        print(f"⚠️ Proxy Verification Failed: {e}")
        
    return jsonify({
        "valid": False,
        "message": "유효하지 않은 기관 코드입니다. (Local & Remote)"
    }), 404

# ----------------- 2. Connect User to Center -----------------
@b2g_bp.route('/api/v1/b2g_sync/connect/', methods=['POST'])
@b2g_bp.route('/api/b2g_sync/connect/', methods=['POST'])
@jwt_required()
def connect_center():
    user_id = get_jwt_identity()
    db = get_db()
    data = request.json
    
    center_id_str = data.get('center_id')
    if not center_id_str:
        return jsonify({"message": "Center ID missing"}), 400
        
    try:
        center_obj_id = ObjectId(center_id_str)
    except:
        return jsonify({"message": "Invalid Center ID Format"}), 400

    center = db.centers.find_one({"_id": center_obj_id})
    if not center:
        return jsonify({"message": "Center not found"}), 404
        
    existing = db.b2g_connections.find_one({
        "user_id": user_id,
        "center_id": center_obj_id
    })
    
    if existing:
        db.b2g_connections.update_one(
            {"_id": existing["_id"]},
            {"$set": {"status": "ACTIVE", "updated_at": get_korea_time()}}
        )
    else:
        db.b2g_connections.insert_one({
            "user_id": user_id,
            "center_id": center_obj_id,
            "center_code": center.get("code"),
            "status": "ACTIVE",
            "created_at": get_korea_time()
        })
        
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"linked_center_code": center.get("code")}}
    )
    
    # [Optional] Notify InsightMind? (Maybe user connection event?)
    # For now, local connection is enough for dashboard visibility.
    
    return jsonify({"message": "Connected successfully"}), 200

# ----------------- 3. Sync Data (Data Push) -----------------
@b2g_bp.route('/api/v1/centers/sync-data/', methods=['POST'])
def sync_data():
    db = get_db()
    data = request.json
    
    center_code = data.get('center_code')
    nickname = data.get('user_nickname')
    
    # 1. Local Log & Persistence
    print(f"📥 [B2G Sync] Data received from {nickname} for {center_code}")
    
    try:
        # Save to 'b2g_metrics' collection for Dashboard
        # Upsert based on (user, center) or just Append?
        # Dashboard likely queries time-series.
        
        # We'll save the raw payload with a timestamp
        payload = {
            "center_code": center_code,
            "user_nickname": nickname,
            "metrics": data.get('mood_metrics', []),
            "risk_level": data.get('risk_level', 0),
            "synced_at": get_korea_time()
        }
        
        # Insert (History Log)
        db.b2g_metrics.insert_one(payload)
        
        # Update Latest Status for User/Center Connection
        db.b2g_connections.update_one(
            {"user_nickname": nickname, "center_code": center_code},
            {"$set": {
                "last_sync": get_korea_time(), 
                "last_risk_level": data.get('risk_level', 0),
                "latest_metrics": data.get('mood_metrics', [])[:1] # Keep latest one for quick view
            }},
            upsert=True
        )

        # [CRITICAL UPGRADE] 
        # 150 서버에서 온 데이터를 '통계'뿐만 아니라 실제 '일기(diaries)' 컬렉션에도 저장해야 함.
        # 그래야 사용자가 앱에서 볼 수 있고 AI 분석이 돌아감.
        
        incoming_metrics = data.get('mood_metrics', [])
        if incoming_metrics:
            # 반환값에 처리 결과 포함
            processed_count = 0
            
            # 유저 ID 조회 (Nickname 기반)
            user = db.users.find_one({"username": nickname}) or db.users.find_one({"nickname": nickname})
            
            if not user:
                print(f"⚠️ [B2G Sync] User not found for nickname: {nickname}. Creating new user...")
                try:
                    # [Auto-Create] 없는 유저면 자동 생성하여 데이터 수용
                    new_user = {
                        "username": nickname,
                        "nickname": nickname,
                        "email": f"{nickname}@b2g.auto", # 가상 이메일
                        "password": "auto_generated", # 접속 불가 (비번 모름)
                        "risk_level": data.get('risk_level', 0),
                        "created_at": get_korea_time(),
                        "source": "B2G_Auto_Sync",
                        "linked_center_code": center_code
                    }
                    res = db.users.insert_one(new_user)
                    user_id = str(res.inserted_id)
                    print(f"🆕 [B2G Sync] Auto-created user: {nickname} ({user_id})")
                except Exception as create_err:
                     print(f"❌ [B2G Sync] User Creation Failed: {create_err}")
                     return jsonify({"message": "User not found & Creation failed"}), 500
            else:
                user_id = str(user['_id'])

            # Common Logic for Diary Save
            from app import encrypt_data # Encryption Helper
                
            for item in incoming_metrics:
                # Date Logic
                date_str = item.get('date', '') 
                if not date_str and item.get('created_at'):
                    date_str = item.get('created_at')[:10]
                    
                if not date_str: continue
                
                # Check duplication (Date Scope)
                try:
                    start = datetime.strptime(date_str, "%Y-%m-%d")
                    end = start + timedelta(days=1)
                    
                    exists = db.diaries.find_one({
                        "user_id": user_id,
                        "created_at": {"$gte": start, "$lt": end}
                    })
                    
                    if not exists:
                        # [Fix] Date Parsing Logic (ISO 8601 & Legacy Support)
                        created_at_val = get_korea_time()
                        if item.get('created_at'):
                            c_str = item.get('created_at')
                            try:
                                # 1. Try ISO format (with Z or Offset)
                                if c_str.endswith('Z'):
                                    c_str = c_str.replace('Z', '+00:00')
                                created_at_val = datetime.fromisoformat(c_str)
                            except ValueError:
                                try:
                                    # 2. Try Standard DB format
                                    created_at_val = datetime.strptime(c_str, '%Y-%m-%d %H:%M:%S')
                                except:
                                    # 3. Fallback
                                    pass
                        
                        raw_diary = {
                            'user_id': user_id,
                            'event': item.get('event', ''),
                            'mood_level': item.get('mood_level', 3),
                            'mood_intensity': item.get('mood_intensity', 0),
                            'mode': item.get('mode', 'green'),
                            
                            # Rich Data
                            'weather': item.get('weather'),
                            'sleep_condition': item.get('sleep') or item.get('sleep_condition'),
                            'emotion_desc': item.get('emotion') or item.get('emotion_desc'),
                            'emotion_meaning': item.get('meaning') or item.get('emotion_meaning'),
                            'self_talk': item.get('selftalk') or item.get('self_talk'),
                            'gratitude_note': item.get('gratitude') or item.get('gratitude_note', ''),
                            'medication_taken': item.get('medication_taken', False),
                            'symptoms': item.get('symptoms', []),
                            
                            # AI Data (Preserve from 150 if exists)
                            'ai_prediction': item.get('ai_prediction', '분석 중...'),
                            'ai_comment': item.get('ai_comment', '잠시만 기다려주세요... 🤖'),
                            'ai_analysis': item.get('ai_analysis', ''),
                            
                            'created_at': created_at_val,
                            'sync_source': 'InsightMind_150'
                        }
                        
                        # Encrypt & Insert
                        encrypted = encrypt_data(raw_diary)
                        db.diaries.insert_one(encrypted)
                        processed_count += 1
                        print(f"✅ [B2G Sync] Inserted diary for {nickname} on {date_str}")
                except Exception as parse_err:
                    print(f"⚠️ [B2G Sync] Parse Error for item: {parse_err}")
                    continue

        print(f"✅ [B2G Sync] Data saved to DB for {nickname} details.")
        return jsonify({"message": "Data synced", "success": True}), 200
        
    except Exception as e:
        print(f"❌ [B2G Sync] Save Error: {e}")
        return jsonify({"message": "Save Failed", "error": str(e)}), 500

# ----------------- 4. Check Connection Status (New) -----------------
@b2g_bp.route('/api/b2g_sync/status/', methods=['GET'])
@jwt_required()
def check_status():
    user_id = get_jwt_identity()
    db = get_db()
    
    # Check users collection
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"linked": False, "message": "User not found"}), 404

    code = user.get("linked_center_code")
    
    if code:
        return jsonify({"linked": True, "code": code}), 200
        
    return jsonify({"linked": False}), 200

# ----------------- 5. Server-to-Server Sync (Web -> 150) -----------------
def sync_to_insight_mind(diary_data, user_id):
    """
    Web(217)에서 작성된 일기를 Admin(150) 서버로 전송
    - Fire and Forget 방식 (메인 스레드 차단 방지)
    - 앱(iOS)과 동일한 포맷 유지
    """
    try:
        from app import mongo
        import requests
        import threading
        
        def _bg_task():
            from app import app
            with app.app_context():
                try:
                    # 1. Get User Info
                    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
                    if not user: return
                    
                    center_code = user.get("linked_center_code") or user.get("center_code")
                    if not center_code: 
                        print(f"⏩ [B2G Web] Skipping sync. No center linked for {user.get('username')}")
                        return
                        
                    nickname = user.get('nickname', user.get('username'))
                    
                    # 2. Format Payload (Same as iOS)
                    # diary_data is 'raw_diary' dict
                    
                    # Safe Decrypt (If needed, but usually passed raw before encryption in create_diary)
                    # If passed AFTER encryption, we need to decrypt.
                    
                    # Assuming we pass RAW data here.
                    
                    metrics = [{
                        "created_at": diary_data.get('created_at').strftime('%Y-%m-%d %H:%M:%S') if diary_data.get('created_at') else "",
                        "date": diary_data.get('created_at').strftime('%Y-%m-%d') if diary_data.get('created_at') else "",
                        "mood_level": diary_data.get('mood_level', 3),
                        "score": diary_data.get('mood_level', 3), # Dashboard uses 'score' often
                        
                        # Content
                        "event": diary_data.get('event', ''),
                        "emotion": diary_data.get('emotion_desc', ''),
                        "meaning": diary_data.get('emotion_meaning', ''),
                        "selftalk": diary_data.get('self_talk', ''),
                        "sleep": diary_data.get('sleep_condition', '') or diary_data.get('sleep_desc', ''),
                        
                        # AI Data
                        "ai_comment": diary_data.get('ai_comment', ''),
                        "ai_advice": diary_data.get('ai_advice', ''), # If any
                        "ai_analysis": diary_data.get('ai_analysis', ''), # If any
                        "ai_prediction": diary_data.get('ai_prediction', ''),
                        
                        # Rich Data (New)
                        "weather": diary_data.get('weather', ''),
                        "medication_taken": diary_data.get('medication_taken', False),
                        "symptoms": diary_data.get('symptoms', []),
                        "gratitude": diary_data.get('gratitude_note', '')
                    }]
                    
                    payload = {
                        "center_code": center_code,
                        "user_nickname": nickname,
                        "risk_level": user.get('risk_level', 0),
                        "mood_metrics": metrics
                    }
                    
                    print(f"🚀 [B2G Web] Pushing to InsightMind(150)... User: {nickname}, Code: {center_code}")
                    
                    # 3. Send
                    url = "https://150.230.7.76.nip.io/api/v1/centers/sync-data/"
                    res = requests.post(url, json=payload, timeout=5, verify=False) # Skip SSL verify for nip.io self-signed if needed
                    
                    if res.status_code == 200:
                        print(f"✅ [B2G Web] Sync Success: {res.json()}")
                    else:
                        print(f"⚠️ [B2G Web] Sync Failed ({res.status_code}): {res.text}")
                        
                except Exception as ex:
                    print(f"❌ [B2G Web] Sync Error: {ex}")

        # Run in Thread
        threading.Thread(target=_bg_task).start()
        
    except Exception as e:
        print(f"❌ [B2G Web] Launcher Error: {e}")

def pull_from_insight_mind(user_id, run_async=True):
    """
    Admin(150) -> Web(217) 데이터 동기화
    run_async=False : 로그인 시 확실한 동기화를 위해 동기 실행 권장
    """
    try:
        from app import mongo
        import requests
        import threading
        from app import encrypt_data # Encrypt before save
        
        def _bg_pull_task():
            # [Fix] Import explicit app object for thread context
            # If running sync, we might already have context, but safe to nest
            from app import app
            # Check if we are already in app context
            try:
                # If we are in Sync mode (Main Thread), `app` is available? 
                # Just use app.app_context() always.
                with app.app_context():
                    _core_pull_logic(mongo, user_id, encrypt_data)
            except RuntimeError:
                # Already inside context?
                _core_pull_logic(mongo, user_id, encrypt_data)
        
        def _core_pull_logic(mongo, user_id, encrypt_data):
            try:
                # 1. Get User Info
                user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
                if not user: return
                
                # [Fix] Check both field names
                center_code = user.get("linked_center_code") or user.get("center_code")
                if not center_code: 
                    print(f"⏩ [B2G Web] Pull skipped. No center code linked for {user.get('username')}")
                    return
                
                nickname = user.get('nickname', user.get('username'))
                
                print(f"🚀 [B2G Web] Pulling from InsightMind(150)... User: {nickname}")
                
                # 2. Fetch from 150
                url = "https://150.230.7.76.nip.io/api/v1/centers/sync-data/"
                params = {"center_code": center_code, "user_nickname": nickname}
                
                res = requests.get(url, params=params, timeout=5, verify=False)
                
                if res.status_code == 200:
                    server_items = res.json() # List of dicts
                    print(f"📥 [B2G Web] Fetched {len(server_items)} items from Server.")
                    
                    count = 0
                    for item in server_items:
                        # 3. Check Duplicate (by date & user)
                        date_str = item.get('created_at', '')[:10] # YYYY-MM-DD
                        if not date_str: continue
                        
                        # MongoDB Date Range Check for that day
                        start = datetime.strptime(date_str, "%Y-%m-%d")
                        end = start + timedelta(days=1)
                        
                        exists = mongo.db.diaries.find_one({
                            "user_id": str(user_id),
                            "created_at": {"$gte": start, "$lt": end}
                        })
                        
                        if not exists:
                            # 4. Convert & Save
                            raw_diary = {
                                'user_id': str(user_id),
                                'event': item.get('event', ''),
                                'mood_level': item.get('mood_level', 3),
                                'mood_intensity': 0,
                                'mode': 'green', # Default
                                
                                # Rich Data
                                'weather': item.get('weather'),
                                'sleep_condition': item.get('sleep_condition'),
                                'emotion_desc': item.get('emotion_desc'),
                                'emotion_meaning': item.get('emotion_meaning'),
                                'self_talk': item.get('self_talk'),
                                'medication_taken': item.get('medication_taken', False),
                                'symptoms': item.get('symptoms', []),
                                'gratitude_note': item.get('gratitude_note', ''),
                                
                                # AI
                                'ai_prediction': item.get('ai_prediction', ''),
                                'ai_comment': item.get('ai_comment', ''),
                                'ai_analysis': item.get('ai_analysis', ''),
                                'created_at': datetime.strptime(item.get('created_at'), '%Y-%m-%d %H:%M:%S')
                            }
                            
                            # Encrypt!
                            encrypted = encrypt_data(raw_diary)
                            mongo.db.diaries.insert_one(encrypted)
                            count += 1
                    
                    if count > 0:
                        print(f"✅ [B2G Web] Pulled & Restored {count} missing diaries.")
                    else:
                        print("✨ [B2G Web] All synced. No missing items.")
                        
                else:
                    print(f"⚠️ [B2G Web] Pull Failed ({res.status_code})")
                    
            except Exception as ex:
                print(f"❌ [B2G Web] Pull Logic Error: {ex}")

        if run_async:
            threading.Thread(target=_bg_pull_task).start()
        else:
            print("⚓️ [B2G Sync] Running Synchronously...")
            _bg_pull_task()
        
    except Exception as e:
        print(f"❌ [B2G Web] Launcher Error: {e}")

def recover_center_code(nickname):
    """
    [Self-Healing] 150 서버에 물어봐서 연동된 코드가 있는지 확인
    Return: code string or None
    """
    try:
        import requests
        print(f"🕵️ [B2G Web] Checking link recovery for '{nickname}'...")
        
        url = "https://150.230.7.76.nip.io/api/v1/centers/sync-data/"
        params = {
            "action": "check_link", 
            "user_nickname": nickname
        }
        
        res = requests.get(url, params=params, timeout=3, verify=False)
        if res.status_code == 200:
            data = res.json()
            if data.get('linked') and data.get('center_code'):
                print(f"🚑 [B2G Web] Link Recovered! -> {data.get('center_code')}")
                return data.get('center_code')
                
        return None
    except Exception as e:
        print(f"❌ [B2G Web] Recovery Failed: {e}")
        return None
