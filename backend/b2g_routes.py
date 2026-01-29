from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from bson.objectid import ObjectId

b2g_bp = Blueprint('b2g_bp', __name__)

# 우리는 app.py의 mongo 인스턴스를 사용해야 합니다.
# 순환 참조를 피하기 위해 함수 내부에서 import하거나, current_app을 사용합니다.
from flask import current_app

def get_db():
    # flask_pymongo의 래퍼가 아닌, 직접 db 객체에 접근
    # medication_routes.py와 동일한 패턴 사용
    from app import mongo
    return mongo.db

import requests

# ----------------- 1. Verify Center Code (Proxy Pattern) -----------------
@b2g_bp.route('/api/v1/centers/verify-code/', methods=['POST'])
def verify_code():
    db = get_db()
    data = request.json
    code = data.get('code', '').strip().upper()
    
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
        print(f"🔄 Proxying verification for {code} to InsightMind(8000)...")
        res = requests.post("http://192.168.0.22:8000/api/v1/centers/verify-code/", json={"code": code}, timeout=3)
        
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
                        "created_at": datetime.utcnow()
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
            {"$set": {"status": "ACTIVE", "updated_at": datetime.utcnow()}}
        )
    else:
        db.b2g_connections.insert_one({
            "user_id": user_id,
            "center_id": center_obj_id,
            "center_code": center.get("code"),
            "status": "ACTIVE",
            "created_at": datetime.utcnow()
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
    
    # 1. Local Log
    print(f"📥 [B2G Sync] Data received from {nickname} for {center_code}")
    
    # 2. Forward to InsightMind (8000)
    # This ensures the 'Real' B2G dashboard at 8000 gets the data too.
    try:
        print(f"📤 Forwarding data to InsightMind(8000)...")
        requests.post("http://192.168.0.22:8000/api/v1/centers/sync-data/", json=data, timeout=2)
    except Exception as e:
        print(f"⚠️ Forwarding Failed: {e}") 
    
    return jsonify({"message": "Data synced"}), 200
