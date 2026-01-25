from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_pymongo import PyMongo
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import os
from config import Config
from config import Config
# Imports moved down to prevent circular dependency
# from tasks import process_diary_ai, analyze_diary_logic
# from ai_brain import EmotionAnalysis

app = Flask(__name__)
app.config.from_object(Config)

# Imports moved to bottom to prevent circular dependency hanging the route registration
# from tasks import process_diary_ai, analyze_diary_logic
# from ai_brain import EmotionAnalysis
# ...

# Global AI for immediate insights (Lazy loaded) - Kept for other routes
insight_ai = None

@app.route('/api/test/hello', methods=['GET'])
def test_hello():
    return jsonify({"message": "Hello from backend!"}), 200

@app.route('/api/chat/reaction', methods=['POST'])
@jwt_required()
def chat_reaction():
    # Use Standalone Function for robustness & Analysis capability
    data = request.json
    text = data.get('text', '')
    mode = data.get('mode', 'reaction') # Accept 'mode'
    if not text:
        return jsonify({'reaction': ""}), 200
        
    # Directly call function, bypassing class instantiation issues
    reaction = generate_analysis_reaction_standalone(text, mode=mode)
    return jsonify({'reaction': reaction}), 200

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
    sensitive_fields = ['event', 'emotion_desc', 'emotion_meaning', 'self_talk', 'sleep_condition', 'sleep_desc', 'ai_prediction', 'ai_comment', 'mindset']
    for field in sensitive_fields:
        if field in doc and isinstance(doc[field], str):
            doc[field] = crypto_manager.decrypt(doc[field])
    return doc

def map_ai_to_mood(ai_text):
    """
    Parses '평범 (85%)' or '평범' style strings and maps them to 1-5 level.
    """
    if not ai_text: return None
    # 5: 행복, 기쁨
    if "행복" in ai_text or "기쁨" in ai_text: return 5
    # 4: 편안, 평온
    if "평온" in ai_text or "편안" in ai_text: return 4
    # 3: 평범, 중립, 보통
    if "평범" in ai_text or "중립" in ai_text or "보통" in ai_text: return 3
    # 2: 우울, 슬픔, 비통
    if "우울" in ai_text or "슬픔" in ai_text: return 2
    # 1: 화남, 분노
    if "화남" in ai_text or "분노" in ai_text: return 1
    
    return None # Fallback to user_mood logic in caller

