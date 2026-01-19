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

from crypto_utils import crypto_manager

# ... imports ...

# Helper to Decrypt Doc
def decrypt_doc(doc):
    if not doc: return None
    sensitive_fields = ['event', 'emotion_desc', 'emotion_meaning', 'self_talk', 'ai_prediction', 'ai_comment', 'mindset']
    for field in sensitive_fields:
        if field in doc and isinstance(doc[field], str):
            doc[field] = crypto_manager.decrypt(doc[field])
    return doc

# Helper to Encrypt Data (for saving)
def encrypt_data(data):
    encrypted = {}
    sensitive_fields = ['event', 'emotion_desc', 'emotion_meaning', 'self_talk', 'ai_prediction', 'ai_comment', 'mindset']
    for k, v in data.items():
        if k in sensitive_fields and isinstance(v, str):
            encrypted[k] = crypto_manager.encrypt(v)
        else:
            encrypted[k] = v
    return encrypted

# --- Usage in Routes ---

@app.route('/api/diaries', methods=['GET'])
@jwt_required()
def get_diaries():
    current_user_id = get_jwt_identity()
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    filter_query = {'user_id': current_user_id}
    if year and month:
        start_date = datetime(year, month, 1)
        if month == 12: end_date = datetime(year + 1, 1, 1)
        else: end_date = datetime(year, month + 1, 1)
        filter_query['created_at'] = {'$gte': start_date, '$lt': end_date}
    
    cursor = mongo.db.diaries.find(filter_query).sort('created_at', -1)
    if not (year and month): cursor = cursor.limit(100)
        
    # Decrypt each doc
    diaries = [serialize_doc(decrypt_doc(doc)) for doc in cursor]
    return jsonify(diaries), 200

@app.route('/api/diaries', methods=['POST'])
@jwt_required()
def create_diary():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    created_at_str = data.get('created_at')
    if created_at_str and created_at_str.endswith('Z'): created_at_str = created_at_str[:-1]
    created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.utcnow()

    # Prepare raw data
    raw_diary = {
        'user_id': current_user_id,
        'event': data.get('event', ''),
        'emotion_desc': data.get('emotion_desc', ''),
        'emotion_meaning': data.get('emotion_meaning', ''),
        'self_talk': data.get('self_talk', ''),
        'mood_level': data.get('mood_level', 3),
        'weather': data.get('weather'),
        'temperature': data.get('temperature'),
        'ai_prediction': "분석 중... (AI가 곧 답변해드려요!)",
        'ai_comment': "잠시만 기다려주세요... 🤖",
        'created_at': created_at
    }
    
    # Encrypt before insert
    encrypted_diary = encrypt_data(raw_diary)
    
    try:
        result = mongo.db.diaries.insert_one(encrypted_diary)
        new_diary_id = str(result.inserted_id)
        
        # Trigger Task
        task_id = None
        try:
            task = process_diary_ai.delay(new_diary_id)
            task_id = task.id
            mongo.db.diaries.update_one({'_id': result.inserted_id}, {'$set': {'task_id': task_id}})
        except Exception as e:
            print(f"Failed to queue task: {e}")
        
        # Return Decrypted Response (which is just raw_diary with ID)
        raw_diary['_id'] = result.inserted_id
        response_data = serialize_doc(raw_diary)
        response_data['task_id'] = task_id
        return jsonify(response_data), 201
        
    except Exception as e:
        return jsonify({"message": f"Create failed: {str(e)}"}), 500

@app.route('/api/diaries/<id>', methods=['GET'])
@jwt_required()
def get_diary(id):
    current_user_id = get_jwt_identity()
    if not ObjectId.is_valid(id): return jsonify({"message": "Invalid ID"}), 400
    
    diary = mongo.db.diaries.find_one({'_id': ObjectId(id)})
    if not diary: return jsonify({"message": "Not found"}), 404
    if diary.get('user_id') != current_user_id: return jsonify({"message": "Unauthorized"}), 403
    
    return jsonify(serialize_doc(decrypt_doc(diary))), 200

