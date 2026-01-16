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

# Check DB Connection
# try:
#     # Trigger a connection to verify
#     mongo.cx.server_info()
#     print("✅ MongoDB Connected via PyMongo")
# except Exception as e:
#     print(f"❌ MongoDB Connection Failed: {e}")

# CORS Setup
# CORS Setup
allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
client_url = os.environ.get('CLIENT_URL')
if client_url:
    allowed_origins.append(client_url)

CORS(app, resources={
    r"/api/*": {
        "origins": allowed_origins,
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
        
    if '_id' in doc:
        del doc['_id']
    return doc

# -------------------- Auth Routes --------------------

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email') # Changed from username to email
    password = data.get('password')
    username = data.get('username') # Keep username for display if desired

    if mongo.db.users.find_one({'email': email}):
        return jsonify({"message": "User already exists"}), 400

    from werkzeug.security import generate_password_hash
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    user_id = mongo.db.users.insert_one({
        'email': email, # Storing email as the primary identifier
        'username': username, # Storing username as well
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
        # Optional Weather Data
        'weather': data.get('weather'),
        'temperature': data.get('temperature'),

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

    # Check ownership
    diary = mongo.db.diaries.find_one({'_id': ObjectId(id)})
    if not diary:
         return jsonify({"message": "Diary not found"}), 404
         
    if diary.get('user_id') != current_user_id: # Use .get() for safety, current_user_id is already string
        return jsonify({"message": "Unauthorized"}), 403
    
    data = request.get_json()
    
    update_fields = {
        'event': data.get('event', diary.get('event')),
        'emotion_desc': data.get('emotion_desc', diary.get('emotion_desc')),
        'emotion_meaning': data.get('emotion_meaning', diary.get('emotion_meaning')),
        'self_talk': data.get('self_talk', diary.get('self_talk')),
        'mood_level': data.get('mood_level', diary.get('mood_level')),
        # Update weather if provided
        'weather': data.get('weather', diary.get('weather')),
        'temperature': data.get('temperature', diary.get('temperature')),
        
        # Reset AI
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

@app.route('/api/diaries/search', methods=['GET'])
@jwt_required()
def search_diaries():
    current_user_id = get_jwt_identity()
    query = request.args.get('q', '')
    
    if not query:
        return jsonify([]), 200
        
    filter_query = {
        'user_id': current_user_id,
        '$or': [
            {'event': {'$regex': query, '$options': 'i'}},
            {'emotion_desc': {'$regex': query, '$options': 'i'}},
            {'emotion_meaning': {'$regex': query, '$options': 'i'}},
            {'self_talk': {'$regex': query, '$options': 'i'}}
        ]
    }
    
    cursor = mongo.db.diaries.find(filter_query).sort('created_at', -1).limit(50)
    results = [serialize_doc(doc) for doc in cursor]
    
    return jsonify(results), 200

@app.route('/api/weather-insight', methods=['GET'])
@jwt_required()
def weather_insight():
    current_user_id = get_jwt_identity()
    weather_str = request.args.get('weather', '')
    date_str = request.args.get('date', '') # Optional date param
    
    if not weather_str:
        return jsonify({'message': '날씨 정보가 없어요. 창밖을 한 번 봐주시겠어요?'}), 200

    # 1. Normalize Weather Keyword
    keywords = ["비", "눈", "맑음", "흐림", "구름"]
    target_keyword = "맑음" # Default
    for k in keywords:
        if k in weather_str:
            target_keyword = k
            break
            
    # 2. Aggregation Query
    pipeline = [
        {"$match": {
            "user_id": current_user_id,
            "weather": {"$regex": target_keyword}
        }},
        {"$group": {"_id": "$mood_level", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    
    # Check if date is today to adjust wording
    is_today = True
    if date_str:
        try:
            input_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if input_date != datetime.utcnow().date(): # Approximate check
                is_today = False
        except:
            pass
            
    time_ref = "오늘" if is_today else "이 날"
    
    try:
        result = list(mongo.db.diaries.aggregate(pipeline))
        
        if not result:
            return jsonify({'message': f"{weather_str}, {time_ref}은 어떤 하루가 될까요?"}), 200
            
        top_mood = result[0]['_id']
        
        # Mood Mapping
        mood_msg_map = {
            1: "조금 예민해지거나 화가 나는 날이 많으셨어요.",
            2: "마음이 차분해지거나 혹은 조금 우울해지곤 하셨어요.",
            3: "평범하고 무난한 하루를 보내시는 편이에요.",
            4: "평온하고 여유로운 기분을 느끼셨어요.",
            5: "기분이 아주 좋고 행복한 에너지가 넘치셨어요!"
        }
        
        mood_desc = mood_msg_map.get(top_mood, "다양한 감정을 느끼셨어요.")
        
        insight_message = f"'{target_keyword}' 날씨에는 주로 {mood_desc} {time_ref} 당신의 마음 날씨는 어떤가요?"
        
        return jsonify({'message': insight_message}), 200
        
    except Exception as e:
        print(f"Insight Error: {e}")
        return jsonify({'message': f"{time_ref} 날씨는 '{weather_str}'이네요. 기분 좋은 하루 보내세요!"}), 200

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

@app.route('/api/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    user_id = get_jwt_identity()
    
    pipeline = [
        {'$match': {'user_id': user_id}},
        {
            '$facet': {
                'monthly': [
                    {
                        '$project': {
                            'month': {'$dateToString': {'format': '%Y-%m', 'date': '$created_at'}}
                        }
                    },
                    {'$group': {'_id': '$month', 'count': {'$sum': 1}}},
                    {'$sort': {'_id': 1}}
                ],
                'moods': [
                    {'$group': {'_id': '$mood_level', 'count': {'$sum': 1}}},
                    {'$sort': {'_id': 1}}
                ],
                'weather': [
                     {'$match': {'weather': {'$ne': None}}},
                     {'$group': {
                         '_id': {'weather': '$weather', 'mood': '$mood_level'},
                         'count': {'$sum': 1}
                     }},
                     {'$group': {
                         '_id': '$_id.weather',
                         'moods': {
                             '$push': {
                                 'mood': '$_id.mood',
                                 'count': '$count'
                             }
                         },
                         'total_count': {'$sum': '$count'}
                     }},
                     {'$sort': {'total_count': -1}}
                ],
                'daily': [
                    {
                        '$project': {
                            'day': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$created_at'}}
                        }
                    },
                    {'$group': {'_id': '$day', 'count': {'$sum': 1}}},
                    {'$sort': {'_id': 1}}
                ]
            }
        }
    ]
    
    try:
        results = list(mongo.db.diaries.aggregate(pipeline))
        stats = results[0] if results else {'monthly': [], 'moods': [], 'weather': []}
        return jsonify(stats), 200
    except Exception as e:
        print(f"Stats Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # No SQL create_all() needed
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5001)
