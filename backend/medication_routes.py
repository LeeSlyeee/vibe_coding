from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
from config import get_korea_time
import threading

med_bp = Blueprint('medication', __name__)

print("🔹 [DEBUG] Medication Blueprint Module Loaded!") 

# --- Helper to access MongoDB ---
def get_mongo():
    from app import mongo
    return mongo

@med_bp.route('/api/user/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    mongo = get_mongo()
    user_id = get_jwt_identity()
    
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)}, {'password_hash': 0})
    if not user:
        return jsonify({"message": "User not found"}), 404
        
    user['_id'] = str(user['_id'])
    
    # Ensure default values
    if 'risk_level' not in user:
        user['risk_level'] = None # Not assessed yet
        
    return jsonify(user), 200

# --- 1. Medication Management ---

@med_bp.route('/api/medications', methods=['POST'])
@jwt_required()
def add_medication():
    mongo = get_mongo()
    user_id = get_jwt_identity()
    
    # 0. Check User Permission (RBAC)
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({"message": "User not found"}), 404
        
    current_risk = user.get('risk_level', 1)
    # 경증(1, 2)인 경우 접근 제한
    if current_risk < 3:
        return jsonify({"message": "보건소 및 병원 사용자 또는 유료사용자 기능입니다."}), 403

    data = request.get_json()
    
    # Validation
    if not data.get('name'):
        return jsonify({"message": "약 이름을 입력해주세요."}), 400
        
    medication = {
        'user_id': user_id,
        'name': data.get('name'),
        'dosage': data.get('dosage', ''),
        'frequency': data.get('frequency', []), # e.g. ['morning', 'night']
        'alarm_time': data.get('alarm_time', {}), # {'morning': '08:00', ...}
        'memo': data.get('memo', ''),
        'color': data.get('color', '#FF5733'), # For UI visualization
        'created_at': get_korea_time(),
        'is_active': True
    }
    
    result = mongo.db.medications.insert_one(medication)
    medication['_id'] = str(result.inserted_id)
    
    return jsonify({"message": "약물이 등록되었습니다.", "medication": medication}), 201

@med_bp.route('/api/medications', methods=['GET'])
@jwt_required()
def get_medications():
    mongo = get_mongo()
    user_id = get_jwt_identity()
    
    # Check Permission
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user: return jsonify({"message": "User not found"}), 404
    if user.get('risk_level', 1) < 3:
        return jsonify({"message": "보건소 및 병원 사용자 또는 유료사용자 기능입니다."}), 403
    
    # Get only active medications
    cursor = mongo.db.medications.find({'user_id': user_id, 'is_active': True})
    meds = []
    for doc in cursor:
        doc['_id'] = str(doc['_id'])
        meds.append(doc)
        
    return jsonify(meds), 200

@med_bp.route('/api/medications/<med_id>', methods=['DELETE'])
@jwt_required()
def delete_medication(med_id):
    mongo = get_mongo()
    user_id = get_jwt_identity()
    
    # Check Permission
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user: return jsonify({"message": "User not found"}), 404
    if user.get('risk_level', 1) < 3:
        return jsonify({"message": "보건소 및 병원 사용자 또는 유료사용자 기능입니다."}), 403
    
    # Soft delete
    mongo.db.medications.update_one(
        {'_id': ObjectId(med_id), 'user_id': user_id},
        {'$set': {'is_active': False}}
    )
    
    return jsonify({"message": "약물이 삭제되었습니다."}), 200

# --- 2. Medication Logs (Check-in) ---

@med_bp.route('/api/medications/log', methods=['POST'])
@jwt_required()
def log_medication():
    mongo = get_mongo()
    user_id = get_jwt_identity()
    
    # Check Permission
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user: return jsonify({"message": "User not found"}), 404
    if user.get('risk_level', 1) < 3:
        return jsonify({"message": "보건소 및 병원 사용자 또는 유료사용자 기능입니다."}), 403

    data = request.get_json()
    
    med_id = data.get('med_id')
    slot = data.get('slot') # 'morning', 'lunch', 'dinner', 'bedtime'
    date_str = data.get('date') # 'YYYY-MM-DD'
    status = data.get('status', 'taken') # 'taken', 'skipped'
    
    if not all([med_id, slot, date_str]):
        return jsonify({"message": "필수 정보가 누락되었습니다."}), 400
        
    # Check if duplicate
    existing = mongo.db.medication_logs.find_one({
        'user_id': user_id,
        'med_id': med_id,
        'date': date_str,
        'slot': slot
    })
    
    if existing:
        # Update existing
        mongo.db.medication_logs.update_one(
            {'_id': existing['_id']},
            {'$set': {'status': status, 'updated_at': get_korea_time()}}
        )
    else:
        # Create new log
        log_entry = {
            'user_id': user_id,
            'med_id': med_id,
            'date': date_str,
            'slot': slot,
            'status': status,
            'taken_at': get_korea_time(),
            'created_at': get_korea_time()
        }
        mongo.db.medication_logs.insert_one(log_entry)
        
    return jsonify({"message": "복용 기록이 저장되었습니다."}), 200

@med_bp.route('/api/medications/logs', methods=['GET'])
@jwt_required()
def get_medication_logs():
    mongo = get_mongo()
    user_id = get_jwt_identity()
    
    # Check Permission
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user: return jsonify({"message": "User not found"}), 404
    if user.get('risk_level', 1) < 3:
        return jsonify({"message": "보건소 및 병원 사용자 또는 유료사용자 기능입니다."}), 403

    date_str = request.args.get('date') # Optional filter
    
    query = {'user_id': user_id}
    if date_str:
        query['date'] = date_str
        
    cursor = mongo.db.medication_logs.find(query).sort('date', -1)
    logs = []
    for doc in cursor:
        doc['_id'] = str(doc['_id'])
        logs.append(doc)
        
    return jsonify(logs), 200

# --- 3. Symptom Assessment & Triage ---

@med_bp.route('/api/assessment', methods=['POST'])
@jwt_required()
def submit_assessment():
    mongo = get_mongo()
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # data structure: {'type': 'PHQ-9', 'score': 15, 'answers': [...]}
    type = data.get('type', 'General')
    score = data.get('score', 0)
    
    # Determine Risk Level
    risk_level = 'mild'
    if type == 'PHQ-9':
        if score >= 20: risk_level = 'high_risk'
        elif score >= 10: risk_level = 'severe'
        else: risk_level = 'mild'
    
    # Save Assessment
    assessment = {
        'user_id': user_id,
        'type': type,
        'score': score,
        'risk_level': risk_level,
        'answers': data.get('answers', []),
        'created_at': get_korea_time()
    }
    mongo.db.assessments.insert_one(assessment)
    
    # Update User Profile with Risk Level
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {
            'risk_level': risk_level,
            'last_assessment_date': get_korea_time(),
            'care_plan': _generate_care_plan(risk_level)
        }}
    )
    
    return jsonify({
        "message": "진단이 완료되었습니다.",
        "risk_level": risk_level,
        "care_plan": _generate_care_plan(risk_level)
    }), 200

def _generate_care_plan(risk_level):
    if risk_level == 'high_risk':
        return "즉각적인 전문가 상담 필요 / 24시간 모니터링"
    elif risk_level == 'severe':
        return "주 3회 이상 감정 기록 / 약물 복용 철저 관리"
    else:
        return "하루 1회 감정 일기 작성 / 규칙적인 운동 권장"