# Helper to Encrypt Data (for saving)
def encrypt_data(data):
    encrypted = {}
    sensitive_fields = ['event', 'emotion_desc', 'emotion_meaning', 'self_talk', 'sleep_condition', 'sleep_desc', 'ai_prediction', 'ai_comment', 'mindset']
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
    print(f"🔍 [DEBUG] Received diary data: {data}")
    print(f"🔍 [DEBUG] sleep_desc value: '{data.get('sleep_desc', 'NOT_FOUND')}'")
    created_at_str = data.get('created_at')
    if created_at_str and created_at_str.endswith('Z'): created_at_str = created_at_str[:-1]
    created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.utcnow()

    # Prepare raw data
    raw_diary = {
        'user_id': current_user_id,
        'event': data.get('event', ''),
        'sleep_desc': data.get('sleep_desc', ''),
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
        
        # Trigger Task (Threading) only if AI analysis is missing
        request_ai_pred = data.get('ai_prediction', '').strip()
        request_ai_comment = data.get('ai_comment', '').strip()
        
        # Check if client provided valid analysis (Hybrid Logic)
        # Note: "분석 중..." or similar placeholders mean no analysis provided.
        is_client_analyzed = (
            request_ai_pred and 
            request_ai_comment and 
            "분석 중" not in request_ai_pred and 
            "기다려주세요" not in request_ai_comment
        )

        task_id = "local-thread"
        
        if is_client_analyzed:
            print("📱 [Hybrid] Client provided AI analysis. Back-end analysis skipped.")
            task_id = "client-side"
            # Update the stored document with the provided AI fields if raw_diary had placeholders
            # But wait, raw_diary was initialized with placeholders above. 
            # We need to update raw_diary BEFORE encryption or update the DB after.
            # Let's adjust raw_diary creation.
            
            # Actually, raw_diary logic above set default placeholders. 
            # We should used the provided values if they exist.
            # Let's correct the workflow:
            # 1. We already inserted the doc. If we want to use client values, we should have used them in insert.
            # To fix this without massive refactor: We update the doc immediately if client provided data.
            
            # Re-encrypt client provided values
            ai_updates = {
                'ai_prediction': crypto_manager.encrypt(request_ai_pred),
                'ai_comment': crypto_manager.encrypt(request_ai_comment),
                'task_id': 'client-side'
            }
            mongo.db.diaries.update_one({'_id': result.inserted_id}, {'$set': ai_updates})
            
            # Update response data to reflect this
            raw_diary['ai_prediction'] = request_ai_pred
            raw_diary['ai_comment'] = request_ai_comment
            
        else:
            print("☁️ [Hybrid] No AI analysis provided. Triggering Server AI...")
            try:
                threading.Thread(
                    target=analyze_diary_logic, 
                    args=(new_diary_id,)
                ).start()
                mongo.db.diaries.update_one({'_id': result.inserted_id}, {'$set': {'task_id': task_id}})
            except Exception as e:
                print(f"Failed to start thread: {e}")
        
        # Return Decrypted Response
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
        'sleep_desc': data.get('sleep_desc', crypto_manager.decrypt(diary.get('sleep_desc'))),
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
    
    mongo.db.diaries.update_one({'_id': ObjectId(id)}, {'$set': encrypted_updates})
    
    # [Hybrid Logic for Update]
    # Check if client provided valid analysis in this update request
    req_ai_pred = data.get('ai_prediction', '').strip()
    req_ai_comment = data.get('ai_comment', '').strip()
    
    is_client_analyzed = (
        req_ai_pred and 
        req_ai_comment and 
        "재분석 중" not in req_ai_pred and 
        "기다려주세요" not in req_ai_comment
    )

    if is_client_analyzed:
        print(f"📱 [Hybrid-Update] Client provided AI analysis for {id}. Server analysis skipped.")
        # We don't need to do anything extra because we already saved the encrypted_updates above,
        # which included ai_prediction/ai_comment if they were present in 'data'.
        # Wait, let's double check 'encrypted_updates' creation above.
        
        # 'updates' dict above sets ai_prediction to "재분석 중..." by default.
        # We need to override that default if client provided data.
        
        # Correct logic:
        # If client provided data, we should have used it in 'updates' dict.
        # Since 'updates' dict was hardcoded with placeholders, we must update DB again here.
        
        ai_fix = {
            'ai_prediction': crypto_manager.encrypt(req_ai_pred),
            'ai_comment': crypto_manager.encrypt(req_ai_comment),
            'task_id': 'client-side-update'
        }
        mongo.db.diaries.update_one({'_id': ObjectId(id)}, {'$set': ai_fix})
        
    else:
        print(f"☁️ [Hybrid-Update] No AI provided. Triggering Server AI Re-analysis for {id}...")
        try:
            threading.Thread(
                target=analyze_diary_logic,
                args=(id,)
            ).start()
            mongo.db.diaries.update_one({'_id': ObjectId(id)}, {'$set': {'task_id': 'local-thread'}})
        except Exception as e: 
            print(f"Failed to start thread: {e}")
    
    # Return decrypted
    updated_diary = mongo.db.diaries.find_one({'_id': ObjectId(id)})
    return jsonify(serialize_doc(decrypt_doc(updated_diary))), 200

@app.route('/api/diaries/<id>', methods=['DELETE'])
@jwt_required()
def delete_diary(id):
    current_user_id = get_jwt_identity()
    print(f"🗑️ [DELETE] Request for ID: {id}, User: {current_user_id}")
    
    if not ObjectId.is_valid(id): 
        print("❌ Invalid ID format")
        return jsonify({"message": "Invalid ID"}), 400
    
    diary = mongo.db.diaries.find_one({'_id': ObjectId(id)})
    if not diary: 
        print("❌ Diary not found in DB")
        return jsonify({"message": "Not found"}), 404
        
    print(f"📄 Found Diary User: {diary.get('user_id')}")
    
    if diary.get('user_id') != current_user_id: 
        print("❌ Unauthorized: User mismatch")
        return jsonify({"message": "Unauthorized"}), 403
    
    result = mongo.db.diaries.delete_one({'_id': ObjectId(id)})
    print(f"✅ Delete Result: {result.deleted_count}")
    
    return jsonify({"message": "Deleted successfully"}), 200

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
    
    from datetime import timedelta
    KST = timedelta(hours=9)
    
    stats = {
        'monthly': {},
        'moods': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        'weather': {},
        'daily_sum': {},
        'daily_count': {},
        'timeline': []
    }
    
    for d in diaries:
        # Full Decryption
        decrypted = decrypt_doc(d)
        
        # Extract Data from Decrypted Doc
        ai_pred_raw = decrypted.get('ai_prediction')
        user_mood = decrypted.get('mood_level')
        weather = decrypted.get('weather')
        created_at = decrypted.get('created_at') # Should be datetime object from decrypt_doc logic

        # Determine Mood
        ai_mood = map_ai_to_mood(ai_pred_raw)
        mood = ai_mood if ai_mood else (user_mood if user_mood is not None else 3)
        
        try: 
            mood = int(mood)
        except: 
            mood = 3
        if not (1 <= mood <= 5): mood = 3
            
        if not created_at: continue
        
        # Handle timezone if naive or UTC
        # Assuming decrypt_doc returns datetime. If it's UTC, add KST.
        # If decrypt_doc handles timezone, adjust accordingly. 
        # Usually pymongo returns UTC datetime.
        local_date = created_at + KST
        date_str = local_date.strftime('%Y-%m-%d')
        month_str = local_date.strftime('%Y-%m')
        
        stats['monthly'][month_str] = stats['monthly'].get(month_str, 0) + 1
        stats['moods'][mood] = stats['moods'].get(mood, 0) + 1
        
        if weather:
            if weather not in stats['weather']: stats['weather'][weather] = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0, 'total': 0}
            stats['weather'][weather][str(mood)] += 1
            stats['weather'][weather]['total'] += 1
            
        stats['daily_sum'][date_str] = stats['daily_sum'].get(date_str, 0) + mood
        stats['daily_count'][date_str] = stats['daily_count'].get(date_str, 0) + 1
        
        stats['timeline'].append({
            'date': date_str,
            'mood_level': mood,
            'ai_label': ai_pred_raw if ai_pred_raw else '',
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

# Async Report Generation
import threading

# Global AI Brain Instance for reuse (Singleton)
global_ai_brain = None

def get_ai_brain():
    global global_ai_brain
    if global_ai_brain is None:
        from ai_brain import EmotionAnalysis
        print("🧠 [App] Initializing Global EmotionAnalysis Instance...")
        global_ai_brain = EmotionAnalysis()
    return global_ai_brain

def background_generate_task(app_instance, user_id, final_input):
    """Background thread to generate report without blocking"""
    with app_instance.app_context():
        try:
            print(f"🧵 [Thread] Starting background report generation for {user_id}")
            ai = get_ai_brain()
            report_content = ai.generate_comprehensive_report(final_input)
            
            # 1. Archive Report (New Collection)
            new_report = {
                'user_id': user_id,
                'content': report_content,
                'created_at': datetime.utcnow(),
                'type': 'comprehensive'
            }
            mongo.db.reports.insert_one(new_report)
            print(f"✅ [Thread] Report archived to DB.")
            
            # 2. Update User Status
            mongo.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {
                    'report_status': 'completed',
                    'latest_report': report_content,
                    'report_updated_at': datetime.utcnow()
                }}
            )
            print(f"✅ [Thread] Report generation complete for {user_id}")
            
        except Exception as e:
            print(f"❌ [Thread] Report generation failed: {e}")
            mongo.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'report_status': 'failed'}}
            )

