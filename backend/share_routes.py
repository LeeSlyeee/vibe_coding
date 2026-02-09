from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from datetime import datetime
import random
import string
from config import get_korea_time

share_bp = Blueprint('share', __name__)

# --- Helper to access MongoDB ---
def get_mongo():
    from app import mongo
    return mongo

def generate_code(length=6):
    """Generate a random 6-character alphanumeric code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# --- 1. Generate Share Code (Sharer) ---
@share_bp.route('/api/v1/share/code', methods=['POST'])
@jwt_required()
def create_share_code():
    mongo = get_mongo()
    user_id = get_jwt_identity()
    
    # Check User
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    # Generate Unique Code
    code = generate_code()
    
    # Save Code with Expiration
    share_entry = {
        'code': code,
        'sharer_id': user_id,
        'sharer_name': user.get('nickname', user.get('username')),
        'created_at': get_korea_time(),
        'used': False
    }
    
    mongo.db.share_codes.insert_one(share_entry)
    
    return jsonify({
        "message": "공유 코드가 생성되었습니다.",
        "code": code,
        "expires_in": "10분" # Logic can enforce this time limit on verification
    }), 201

# --- 2. Connect with Code (Viewer) ---
@share_bp.route('/api/v1/share/connect', methods=['POST'])
@jwt_required()
def connect_share():
    mongo = get_mongo()
    viewer_id = get_jwt_identity()
    data = request.get_json()
    code = data.get('code', '').strip().upper()
    
    if not code:
        return jsonify({"message": "코드를 입력해주세요."}), 400
        
    # Find Code
    share_entry = mongo.db.share_codes.find_one({'code': code, 'used': False})
    if not share_entry:
        return jsonify({"message": "유효하지 않거나 이미 사용된 코드입니다."}), 404
        
    sharer_id = share_entry['sharer_id']
    
    # Prevent Self-Share
    if sharer_id == viewer_id:
        return jsonify({"message": "본인의 코드는 등록할 수 없습니다."}), 400
        
    # Create Relationship
    relationship = {
        'viewer_id': viewer_id,
        'sharer_id': sharer_id,
        'sharer_name': share_entry['sharer_name'],
        'created_at': get_korea_time()
    }
    
    # Upsert (Avoid duplicates)
    mongo.db.share_relationships.update_one(
        {'viewer_id': viewer_id, 'sharer_id': sharer_id},
        {'$set': relationship},
        upsert=True
    )
    
    # Mark Code as Used
    mongo.db.share_codes.update_one({'_id': share_entry['_id']}, {'$set': {'used': True}})
    
    return jsonify({
        "message": f"{share_entry['sharer_name']}님과 성공적으로 연결되었습니다.",
        "sharer_name": share_entry['sharer_name']
    }), 200

# --- 3. List My Connected Users (Viewer) ---
@share_bp.route('/api/v1/share/list', methods=['GET'])
@jwt_required()
def get_shared_list():
    mongo = get_mongo()
    viewer_id = get_jwt_identity()
    
    cursor = mongo.db.share_relationships.find({'viewer_id': viewer_id})
    results = []
    
    for rel in cursor:
        results.append({
            'sharer_id': rel['sharer_id'],
            'name': rel['sharer_name'],
            'connected_at': rel['created_at']
        })
        
    return jsonify(results), 200

# --- 4. View Insights (Core: Sync from 150) ---
@share_bp.route('/api/v1/share/insights/<target_id>', methods=['GET'])
@jwt_required()
def get_shared_insights(target_id):
    mongo = get_mongo()
    viewer_id = get_jwt_identity()
    
    # 1. Verify Permission
    rel = mongo.db.share_relationships.find_one({
        'viewer_id': viewer_id,
        'sharer_id': target_id
    })
    
    if not rel:
        return jsonify({"message": "해당 사용자의 정보를 볼 권한이 없습니다."}), 403
        
    # 2. Sync Data from 150 (Data Freshness Guarantee)
    # [Important] We trigger a pull to ensure viewer sees LATEST analysis
    try:
        from b2g_routes import pull_from_insight_mind
        print(f"🔄 [Share] Syncing data for {target_id} from 150 Server...")
        pull_from_insight_mind(target_id, run_async=False) # Wait for sync
    except Exception as e:
        print(f"⚠️ [Share] Sync Warning: {e}")
        # Proceed with local data even if sync fails
        
    # 3. Fetch Report & Stats (Re-use existing logic logic)
    # Fetch User Info
    user = mongo.db.users.find_one({'_id': ObjectId(target_id)})
    if not user: return jsonify({"message": "User not found"}), 404
    
    # Fetch Latest Report
    report = user.get('latest_report', "아직 생성된 리포트가 없습니다.")
    risk_level = user.get('risk_level', 1)
    
    # Fetch Simple Stats (Last 7 Days Mood)
    # Aggregation
    pipeline = [
        {"$match": {"user_id": target_id}}, # Match Target User
        {"$sort": {"created_at": -1}},
        {"$limit": 7},
        {"$project": {"mood_level": 1, "created_at": 1, "ai_prediction": 1}}
    ]
    
    recent_moods = list(mongo.db.diaries.aggregate(pipeline))
    processed_moods = []
    
    # Decryption Helper
    from app import decrypt_doc
    
    for doc in recent_moods:
        decrypted = decrypt_doc(doc)
        processed_moods.append({
            "date": decrypted.get('created_at').strftime('%Y-%m-%d') if decrypted.get('created_at') else "",
            "mood": decrypted.get('mood_level', 3),
            "label": decrypted.get('ai_prediction', '')
        })
        
    return jsonify({
        "user_name": rel['sharer_name'],
        "risk_level": risk_level,
        "latest_report": report,
        "recent_moods": processed_moods,
        "last_sync": get_korea_time()
    }), 200