@app.route('/api/diaries/<id>', methods=['PUT'])
@jwt_required()
def update_diary(id):
    current_user_id = get_jwt_identity()
    if not ObjectId.is_valid(id): return jsonify({"message": "Invalid ID"}), 400
    
    diary = mongo.db.diaries.find_one({'_id': ObjectId(id)})
    if not diary: return jsonify({"message": "Not found"}), 404
    if diary.get('user_id') != current_user_id: return jsonify({"message": "Unauthorized"}), 403
    
    data = request.get_json()
    
    # Prepare update fields
    updates = {
        'event': data.get('event', crypto_manager.decrypt(diary.get('event'))), # Use existing decrypted if not provided
        'emotion_desc': data.get('emotion_desc', crypto_manager.decrypt(diary.get('emotion_desc'))),
        'emotion_meaning': data.get('emotion_meaning', crypto_manager.decrypt(diary.get('emotion_meaning'))),
        'self_talk': data.get('self_talk', crypto_manager.decrypt(diary.get('self_talk'))),
        'mood_level': data.get('mood_level', diary.get('mood_level')),
        'weather': data.get('weather', diary.get('weather')),
        'temperature': data.get('temperature', diary.get('temperature')),
        'ai_prediction': "재분석 중...",
        'ai_comment': "AI가 다시 생각하고 있어요... 🤔"
    }
    
    # Encrypt updates
    encrypted_updates = encrypt_data(updates)
    
    mongo.db.diaries.update_one({'_id': ObjectId(id)}, {'$set': encrypted_updates})
    
    # Trigger AI
    task_id = None
    try:
        task = process_diary_ai.delay(id)
        task_id = task.id
        mongo.db.diaries.update_one({'_id': ObjectId(id)}, {'$set': {'task_id': task_id}})
    except: pass
    
    # Return decrypted
    updated_diary = mongo.db.diaries.find_one({'_id': ObjectId(id)})
    return jsonify(serialize_doc(decrypt_doc(updated_diary))), 200

@app.route('/api/diaries/search', methods=['GET'])
@jwt_required()
def search_diaries():
    current_user_id = get_jwt_identity()
    query = request.args.get('q', '')
    if not query: return jsonify([]), 200
    
    # ⚠️ Encryption Limitation: Cannot use MongoDB $regex.
    # Must fetch ALL diaries (id, dates) and decrypt in memory to search.
    # For 20k diaries, this might be slow. Limit to last 1000 for performance?
    # Or fetch all. Let's try last 500 for responsiveness.
    
    cursor = mongo.db.diaries.find({'user_id': current_user_id}).sort('created_at', -1).limit(500)
    
    results = []
    for doc in cursor:
        decrypted = decrypt_doc(doc)
        # Search in decrypted fields
        if (query in decrypted.get('event','') or 
            query in decrypted.get('emotion_desc','') or 
            query in decrypted.get('emotion_meaning','') or 
            query in decrypted.get('self_talk','')):
            results.append(serialize_doc(decrypted))
            if len(results) >= 50: break # Limit output
            
    return jsonify(results), 200

@app.route('/api/weather-insight', methods=['GET'])
@jwt_required()
def weather_insight():
    # Similar adjustment needed if aggregation uses encrypted fields.
    # But weather insight logic currently uses 'mood_level' (int) and 'weather' (plain string probably?)
    # Weather field was NOT in sensitive list in migrate script. So it's plain text.
    # Aggregation works fine!
    return weather_insight_original() # Wrapper to keep original logic logic