def background_long_term_task(app_instance, user_id, history_data):
    """Background thread to generate long-term insight without blocking"""
    with app_instance.app_context():
        try:
            print(f"🧵 [Thread] Starting long-term analysis for {user_id}")
            ai = get_ai_brain()
            insight = ai.generate_long_term_insight(history_data)
            
            # Update User Status & Result
            mongo.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {
                    'longterm_status': 'completed',
                    'longterm_result': insight,
                    'longterm_updated_at': datetime.utcnow()
                }}
            )
            print(f"✅ [Thread] Long-term analysis complete for {user_id}")
            
        except Exception as e:
            print(f"❌ [Thread] Long-term analysis failed: {e}")
            mongo.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'longterm_status': 'failed'}}
            )

@app.route('/api/report/longterm/start', methods=['POST'])
@jwt_required()
def start_long_term_report():
    user_id = get_jwt_identity()
    
    # 1. Fetch Past Reports (Limit 5 most recent)
    cursor = mongo.db.reports.find({'user_id': user_id, 'type': 'comprehensive'}).sort('created_at', -1).limit(5)
    reports = list(cursor)
    
    if len(reports) < 2:
        return jsonify({"message": "장기 분석을 하려면 최소 2개 이상의 심층 리포트가 필요해요."}), 400
        
    # Prepare Data
    reports.reverse() 
    history_data = []
    for r in reports:
        history_data.append({
            'date': r['created_at'].strftime('%Y-%m-%d'),
            'content': r['content']
        })
        
    # 2. Set Status & Start Thread
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'longterm_status': 'processing'}}
    )

    thread = threading.Thread(target=background_long_term_task, args=(app, user_id, history_data))
    thread.start()
        
    return jsonify({"status": "processing", "message": "과거 기록 통합 분석을 시작했습니다."}), 202

