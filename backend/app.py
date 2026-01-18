from flask import Flask, jsonify, request
# from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_pymongo import PyMongo
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import os
from config import Config
from tasks import process_diary_ai
from ai_brain import EmotionAnalysis

app = Flask(__name__)
app.config.from_object(Config)

# Global AI for immediate insights (Lazy loaded)
insight_ai = None

# ... (Previous code)

@app.route('/api/insight', methods=['GET'])
@jwt_required()
def get_insight():
    global insight_ai
    current_user_id = get_jwt_identity()
    
    # 1. Lazy Load AI
    if insight_ai is None:
        print("💡 Initializing AI for Insight (Lazy Load)...")
        try:
            insight_ai = EmotionAnalysis()
        except Exception as e:
            print(f"Failed to load AI: {e}")
            return jsonify({'message': "AI를 준비하는 중입니다. 잠시 후 다시 시도해주세요."}), 503

    # 2. Date Calculation (Target Date - 3 Weeks)
    target_date_str = request.args.get('date')
    
    if target_date_str:
        try:
            # Parse 'YYYY-MM-DD' and set time to end of that day for inclusion
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
            # End of target date (next day 00:00:00)
            end_date = target_date + timedelta(days=1)
        except ValueError:
            target_date = datetime.utcnow()
            end_date = target_date + timedelta(days=1)
    else:
        target_date = datetime.utcnow()
        end_date = target_date + timedelta(days=1)

    start_date = target_date - timedelta(weeks=1)
    
    try:
        # 3. Fetch Diaries (Range: Start -> End)
        print(f"🔍 [Insight] Query Range: {start_date} to {end_date} (User: {current_user_id})")
        cursor = mongo.db.diaries.find({
            'user_id': current_user_id,
            'created_at': {
                '$gte': start_date,
                '$lt': end_date
            }
        }).sort('created_at', 1) 
        
        recent_diaries = []
        for doc in cursor:
            recent_diaries.append({
                'date': doc.get('created_at').strftime('%Y-%m-%d') if doc.get('created_at') else '',
                'mood': doc.get('mood_level', '보통'),
                'event': doc.get('event', '')[:50]
            })
        
        print(f"📊 [Insight] Found {len(recent_diaries)} diaries for context.")

        # 3.5. Fetch Weather Stats (Historical Pattern)
        weather = request.args.get('weather')
        weather_stats = None
        if weather:
            print(f"📊 [Insight] Finding historical patterns for weather: {weather}")
            # Search all past diaries with the same weather
            weather_cursor = mongo.db.diaries.find({
                'user_id': current_user_id,
                'weather': weather
            })
            
            emotion_counts = {}
            for doc in weather_cursor:
                # Use ai_prediction if available, else mood_level
                pred_raw = doc.get('ai_prediction', '')
                pred = pred_raw.split(' ')[0] if pred_raw else ""
                
                if not pred:
                    lvl = doc.get('mood_level', 3)
                    pred = {1:'화남', 2:'우울', 3:'평범', 4:'편안', 5:'행복'}.get(lvl, '평범')
                
                emotion_counts[pred] = emotion_counts.get(pred, 0) + 1
            
            if emotion_counts:
                # Sort by count
                sorted_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)
                # Keep top 2
                weather_stats = ", ".join([f"'{e[0]}'" for e in sorted_emotions[:2]])
                print(f"📈 [Insight] Top emotions for {weather}: {weather_stats}")

        # 4. Generate Insight
        message = insight_ai.generate_pre_write_insight(recent_diaries, weather=weather, weather_stats=weather_stats)
        
        # If message is None (filtered or failed), return empty
        if not message:
             print("💡 [Insight] Final result is None (Fallback triggered)")
             return jsonify({'message': ""}), 200
             
        print(f"✅ [Insight] Final Response: {message[:30]}...")
        return jsonify({'message': message}), 200
        
    except Exception as e:
        print(f"Insight Route Error: {e}")
        return jsonify({'message': ""}), 200

# ... (Existing Stats Route)


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
# CORS Setup - Allow All (Debug Mode)
# CORS(app, resources={
#     r"/*": {
#         "origins": "*",
#         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#         "allow_headers": ["Content-Type", "Authorization"],
#     }
# })

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
    username = data.get('username')
    password = data.get('password')

    if mongo.db.users.find_one({'username': username}):
        return jsonify({"message": "User already exists"}), 400

    from werkzeug.security import generate_password_hash
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

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

