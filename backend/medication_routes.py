from flask import Blueprint, jsonify, request

med_bp = Blueprint('medication', __name__)

@med_bp.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    return jsonify({"message": "Service Temporarily Unavailable"}), 503

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