@app.route('/api/report/longterm/status', methods=['GET'])
@jwt_required()
def check_long_term_report_status():
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        return jsonify({"status": "none"}), 200
        
    status = user.get('longterm_status', 'none')
    insight = ''
    
    if status == 'completed':
        insight = user.get('longterm_result', '')
        
    return jsonify({"status": status, "insight": insight}), 200

@app.route('/api/report/start', methods=['POST'])
@jwt_required()
def start_report_generation():
    user_id = get_jwt_identity()

    # 1. Check Diaries
    cursor = mongo.db.diaries.find({'user_id': user_id}).sort('created_at', -1).limit(50)
    diaries = list(cursor)

    if len(diaries) < 3:
        return jsonify({"status": "error", "message": "분석을 위해서는 최소 3일 이상의 기록이 필요해요."}), 400

    # 2. Summarize Data
    summary_lines = []
    mood_counts = {}

    for d in diaries:
        decrypted = decrypt_doc(d)
        date = decrypted.get('created_at').strftime('%Y-%m-%d') if decrypted.get('created_at') else "날짜없음"
        mood = decrypted.get('mood_level', 3)
        event = decrypted.get('event', '')[:50].replace('\n', ' ')
        emotion = decrypted.get('emotion_desc', '')[:30]
        thought = decrypted.get('emotion_meaning', '')[:30]
        
        summary_lines.append(f"- {date} (기분:{mood}/5): {event} | 감정: {emotion} | 생각: {thought}")
        mood_counts[mood] = mood_counts.get(mood, 0) + 1

    summary_text = "\n".join(summary_lines)
    stats_text = f"최근 {len(diaries)}일간 기분 분포: {mood_counts}"
    final_input = f"{stats_text}\n\n[최근 일기 요약]\n{summary_text}"

    # 3. Set Status & Start Thread
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'report_status': 'processing'}}
    )

    thread = threading.Thread(target=background_generate_task, args=(app, user_id, final_input))
    thread.start()

    return jsonify({"status": "processing", "message": "리포트 분석을 시작했습니다."}), 202

@app.route('/api/report/status', methods=['GET'])
@jwt_required()
def check_report_status():
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        return jsonify({"status": "none"}), 200
        
    status = user.get('report_status', 'none')
    report = ''
    
    if status == 'completed':
        report = user.get('latest_report', '')
        
    return jsonify({"status": status, "report": report}), 200

@app.route('/api/voice/transcribe', methods=['POST'])
@jwt_required()
def transcribe_voice():
    print(f"🎤 [DEBUG] Headers: {request.headers}")
    print(f"🎤 [DEBUG] Files: {request.files}")
    if 'file' not in request.files:
        print("❌ [DEBUG] No 'file' key in request.files")
        return jsonify({"message": "No file part (DEBUG: file key missing)"}), 400
    
    file = request.files['file']
    print(f"🎤 [DEBUG] Filename: {file.filename}")
    if file.filename == '':
        print("❌ [DEBUG] Empty filename")
        return jsonify({"message": "No selected file (DEBUG: filename empty)"}), 400
        
    if file:
        try:
            filename = secure_filename(file.filename)
            # Create temp file
            # Determine suffix based on filename or default to .webm
            suffix = os.path.splitext(filename)[1]
            if not suffix: suffix = ".webm"
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                file.save(temp.name)
                temp_path = temp.name
                
            print(f"🎙️ Transcribing file: {temp_path}")
            text = voice_brain_instance.transcribe(temp_path)
            
            # Clean up
            os.remove(temp_path)
            
            # Check for auto-structure request
            auto_fill = request.form.get('auto_fill', 'false').lower() == 'true'
            
            response_data = {"text": text}
            
            if auto_fill and text and len(text) > 10:
                print(f"🧠 Auto-Filling requested for: {text[:30]}...")
                structured_data = voice_brain_instance.structure_diary_text(text)
                if structured_data:
                    response_data['structured'] = structured_data
            
            return jsonify(response_data), 200
        except Exception as e:
            print(f"❌ Transcribe Error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"message": f"Transcription failed: {str(e)}"}), 500

if __name__ == '__main__':
    # No SQL create_all() needed
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5001)
 

