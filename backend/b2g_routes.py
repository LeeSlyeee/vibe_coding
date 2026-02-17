from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from models import db, User, Center

b2g_bp = Blueprint('b2g_bp', __name__)

# [REMOVED] get_db() -> No Mongo

# ----------------- 1. Verify Center Code (PG-Based) -----------------
@b2g_bp.route('/centers/verify-code/', methods=['POST'])
@b2g_bp.route('/api/centers/verify-code/', methods=['POST'])
@b2g_bp.route('/api/v1/centers/verify-code/', methods=['POST'])
def verify_code():
    data = request.json
    code = (data.get('center_code') or data.get('code', '')).strip().upper()
    
    # 1. Local Lookup (Postgres)
    center = Center.query.filter_by(code=code).first()
    
    if center:
        return jsonify({
            "valid": True,
            "center": {
                "name": center.name,
                "region": center.region,
                "id": str(center.id)
            },
            "center_id": str(center.id),
            "user": {} 
        }), 200
        
    # 2. Proxy Lookup (Local Dashboard - Django 8000)
    try:
        print(f"🔄 Proxying verification for {code} to Local Dashboard(8000)...")
        res = requests.post("http://127.0.0.1:8000/api/v1/centers/verify-code/", json={"code": code}, timeout=3)
        
        if res.status_code == 200:
            ext_data = res.json()
            if ext_data.get("valid"):
                ext_center = ext_data.get("center", {})
                
                # Check duplication
                if not Center.query.filter_by(code=code).first():
                    new_center = Center(
                        code=code,
                        name=ext_center.get("name", "External Center"),
                        region=ext_center.get("region", "External"),
                        # external_id ...
                    )
                    db.session.add(new_center)
                    db.session.commit()
                    center = new_center
                
                return jsonify({
                    "valid": True,
                    "center": {
                        "name": ext_center.get("name", "External Center"),
                        "region": ext_center.get("region", "External"),
                        "id": str(center.id) if center else "0"
                    },
                    "center_id": str(center.id) if center else "0"
                }), 200
    except Exception as e:
        print(f"⚠️ Proxy Verification Failed: {e}")
        
    return jsonify({
        "valid": False,
        "message": "유효하지 않은 기관 코드입니다."
    }), 404

# ----------------- 2. Connect User to Center -----------------
@b2g_bp.route('/api/v1/b2g_sync/connect/', methods=['POST'])
@b2g_bp.route('/api/b2g_sync/connect/', methods=['POST'])
@jwt_required()
def connect_center():
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.json
    center_id = data.get('center_id')
    
    if not center_id:
        return jsonify({"message": "Center ID missing"}), 400
        
    center = None
    if str(center_id).isdigit():
        center = Center.query.get(int(center_id))
    
    if not center:
        # Try finding by code directly if ID fails or is not int
        center = Center.query.filter_by(code=str(center_id)).first()

    if not center:
        return jsonify({"message": "Center not found"}), 404
        
    # Update User
    user.center_code = center.code
    db.session.commit()
    
    return jsonify({"message": "Connected successfully", "center_code": center.code}), 200

# ----------------- 3. Check Connection Status -----------------
@b2g_bp.route('/api/b2g_sync/status/', methods=['GET'])
@jwt_required()
def check_status():
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()
    
    if not user:
        return jsonify({"linked": False, "message": "User not found"}), 404

    if user.center_code:
        return jsonify({"linked": True, "code": user.center_code}), 200
        
    return jsonify({"linked": False}), 200

# [Stubbed Sync Helpers]
def sync_to_insight_mind(diary_data, user_id):
    """
    Web(217) -> Admin(Local 8000) Sync
    Uses PostgreSQL Data
    """
    try:
        import threading
        
        def _bg_task():
            # Create a new app context since we are in a thread
            from app import app
            with app.app_context():
                try:
                    # 1. Get User Info (Postgres)
                    # user_id passed might be int or str. PG ID is int.
                    if isinstance(user_id, str) and not user_id.isdigit():
                         # Maybe username?
                         user = User.query.filter_by(username=user_id).first()
                    else:
                         user = User.query.get(int(user_id))
                         
                    if not user: return
                    
                    center_code = user.center_code
                    if not center_code: 
                        print(f"⏩ [B2G Local] Skipping sync. No center linked for {user.username}")
                        return
                        
                    nickname = user.nickname or user.username
                    
                    # 2. Format Payload
                    # diary_data should be DECRYPTED dictionary (from serialize_diary)
                    
                    metrics = [{
                        "created_at": diary_data.get('created_at', ''),
                        "date": diary_data.get('date', ''),
                        "mood_level": diary_data.get('mood_level', 3),
                        
                        # Content
                        "event": diary_data.get('event', ''),
                        "emotion": diary_data.get('emotion_desc', ''),
                        "meaning": diary_data.get('emotion_meaning', ''),
                        "selftalk": diary_data.get('self_talk', ''),
                        "sleep": diary_data.get('sleep_condition', ''),
                        "gratitude": diary_data.get('gratitude_note', ''),
                        
                        # AI Data
                        "ai_comment": diary_data.get('ai_comment', ''),
                        "ai_prediction": diary_data.get('ai_emotion', ''),
                        
                        # Rich Data
                        "weather": diary_data.get('weather', ''),
                        "mode": diary_data.get('mode', 'green'),
                        "mood_intensity": diary_data.get('mood_intensity', 0)
                    }]
                    
                    payload = {
                        "center_code": center_code,
                        "user_nickname": nickname,
                        "risk_level": 0,
                        "mood_metrics": metrics
                    }
                    
                    # 3. Send to Local Dashboard (Django on Port 8000)
                    url = "http://127.0.0.1:8000/api/v1/centers/sync-data/"
                    print(f"🚀 [B2G Local] Pushing to Dashboard(8000)... User: {nickname}, Code: {center_code}")
                    
                    res = requests.post(url, json=payload, timeout=5) # No SSL verify needed for localhost
                    
                    if res.status_code == 200:
                        print(f"✅ [B2G Local] Sync Success: {res.json()}")
                    else:
                        print(f"⚠️ [B2G Local] Sync Failed ({res.status_code}): {res.text}")
                        
                except Exception as ex:
                    print(f"❌ [B2G Local] Sync Error inside thread: {ex}")

        # Run in Thread
        threading.Thread(target=_bg_task).start()
        
    except Exception as e:
        print(f"❌ [B2G Local] Launcher Error: {e}")

def pull_from_insight_mind(user_id, run_async=True):
    """
    [DEPRECATED] 150 Server Pull Removed per User Request.
    """
    pass

def recover_center_code(nickname):
    return None

def migrate_personal_diaries(user_id, username, password):
    pass
