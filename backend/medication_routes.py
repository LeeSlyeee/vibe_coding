from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

med_bp = Blueprint('medication', __name__)

@med_bp.route('/api/user/profile', methods=['GET', 'PUT'])
@med_bp.route('/api/user/profile/', methods=['GET', 'PUT'])
@jwt_required()
def user_profile():
    from models import db, User
    current_user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=current_user_id).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if request.method == 'GET':
        return jsonify({
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname or user.real_name or user.username,
            "real_name": user.real_name or "",
            "birth_date": getattr(user, 'birth_date', None) or "",
            "center_code": user.center_code or ""
        }), 200
    
    # PUT: 프로필 업데이트
    data = request.get_json() or {}
    
    # Whitelist 방식: 허용된 필드만 업데이트
    if 'nickname' in data and data['nickname']:
        user.nickname = data['nickname']
    if 'birth_date' in data and data['birth_date']:
        user.birth_date = data['birth_date']
    if 'real_name' in data and data['real_name']:
        user.real_name = data['real_name']
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "nickname": user.nickname,
        "birth_date": getattr(user, 'birth_date', None) or "",
        "real_name": user.real_name or ""
    }), 200

@med_bp.route('/api/medications', methods=['GET', 'POST'])
def medications():
    if request.method == 'GET':
        return jsonify([]), 200
    return jsonify({"message": "복약 관리 기능 점검 중입니다."}), 200

@med_bp.route('/api/medications/<med_id>', methods=['DELETE'])
def delete_medication(med_id):
    return jsonify({"message": "점검 중입니다."}), 200

@med_bp.route('/api/medications/log', methods=['POST'])
def log_medication():
    return jsonify({"message": "점검 중입니다."}), 200

@med_bp.route('/api/medications/logs', methods=['GET'])
def get_medication_logs():
    return jsonify([]), 200

@med_bp.route('/api/assessment', methods=['POST'])
def submit_assessment():
    return jsonify({"message": "진단 기능 점검 중입니다.", "risk_level": "mild", "care_plan": ""}), 200

# [Disabled] Report handled by app.py
# @med_bp.route('/api/report/start', methods=['POST'])
# def start_report():
#     return jsonify({"message": "리포트 기능 점검 중입니다."}), 200

# @med_bp.route('/api/report/status', methods=['GET'])
# def get_report_status():
#     return jsonify({"status": "completed", "report": "시스템 점검 중입니다."}), 200

# [Disabled] Statistics handled by app.py
# @med_bp.route('/api/statistics', methods=['GET'])
# def get_statistics():
#    return jsonify({"timeline": [], "moods": [], "daily": [], "weather": []}), 200