# Standalone Function Injected directly into app.py
def generate_analysis_reaction_standalone(user_text, mode='reaction'):
    print(f"DEBUG: generate_analysis_reaction_standalone (Local) called. Mode={mode}")
    if not user_text: return None
    import re
    import requests
    import random
    
    # 1. Sanitize
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '[EMAIL]', user_text)
    sanitized = text[:300]
    
    # 2. Prompt Switching
    if mode == 'question':
        prompt_text = (
            f"내담자의 말: \"{sanitized}\"\n\n"
            "내담자가 너무 짧고 단답형으로 대답했어. 대화를 더 깊게 이끌어내기 위해 **자연스러운 꼬리 질문**을 하나 던져줘.\n"
            "지시사항:\n"
            "1. 내담자의 말을 반복하기보다, 그 이면의 이유나 구체적인 내용을 물어봐.\n"
            "2. '그렇군요' 같은 짧은 공감 후 바로 질문해.\n"
            "3. 말투는 다정하고 궁금해하는 '해요체'를 써.\n"
            "4. 100자 이내로.\n\n"
            "꼬리 질문:"
        )
    else:
        prompt_text = (
            f"내담자의 말: \"{sanitized}\"\n\n"
            "너는 깊은 통찰력을 지닌 따뜻한 심리 상담사야. 내담자의 말을 듣고 **상황을 분석**하고 **지지하는 코멘트**를 해줘.\n"
            "지시사항:\n"
            "1. 먼저 내담자의 말 속에 숨겨진 감정이나 욕구를 분석해서 언급해줘.\n"
            "2. 그 다음, 그 감정이 타당함을 지지해주고 따뜻하게 격려해줘.\n"
            "3. 말투는 전문적이고 부드러운 '해요체'를 써.\n"
            "4. 질문은 하지 마.\n"
            "5. 150자 이내로.\n\n"
            "분석 및 리액션:"
        )
    
    try:
        payload = {
            "model": "maum-on-gemma",
            "prompt": prompt_text,
            "stream": False,
            "options": {
                "temperature": 0.7, 
                "num_predict": 180
            }
        }
        res = requests.post("http://localhost:11434/api/generate", json=payload, timeout=60)
        
        if res.status_code == 200:
            result = res.json().get('response', '').strip()
            if result.startswith('"') and result.endswith('"'):
                result = result[1:-1]
            if result: return result
            
    except Exception as e:
        print(f"❌ Standalone AI Error: {e}")
        
    # 3. Fallback
    if mode == 'question':
        fallbacks = [
            "그렇군요. 혹시 조금 더 자세히 이야기해주실 수 있나요? 궁금해요.",
            "저런, 특별한 이유가 있었는지 듣고 싶어요.",
            "짧게 말씀하시니 더 깊은 속마음이 궁금해지네요. 편하게 털어놓아주세요.",
            "그 일이 내담자님께 어떤 의미였는지 조금만 더 들려주세요."
        ]
    else:
        fallbacks = [
            "말씀하신 내용에서 깊은 고민과 진심이 느껴지네요. 잘하고 계십니다.",
            "상황을 차분히 들여다보면, 그 안에서 스스로의 성장을 발견하실 수 있을 거예요.",
            "지금 느끼시는 감정은 매우 자연스러운 반응이에요. 스스로를 믿어보세요.",
            "이야기를 들어보니, 그동안 마음속에 담아두셨던 생각들이 많으셨던 것 같아 마음이 쓰이네요."
        ]
        
    return random.choice(fallbacks)

# Late Imports at EOF to avoid Circular Dependency
try:
    from tasks import process_diary_ai, analyze_diary_logic
    from ai_brain import EmotionAnalysis
except ImportError:
    pass