# For Statistics, we need to decrypt AI prediction
@app.route('/api/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    user_id = get_jwt_identity()
    diaries = list(mongo.db.diaries.find({'user_id': user_id}).sort('created_at', 1))
    
    # Decrypt 'ai_prediction' for processing
    for d in diaries:
        if 'ai_prediction' in d:
            d['ai_prediction'] = crypto_manager.decrypt(d['ai_prediction'])
            
    # Copy paste the rest of the statistics logic logic...
    # (Reusing existing logic with decrypted 'diaries' list)
    
    stats = {
        'monthly': {},
        'moods': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        'weather': {},
        'daily_sum': {},
        'daily_count': {},
        'timeline': []
    }
    
    from datetime import timedelta
    KST = timedelta(hours=9)
    
    for d in diaries:
        ai_mood = map_ai_to_mood(d.get('ai_prediction'))
        user_mood = d.get('mood_level')
        mood = ai_mood if ai_mood else (user_mood if user_mood is not None else 3)
        try: mood = int(mood)
        except: mood = 3
        if not (1 <= mood <= 5): mood = 3
            
        utc_date = d.get('created_at')
        if not utc_date: continue
        local_date = utc_date + KST
        date_str = local_date.strftime('%Y-%m-%d')
        month_str = local_date.strftime('%Y-%m')
        
        stats['monthly'][month_str] = stats['monthly'].get(month_str, 0) + 1
        stats['moods'][mood] = stats['moods'].get(mood, 0) + 1
        
        weather = d.get('weather')
        if weather:
            if weather not in stats['weather']: stats['weather'][weather] = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0, 'total': 0}
            stats['weather'][weather][str(mood)] += 1
            stats['weather'][weather]['total'] += 1
            
        stats['daily_sum'][date_str] = stats['daily_sum'].get(date_str, 0) + mood
        stats['daily_count'][date_str] = stats['daily_count'].get(date_str, 0) + 1
        
        stats['timeline'].append({
            'date': date_str,
            'mood_level': mood,
            'ai_label': d.get('ai_prediction', ''), # Decrypted
            'user_mood': user_mood
        })

    daily_moods = {}
    for k in stats['daily_sum']:
        daily_moods[k] = round(stats['daily_sum'][k] / stats['daily_count'][k])

    response_data = {
        'monthly': sorted([{'month': k, 'count': v} for k, v in stats['monthly'].items()], key=lambda x: x['month']),
        'moods': sorted([{'_id': k, 'count': v} for k, v in stats['moods'].items()], key=lambda x: x['_id']),
        'daily': sorted([{'_id': k, 'count': v} for k, v in daily_moods.items()], key=lambda x: x['_id']),
        'timeline': stats['timeline'],
        'weather': []
    }
    
    for w, counts in stats['weather'].items():
        moods_list = [{'mood': m, 'count': counts[str(m)]} for m in range(1, 6) if counts[str(m)] > 0]
        response_data['weather'].append({'_id': w, 'moods': moods_list, 'total_count': counts['total']})
    
    response_data['weather'].sort(key=lambda x: x['total_count'], reverse=True)
    return jsonify(response_data), 200

# Need to redefine weather_insight_original or just keep it as is since it wasn't modified in the diff block logic
def weather_insight_original():
    current_user_id = get_jwt_identity()
    weather_str = request.args.get('weather', '')
    date_str = request.args.get('date', '')
    if not weather_str: return jsonify({'message': '날씨 정보가 없어요.'}), 200
    
    keywords = ["비", "눈", "맑음", "흐림", "구름"]
    target_keyword = "맑음"
    for k in keywords:
        if k in weather_str:
            target_keyword = k
            break
            
    pipeline = [
        {"$match": {"user_id": current_user_id, "weather": {"$regex": target_keyword}}},
        {"$group": {"_id": "$mood_level", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    
    try:
        result = list(mongo.db.diaries.aggregate(pipeline))
        if not result: return jsonify({'message': f"{weather_str}, 기록된 패턴이 없네요."}), 200
        top_mood = result[0]['_id']
        mood_msg_map = {1: "예민", 2: "우울", 3: "평범", 4: "평온", 5: "행복"}
        mood_desc = mood_msg_map.get(top_mood, "다양한")
        return jsonify({'message': f"'{target_keyword}' 날씨에는 주로 {mood_desc}한 기분을 느끼셨어요."}), 200
    except:
        return jsonify({'message': ""}), 200

if __name__ == '__main__':
    # No SQL create_all() needed
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5001)