# --- Helper to map AI string to Mood Level (1-5) ---
def map_ai_to_mood(ai_str):
    if not ai_str or not isinstance(ai_str, str):
        return None
        
    # Extract label part (before parenthesis if exists)
    # Ex: "슬픔 (비통함) (85.2%)" -> "슬픔 (비통함)"
    clean_str = ai_str.split('(')[0].strip() if '(' in ai_str else ai_str
    
    # Keywords Mapping
    # 1: 화남 😠
    # 2: 우울 😢
    # 3: 보통 😐
    # 4: 편안 😌
    # 5: 행복 😊
    
    if any(k in ai_str for k in ['분노', '짜증', '배신', '혐오', '화가', '불쾌', '억울']):
        return 1
    elif any(k in ai_str for k in ['슬픔', '우울', '외로움', '무기력', '후회', '비참', '괴로움', '지침', '죄책', '부끄', '한심', '불안', '당황', '두려움', '혼란', '걱정', '긴장', '고독', '상실', '좌절']):
        return 2
    elif any(k in ai_str for k in ['보통', '무난', '평범']):
        return 3
    elif any(k in ai_str for k in ['편안', '감사', '만족', '홀가분', '안정', '여유']):
        return 4
    elif any(k in ai_str for k in ['기쁨', '설렘', '신남', '자신', '뿌듯', '행복', '환희', '성취']):
        return 5
        
    return None

@app.route('/api/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    user_id = get_jwt_identity()
    
    # Fetch all diaries to process in Python (more flexible for string parsing)
    diaries = list(mongo.db.diaries.find({'user_id': user_id}).sort('created_at', 1))
    
    # Initial stats setup
    stats = {
        'monthly': {},
        'moods': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        'weather': {},
        'daily_sum': {},
        'daily_count': {},
        'timeline': []
    }
    
    # Timezone Offset (KST = UTC+9)
    from datetime import timedelta
    KST = timedelta(hours=9)
    
    for d in diaries:
        # Determine Mood Level: AI Analysis takes priority over User Input
        ai_mood = map_ai_to_mood(d.get('ai_prediction'))
        user_mood = d.get('mood_level')
        
        # Priority: AI Predicted (1-5) > User Input (1-5) > Default (3)
        mood = ai_mood if ai_mood else (user_mood if user_mood is not None else 3)
        
        # Ensure mood is int and in range
        try:
            mood = int(mood)
            if not (1 <= mood <= 5): mood = 3
        except:
            mood = 3
            
        # created_at is in UTC in MongoDB
        utc_date = d.get('created_at')
        if not utc_date: continue
        
        # Convert to local time (KST) for correct 'Day' display
        local_date = utc_date + KST
        date_str = local_date.strftime('%Y-%m-%d')
        month_str = local_date.strftime('%Y-%m')
        
        # 1. Monthly Count (Total number of diaries)
        stats['monthly'][month_str] = stats['monthly'].get(month_str, 0) + 1
        
        # 2. Mood Collection (For overall distribution)
        stats['moods'][mood] = stats['moods'].get(mood, 0) + 1
        
        # 3. Weather-Mood Stats
        weather = d.get('weather')
        if weather:
            if weather not in stats['weather']:
                stats['weather'][weather] = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0, 'total': 0}
            stats['weather'][weather][str(mood)] += 1
            stats['weather'][weather]['total'] += 1
            
        # 4. Daily Mood Calculation (Prepare for Average)
        stats['daily_sum'][date_str] = stats['daily_sum'].get(date_str, 0) + mood
        stats['daily_count'][date_str] = stats['daily_count'].get(date_str, 0) + 1
        
        # 5. Timeline (Raw entries)
        stats['timeline'].append({
            'date': date_str,
            'mood_level': mood,
            'ai_label': d.get('ai_prediction', ''),
            'user_mood': user_mood # Keep raw user input for comparison if needed
        })
        
    # Calculate Daily Averages for the Bar Chart
    daily_moods = {}
    for date_key in stats['daily_sum']:
        # Average rounded to nearest integer for Bar/Flow display
        avg_mood = round(stats['daily_sum'][date_key] / stats['daily_count'][date_key])
        daily_moods[date_key] = avg_mood

    # Format for Frontend
    response_data = {
        'monthly': [{'month': k, 'count': v} for k, v in stats['monthly'].items()],
        'moods': [{'_id': k, 'count': v} for k, v in stats['moods'].items()],
        'daily': [{'_id': k, 'count': v} for k, v in daily_moods.items()],
        'timeline': stats['timeline'],
        'weather': []
    }
    
    # Sort Lists
    response_data['monthly'].sort(key=lambda x: x['month'])
    response_data['moods'].sort(key=lambda x: x['_id'])
    response_data['daily'].sort(key=lambda x: x['_id'])
    
    # Format Weather
    for w, counts in stats['weather'].items():
        moods_list = []
        for m in range(1, 6):
            if counts[str(m)] > 0:
                moods_list.append({'mood': m, 'count': counts[str(m)]})
        
        response_data['weather'].append({
            '_id': w,
            'moods': moods_list,
            'total_count': counts['total']
        })
    
    response_data['weather'].sort(key=lambda x: x['total_count'], reverse=True)

    return jsonify(response_data), 200

if __name__ == '__main__':
    # No SQL create_all() needed
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5001)
