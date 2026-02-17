from flask import Blueprint, jsonify, request

share_bp = Blueprint('share', __name__)

@share_bp.route('/api/v1/share/code', methods=['POST'])
def create_share_code():
    return jsonify({"message": "공유 기능 점검 중입니다.", "code": "TEMP00"}), 200

@share_bp.route('/api/v1/share/connect', methods=['POST'])
def connect_share():
    return jsonify({"message": "점검 중입니다."}), 200

@share_bp.route('/api/v1/share/list', methods=['GET'])
def get_shared_list():
    return jsonify({"data": []}), 200

@share_bp.route('/api/v1/share/disconnect', methods=['POST'])
def disconnect_share():
    return jsonify({"message": "점검 중입니다."}), 200

@share_bp.route('/api/v1/share/insights/<target_id>', methods=['GET'])
def get_shared_insights(target_id):
    return jsonify({"message": "점검 중입니다."}), 200
