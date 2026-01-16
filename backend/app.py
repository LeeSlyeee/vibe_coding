from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_pymongo import PyMongo
from datetime import datetime
from bson.objectid import ObjectId
import os
from config import Config
from tasks import process_diary_ai

app = Flask(__name__)
app.config.from_object(Config)

# MongoDB Setup
mongo = PyMongo(app)

# CORS Setup
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

jwt = JWTManager(app)

# --- Helper Function for ObjectId Serialization ---
def serialize_doc(doc):
    if not doc:
        return None
    doc['id'] = str(doc['_id'])
    
    # Datetime Serialization
    if 'created_at' in doc and isinstance(doc['created_at'], datetime):
        doc['created_at'] = doc['created_at'].isoformat()
        
    del doc['_id']
    return doc

# -------------------- Auth Routes --------------------

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if mongo.db.users.find_one({'username': username}):
        return jsonify({"message": "Username already exists"}), 400

    from werkzeug.security import generate_password_hash
    hashed_password = generate_password_hash(password)

    user_id = mongo.db.users.insert_one({
        'username': username,
        'password_hash': hashed_password,
        'created_at': datetime.utcnow()
    }).inserted_id

    return jsonify({"message": "User registered successfully", "user_id": str(user_id)}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = mongo.db.users.find_one({'username': username})
    
    if not user:
         return jsonify({"message": "Invalid credentials"}), 401

    from werkzeug.security import check_password_hash
    if check_password_hash(user['password_hash'], password):
        # Use ObjectId string as identity
        access_token = create_access_token(identity=str(user['_id'])) 
        return jsonify(access_token=access_token, username=user['username']), 200

    return jsonify({"message": "Invalid credentials"}), 401

# -------------------- Diary Routes --------------------

@app.route('/api/diaries', methods=['GET'])
@jwt_required()
def get_diaries():
    current_user_id = get_jwt_identity()
    
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    filter_query = {'user_id': current_user_id}
    
    if year and month:
        # Date filtering in MongoDB
        # Assuming 'created_at' is stored as ISODate
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
            
        filter_query['created_at'] = {
            '$gte': start_date,
            '$lt': end_date
        }
    
    # Sort by created_at DESC
    cursor = mongo.db.diaries.find(filter_query).sort('created_at', -1)
    
    # Limit default 100
    if not (year and month):
        cursor = cursor.limit(100)
        
    diaries = [serialize_doc(doc) for doc in cursor]
    return jsonify(diaries), 200

@app.route('/api/diaries', methods=['POST'])
@jwt_required()
def create_diary():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    created_at_str = data.get('created_at')

    if created_at_str and created_at_str.endswith('Z'):
        created_at_str = created_at_str[:-1]
        
    created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.utcnow()

    new_diary = {
        'user_id': current_user_id,
        'event': data.get('event', ''),
        'emotion_desc': data.get('emotion_desc', ''),
        'emotion_meaning': data.get('emotion_meaning', ''),
        'self_talk': data.get('self_talk', ''),
        'mood_level': data.get('mood_level', 3),
        'ai_prediction': "분석 중... (AI가 곧 답변해드려요!)",
        'ai_comment': "잠시만 기다려주세요... 🤖",
        'created_at': created_at
    }
    
    try:
        result = mongo.db.diaries.insert_one(new_diary)
        new_diary_id = str(result.inserted_id)
        
        # Trigger Async AI Task with String ID
        task_id = None
        try:
            task = process_diary_ai.delay(new_diary_id)
            task_id = task.id
            
            # Update diary with task_id
            mongo.db.diaries.update_one(
                {'_id': result.inserted_id},
                {'$set': {'task_id': task_id}}
            )
        except Exception as e:
            print(f"Failed to queue celery task: {e}")
        
        # Prepare response
        new_diary['_id'] = result.inserted_id
        response_data = serialize_doc(new_diary)
        response_data['task_id'] = task_id
        
        return jsonify(response_data), 201
        
    except Exception as e:
        return jsonify({"message": f"Create failed: {str(e)}"}), 500

@app.route('/api/diaries/<id>', methods=['GET'])
@jwt_required()
def get_diary(id):
    current_user_id = get_jwt_identity()
    
    # ObjectId validation
    if not ObjectId.is_valid(id):
        return jsonify({"message": "Invalid ID format"}), 400
        
    diary = mongo.db.diaries.find_one({'_id': ObjectId(id)})
    
    if not diary:
        return jsonify({"message": "Diary not found"}), 404
        
    if diary.get('user_id') != current_user_id:
        return jsonify({"message": "Unauthorized"}), 403
    
    return jsonify(serialize_doc(diary)), 200

@app.route('/api/diaries/<id>', methods=['PUT'])
@jwt_required()
def update_diary(id):
    current_user_id = get_jwt_identity()
    
    if not ObjectId.is_valid(id):
        return jsonify({"message": "Invalid ID format"}), 400

    diary = mongo.db.diaries.find_one({'_id': ObjectId(id)})
    if not diary:
         return jsonify({"message": "Diary not found"}), 404
         
    if diary.get('user_id') != current_user_id:
        return jsonify({"message": "Unauthorized"}), 403
    
    data = request.get_json()
    
    update_fields = {
        'event': data.get('event', diary.get('event')),
        'emotion_desc': data.get('emotion_desc', diary.get('emotion_desc')),
        'emotion_meaning': data.get('emotion_meaning', diary.get('emotion_meaning')),
        'self_talk': data.get('self_talk', diary.get('self_talk')),
        'mood_level': data.get('mood_level', diary.get('mood_level')),
        # Reset AI status
        'ai_prediction': "재분석 중...",
        'ai_comment': "AI가 다시 생각하고 있어요... 🤔"
    }
    
    mongo.db.diaries.update_one(
        {'_id': ObjectId(id)},
        {'$set': update_fields}
    )
    
    # Trigger AI Task again
    task_id = None
    try:
        task = process_diary_ai.delay(id)
        task_id = task.id
        mongo.db.diaries.update_one({'_id': ObjectId(id)}, {'$set': {'task_id': task_id}})
    except:
        pass
        
    # Get updated doc
    updated_diary = mongo.db.diaries.find_one({'_id': ObjectId(id)})
    response_data = serialize_doc(updated_diary)
    response_data['task_id'] = task_id
    
    return jsonify(response_data), 200

@app.route('/api/diaries/<id>', methods=['DELETE'])
@jwt_required()
def delete_diary(id):
    current_user_id = get_jwt_identity()
    
    if not ObjectId.is_valid(id):
         return jsonify({"message": "Invalid ID format"}), 400

    diary = mongo.db.diaries.find_one({'_id': ObjectId(id)})
    
    if not diary:
        return jsonify({"message": "Diary not found"}), 404

    if diary.get('user_id') != current_user_id:
        return jsonify({"message": "Unauthorized"}), 403
    
    mongo.db.diaries.delete_one({'_id': ObjectId(id)})
    return jsonify({"message": "Diary deleted successfully"}), 200

# Task Status API (Maintained as is, using Celery backend)
@app.route('/api/tasks/status/<task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id):
    task = process_diary_ai.AsyncResult(task_id)
    response = {
        'state': task.state,
        'process_percent': 0, 'message': '대기 중...', 'eta_seconds': 0
    }
    
    if task.state == 'PENDING':
        response.update({'message': '작업 대기 중...', 'eta_seconds': 15})
    elif task.state == 'PROGRESS':
        response.update({
            'process_percent': task.info.get('process_percent', 0),
            'message': task.info.get('message', ''),
            'eta_seconds': task.info.get('eta_seconds', 0)
        })
    elif task.state == 'SUCCESS':
        response.update({'process_percent': 100, 'message': '분석 완료!', 'eta_seconds': 0})
    else:
        response['message'] = '오류 발생'
        
    return jsonify(response), 200

if __name__ == '__main__':
    # No SQL create_all() needed
    app.run(debug=True, host='0.0.0.0', port=5001)
