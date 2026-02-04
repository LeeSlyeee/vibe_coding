from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_pymongo import PyMongo
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import requests # [RunPod] Added for forwarding
import os
import threading
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

@app.route('/api/v1/chat/reaction', methods=['POST'])
@app.route('/api/chat/reaction', methods=['POST']) # [Legacy Support] Match iOS Client
# @jwt_required(optional=True) -> Removed to prevent 422 on invalid token
def chat_reaction():
    # [RunPod vLLM Forwarding Logic]
    # 앱(iOS) -> 217 서버 -> RunPod (GPU) -> 217 서버 -> 앱
    
    # [Manual Auth Attempt]
    # 토큰이 유효하지 않아도(150 서버 등) 채팅 요청은 수행해야 함.
    # 따라서 데코레이터 대신 수동으로 시도하고 실패 시 무시.
    current_user_id = "anonymous_user"
    try:
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request(optional=True)
        id_found = get_jwt_identity()
        if id_found: current_user_id = id_found
    except Exception:
        pass # Ignore auth errors (Signature mismatch, etc.)
    
    data = request.json
    user_text = data.get('text', '')
    history = data.get('history', '') # Previous conversation context
    
    if not user_text:
        return jsonify({'reaction': ""}), 200

    # [Target Change] Detected Serverless Endpoint (ID: mp2w6kb0npg0tp)
    # Serverless Base: https://api.runpod.ai/v2/{ID}/openai/v1
    # [RunPod Serverless Native Mode]
    # vLLM OpenAI Proxy가 아닌 RunPod Worker 모드로 직접 실행
    # Endpoint: /runsync (동기 실행)
    target_url = "https://api.runpod.ai/v2/mp2w6kb0npg0tp/runsync"
    
    # [Auth Fix] Force valid API Key
    runpod_api_key = os.getenv('RUNPOD_API_KEY')
    
    # 2. Prompt Construction (RunPod Schema)
    # [Persona Injection]
    # AI가 단순 대화가 아닌 '일기 쓰기'를 유도하도록 강력한 페르소나 주입
    system_prompt = (
        "당신은 사용자의 하루를 기록해주는 다정한 AI 비서 '마음 온'입니다. "
        "사용자가 편안하게 하루 있었던 일과 감정을 털어놓도록 따뜻하게 질문해주세요. "
        "한 번에 너무 많은 질문을 하지 말고, 친구처럼 하나씩 물어봐주세요. "
        "사용자의 말에 공감해주고, 구체적으로 어떤 일이 있었는지 꼬리를 무는 질문을 해주세요. "
        "절대 기계적인 말투를 쓰지 마세요. 이모지를 적절히 사용하여 생동감 있게 대화하세요."
    )
    
    payload = {
        "input": {
            "prompt": f"System: {system_prompt}\n\n{history}\nUser: {user_text}\nAssistant:",
            "max_tokens": 300, # 답변 길이 여유 있게
            "temperature": 0.8 # 창의성 약간 증가 (딱딱함 방지)
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {runpod_api_key}"
    }

    try:
        reaction = ""
        print(f"🚀 [Chat] Invoking RunPod Serverless: {target_url}")
        
        # 3. Call RunPod (Timeout Extended to 300s for Queue)
        # Serverless Cold Start can take 2-3 minutes if queue is full
        try:
            resp = requests.post(target_url, json=payload, headers=headers, timeout=300)
        except requests.exceptions.Timeout:
            print("❌ [Chat] RunPod Request Timed Out (Initial POST)")
            return jsonify({'reaction': "죄송해요, 생각이 조금 길어지고 있어요. 잠시 후 다시 말 걸어주시겠어요? 🌿"}), 200
            
        if resp.status_code == 200:
            result = resp.json()
            
            # [Async Handling] runsync might return 'IN_QUEUE' if it takes too long
            if result.get("status") in ["IN_QUEUE", "IN_PROGRESS"] and "id" in result:
                job_id = result["id"]
                print(f"⏳ [Chat] Job {job_id} queued. Polling status...")
                
                # Poll for result (Max 300s)
                import time
                start_time = time.time()
                while time.time() - start_time < 300:
                    time.sleep(2)
                    status_url = f"https://api.runpod.ai/v2/mp2w6kb0npg0tp/status/{job_id}"
                    try:
                        status_resp = requests.get(status_url, headers=headers, timeout=30)
                        if status_resp.status_code == 200:
                            status_data = status_resp.json()
                            if status_data.get("status") == "COMPLETED":
                                result = status_data
                                break
                            elif status_data.get("status") == "FAILED":
                                print(f"❌ [Chat] Job Failed: {status_data}")
                                result = status_data 
                                break
                    except:
                        pass # Ignore transient polling errors
                
                # Check if still not completed
                if result.get("status") != "COMPLETED":
                     print(f"⚠️ [Chat] Job Timeout or Not Completed: {result.get('status')}")
                     # Return friendly message instead of 500 error
                     return jsonify({'reaction': "죄송해요, 지금 많은 분들의 이야기를 듣고 있어서 답변이 늦어지고 있어요. 1분 뒤에 다시 시도해주시겠어요? 🙇🏻‍♂️"}), 200
            
            # RunPod Response Format: { "status": "COMPLETED", "output": "..." }
            if "output" in result:
                # vLLM Worker Output handling
                output_data = result["output"]
                if isinstance(output_data, dict) and "text" in output_data: # vLLM standard
                     reaction = output_data["text"][0] if isinstance(output_data["text"], list) else output_data["text"]
                elif isinstance(output_data, list) and len(output_data) > 0: # Some workers return list
                     reaction = output_data[0]
                elif isinstance(output_data, str):
                     reaction = output_data
                else:
                     reaction = str(output_data) # Fallback
                
                # [Data Cleaning]
                # If output is weird JSON string like "{'reaction': '...'}", clean it.
                if "{'reaction':" in reaction or '{"reaction":' in reaction:
                    try:
                        # Simple cleanup
                        import ast
                        parsed = ast.literal_eval(reaction)
                        if isinstance(parsed, dict) and 'reaction' in parsed:
                            reaction = parsed['reaction']
                    except Exception:
                        pass # Keep original if parsing fails
                        
                # Remove quotes if wrapped
                reaction = reaction.strip().strip("'").strip('"')
            else:
                 print(f"⚠️ [Chat] Unexpected RunPod Response: {result}")
                 reaction = "(AI 응답 형식이 올바르지 않습니다)"
                 
            print(f"✅ [Chat] RunPod Success: {len(reaction)} chars")
        else:
             print(f"❌ [Chat] RunPod Fail: {resp.status_code} {resp.text}")
             reaction = "(서버 연결 실패) AI 서버가 응답하지 않습니다. (RunPod Error)"

    except Exception as e:
        print(f"❌ [Chat] Forwarding Error: {e}")
        reaction = "AI 서버와 연결할 수 없습니다. (네트워크 오류)"

    # [Async Logging] - 기존 로직 유지
    # Auth logic moved to top of function
    threading.Thread(target=background_chat_log_task, args=(app, current_user_id, user_text, reaction)).start() # [Fix] Use 'app' directly

    return jsonify({'reaction': reaction}), 200

# Helper for Threading context
def background_chat_log_task(app_instance, user_id, u_text, a_react):
    with app_instance.app_context():
        try:
            log_entry = {
                'user_id': user_id,
                'user_message': u_text,
                'ai_response': a_react,
                'created_at': datetime.utcnow()
            }
            mongo.db.chat_logs.insert_one(log_entry)
        except Exception as e:
            print(f"Log Error: {e}")

# ... (Previous code)

# Global AI (Pre-loaded for Performance)
print("💡 [Pre-Load] Initializing AI Models... (Please wait ~10s)")
try:
    from ai_brain import EmotionAnalysis
    # Create single instance for both Insight and Reports
    insight_ai = EmotionAnalysis()
    print("✅ [Pre-Load] AI Models Ready!")
except Exception as e:
    print(f"❌ [Pre-Load] Failed to load AI: {e}")
    insight_ai = None

@app.route('/api/insight', methods=['GET'])
@jwt_required()
def get_insight():
    # Use global instance directly
    if insight_ai is None:
        return jsonify({'message': "AI 서버 점검 중입니다. 잠시 후 시도해주세요."}), 503

    current_user_id = get_jwt_identity()

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
            # Decrypt event for meaningful insight
            event_text = doc.get('event', '')
            if isinstance(event_text, str):
                event_text = safe_decrypt(event_text)
            
            recent_diaries.append({
                'date': doc.get('created_at').strftime('%Y-%m-%d') if doc.get('created_at') else '',
                'mood': doc.get('mood_level', '보통'),
                'event': event_text[:50]
            })
        
        print(f"📊 [Insight] Found {len(recent_diaries)} diaries for context in range.")

        # [Fallback] If no data in range, fetch recent 5 global entries
        if not recent_diaries:
            print("📉 [Insight] No recent diaries in range. Fetching last 5 global diaries as fallback.")
            fallback_cursor = mongo.db.diaries.find({
                'user_id': current_user_id
            }).sort('created_at', -1).limit(5)
            
            # Need to reverse so they are chronological for AI context
            fallback_docs = list(fallback_cursor) # Newest first
            fallback_docs.reverse() # Oldest first
            
            for doc in fallback_docs:
                event_text = doc.get('event', '')
                if isinstance(event_text, str):
                    event_text = safe_decrypt(event_text)
                
                recent_diaries.append({
                    'date': doc.get('created_at').strftime('%Y-%m-%d') if doc.get('created_at') else '',
                    'mood': doc.get('mood_level', '보통'),
                    'event': event_text[:50]
                })
            print(f"📊 [Insight] Fallback loaded {len(recent_diaries)} diaries.")

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
             return jsonify({'message': "오늘 하루는 어떠셨나요? 편안하게 기록해보세요."}), 200
             
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
# CORS Setup - Enable for Local Development with Credentials
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:5173", 
            "http://127.0.0.1:5173",
            "http://217.142.253.35",
            "https://217.142.253.35",
            "http://217.142.253.35.nip.io",
            "https://217.142.253.35.nip.io"
        ],
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
    # Support both 'username' and 'nickname' for compatibility
    username = data.get('username') or data.get('nickname')
    password = data.get('password')
    name = data.get('name') # [New] 실명 받기
    center_code = data.get('center_code') # [New] 기관 코드 확인

    if not username or not password:
        return jsonify({"message": "Username/Nickname and password required"}), 400

    from werkzeug.security import generate_password_hash, check_password_hash
    
    user = mongo.db.users.find_one({'username': username})
    
    # [Secure Logic]
    # 1. New User -> Auto Register (with Name)
    if not user:
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        user_doc = {
            'username': username,
            'nickname': username, 
            'password_hash': hashed_password,
            'created_at': datetime.utcnow()
        }
        if name:
            user_doc['name'] = name 
        
        # [B2G] If center_code provided, bypass assessment
        if center_code:
            user_doc['center_code'] = center_code
            user_doc['assessment_completed'] = True
            user_doc['assessment_date'] = datetime.utcnow()
            user_doc['phq9_score'] = 0 
            user_doc['risk_level'] = 1
            user_doc['is_premium'] = True # [B2G] Institutions get Premium
            print(f"🏥 [B2G] User '{username}' linked to '{center_code}'. Premium Granted.")
            
        user_id = mongo.db.users.insert_one(user_doc).inserted_id
        
        user = mongo.db.users.find_one({'_id': user_id})
        print(f"🆕 [New User] '{username}' ({name}) registered and logged in.")
        
    else:
        # 2. Existing User -> STRICT Password Check
        if not check_password_hash(user['password_hash'], password):
            print(f"⛔️ [Auth Failed] Password mismatch for '{username}'")
            return jsonify({"message": "비밀번호가 일치하지 않습니다."}), 401

        # [B2G] Late Binding (Existing User Login with Code)
        # Fix: Always check if center_code is provided to upgrade
        if center_code:
             # Check if already linked or needs upgrade
             update_fields = {}
             if not user.get('assessment_completed'):
                 update_fields['assessment_completed'] = True
                 update_fields['assessment_date'] = datetime.utcnow()
             
             if not user.get('is_premium'):
                 update_fields['is_premium'] = True
                 
             if not user.get('center_code'):
                 update_fields['center_code'] = center_code
                 
             if update_fields:
                mongo.db.users.update_one({'_id': user['_id']}, {'$set': update_fields})
                print(f"🏥 [B2G] Existing User '{username}' upgraded with code '{center_code}'. Fields: {update_fields.keys()}")

    # Create Token
    access_token = create_access_token(identity=str(user['_id']))
    
    # [Check Linked Center]
    # DB에 저장된 연동 코드 확인 (linked_center_code or center_code)
    db_center_code = user.get('linked_center_code') or user.get('center_code')
    
    # [Self-Healing] DB에 코드가 없으면 150 서버에서 조회 (FIRST)
    if not db_center_code:
        try:
            from b2g_routes import recover_center_code
            recovered = recover_center_code(user.get('nickname', username))
            if recovered:
                db_center_code = recovered
                # DB Update immediately
                mongo.db.users.update_one(
                    {'_id': user['_id']}, 
                    {'$set': {
                        'linked_center_code': recovered,
                        'center_code': recovered,
                        'is_premium': True
                    }}
                )
                print(f"🏥 [B2G Recovery] Restored code '{recovered}' for '{username}'")
        except Exception as rec_err:
             print(f"⚠️ [B2G Recovery] Error: {rec_err}")

    # [B2G Sync Hook]
    # 로그인 시 150 서버(Admin)에서 데이터 Pull (SECOND - After Recovery)
    try:
        from b2g_routes import pull_from_insight_mind
        # Run Synchronously (Wait for data)
        pull_from_insight_mind(str(user['_id']), run_async=False)
    except Exception as e:
        print(f"❌ [B2G Sync] Pull Trigger Error: {e}")
    
    # [Auto-Pass Assessment]
    # 연동된 유저는 심리검사 자동 패스
    is_assessed = user.get('assessment_completed', False)
    if db_center_code and not is_assessed:
        is_assessed = True
        # DB Update for consistency
        mongo.db.users.update_one({'_id': user['_id']}, {'$set': {'assessment_completed': True, 'assessment_date': datetime.utcnow()}})
        print(f"🏥 [B2G] User '{username}' has center code '{db_center_code}'. Auto-passing assessment.")

    return jsonify({
        "access_token": access_token, 
        "user_id": str(user['_id']),
        "nickname": user.get('nickname', username),
        "name": user.get('name', ""),
        "assessment_completed": is_assessed, # Frontend uses this to show/hide modal
        "is_premium": user.get('is_premium', False), # or True if db_center_code else ...
        "linked_center_code": db_center_code
    }), 200

    user = mongo.db.users.find_one({'username': username})
    
    if not user:
         return jsonify({"message": "Invalid credentials"}), 401

    from werkzeug.security import check_password_hash
    if check_password_hash(user['password_hash'], password):
        # Use ObjectId string as identity
        access_token = create_access_token(identity=str(user['_id'])) 
        
        # Check Assessment Status
        is_assessed = user.get('assessment_completed', False)
        
        return jsonify(
            access_token=access_token, 
            username=user['username'],
            assessment_completed=is_assessed
        ), 200

    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/api/user/me', methods=['GET'])
@jwt_required()
def get_user_me():
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({"message": "User not found"}), 404
        
    return jsonify({
        "username": user.get('username'),
        "risk_level": user.get('risk_level', 1),
        "assessment_completed": user.get('assessment_completed', False),
        "is_premium": user.get('is_premium', False),
        "linked_center_code": user.get('linked_center_code') or user.get('center_code')
    }), 200

# -------------------- Payment/Premium Route --------------------
@app.route('/api/payment/upgrade', methods=['POST'])
@jwt_required()
def upgrade_premium():
    user_id = get_jwt_identity()
    # Mock Payment Success
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'is_premium': True}}
    )
    return jsonify({"message": "PREMIUM_UPGRADED", "is_premium": True}), 200


# -------------------- Assessment Route (Triage) --------------------

@app.route('/api/assessment', methods=['POST'])
@jwt_required()
def submit_assessment():
    user_id = get_jwt_identity()
    data = request.json
    score = data.get('score', 0)
    answers = data.get('answers', []) # List of scores 0-3 for 9 questions
    
    # Simple scoring (PHQ-9)
    # 0-4: Minimal (Level 1)
    # 5-9: Mild (Level 2)
    # 10-14: Moderate (Level 3)
    # 15-19: Moderately Severe (Level 4)
    # 20-27: Severe (Level 5)
    
    severity = 'Minimal'
    risk_level = 1
    
    if 5 <= score <= 9:
        severity = 'Mild'
        risk_level = 2
    elif 10 <= score <= 14:
        severity = 'Moderate'
        risk_level = 3
    elif 15 <= score <= 19:
        severity = 'Moderately Severe'
        risk_level = 4
    elif score >= 20:
        severity = 'Severe'
        risk_level = 5
        
    print(f"📋 Assessment for {user_id}: Score={score}, Severity={severity}")
    
    # Save to User
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {
            'phq9_score': score,
            'risk_level': risk_level,
            'assessment_completed': True,
            'assessment_date': datetime.utcnow()
        }}
    )
    
    return jsonify({
        'message': 'Assessment saved',
        'severity': severity,
        'risk_level': risk_level
    }), 200

# -------------------- Diary Routes --------------------

from crypto_utils import crypto_manager

# ... imports ...

# Helper for Safe Decryption
def safe_decrypt(text):
    if not isinstance(text, str) or not text: return ""
    try:
        return crypto_manager.decrypt(text)
    except Exception as e:
        print(f"❌ Safe Decrypt Error: {e}")
        return "[복호화 실패]"

# Helper to Decrypt Doc
def decrypt_doc(doc):
    if not doc: return None
    sensitive_fields = ['event', 'emotion_desc', 'emotion_meaning', 'self_talk', 'sleep_condition', 'sleep_desc', 'ai_prediction', 'ai_comment', 'mindset', 'gratitude_note', 'followup_question']
    for field in sensitive_fields:
        if field in doc and isinstance(doc[field], str):
            doc[field] = safe_decrypt(doc[field])
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
    created_at_str = data.get('created_at') or data.get('date')
    if created_at_str and created_at_str.endswith('Z'): created_at_str = created_at_str[:-1]
    created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.utcnow()

    # Map Frontend Questions to Backend Fields
    event_val = data.get('event') or data.get('question1', '')
    emotion_desc_val = data.get('emotion_desc') or data.get('question2', '')
    emotion_meaning_val = data.get('emotion_meaning') or data.get('question3', '')
    self_talk_val = data.get('self_talk') or data.get('question4', '')
    sleep_val = data.get('sleep_condition') or data.get('sleep_desc') or data.get('question_sleep', '')

    # Prepare raw data
    raw_diary = {
        'user_id': current_user_id,
        'event': event_val,
        'sleep_condition': sleep_val, # Unified field
        'sleep_desc': sleep_val,      # Legacy support
        'emotion_desc': emotion_desc_val,
        'emotion_meaning': emotion_meaning_val,
        'self_talk': self_talk_val,
        'mood_level': data.get('mood_level', 3),
        'weather': data.get('weather'),
        'temperature': data.get('temperature'),
        # New Fields for v2 UI (Green/Red Modes)
        'mode': data.get('mode', 'green'), # green or red
        'symptoms': data.get('symptoms', []), # List of strings
        'mood_intensity': data.get('mood_intensity', 0), # integer 1-10
        'gratitude_note': data.get('gratitude_note', ''),
        'mood_intensity': data.get('mood_intensity', 0), # integer 1-10
        'gratitude_note': data.get('gratitude_note', ''),
        'safety_flag': data.get('safety_flag', False),
        'medication_taken': data.get('medication_taken', False),
        
        'ai_prediction': "분석 중... (AI가 곧 답변해드려요!)",
        'ai_comment': "잠시만 기다려주세요... 🤖",
        'created_at': created_at,
        'date': created_at.strftime("%Y-%m-%d") # Essential for Calendar Matching
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
            
            # Re-encrypt client provided values
            ai_updates = {
                'ai_prediction': crypto_manager.encrypt(request_ai_pred),
                'ai_comment': crypto_manager.encrypt(request_ai_comment),
                'task_id': 'client-side'
            }
            mongo.db.diaries.update_one({'_id': result.inserted_id}, {'$set': ai_updates})
        
        # [B2G Sync Hook]
        # Web에서 작성된 일기도 Admin(150)으로 자동 전송
        try:
            from b2g_routes import sync_to_insight_mind
            # raw_diary has decrypted data + AI placeholders
            # If client provided analysis, update raw_diary to reflect it for sync
            if is_client_analyzed:
                raw_diary['ai_prediction'] = request_ai_pred
                raw_diary['ai_comment'] = request_ai_comment
            
            # Pass raw_diary (decrypted) and user_id
            sync_to_insight_mind(raw_diary, current_user_id)
        except Exception as sync_err:
            print(f"❌ [B2G Hook] Sync Failed: {sync_err}")
            
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



@app.route('/api/diaries/date/<date_str>', methods=['GET'])
@jwt_required()
def get_diary_by_date(date_str):
    current_user_id = get_jwt_identity()
    try:
        # Parse 'YYYY-MM-DD'
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
        end_date = target_date + timedelta(days=1)
        
        diary = mongo.db.diaries.find_one({
            'user_id': current_user_id,
            'created_at': {
                '$gte': target_date,
                '$lt': end_date
            }
        })
        
        if not diary:
            return jsonify({"message": "Not found"}), 404
            
        return jsonify(serialize_doc(decrypt_doc(diary))), 200
        
    except ValueError:
        return jsonify({"message": "Invalid date format"}), 400
    except Exception as e:
        print(f"Error fetching diary by date: {e}")
        return jsonify({"message": "Error"}), 500

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
    
    # [Field Mapping & Updates Construction]
    # Only update fields that are explicitly provided in the request or mapped keys.
    # If a field is NOT in data, we should NOT touch it (MongoDB keeps existing value).
    # We map frontend keys (questionX) to backend keys (event, etc.)
    
    updates = {}
    
    # 1. Text Fields (Check mapped keys)
    # logic: if 'event' is in data, use it. Else if 'question1' is in data, use it.
    # We use explicit checks to allow updates to empty strings.
    
    if 'event' in data: updates['event'] = data['event']
    elif 'question1' in data: updates['event'] = data['question1']
        
    if 'sleep_condition' in data: 
        updates['sleep_condition'] = data['sleep_condition']
        updates['sleep_desc'] = data['sleep_condition'] # Sync legacy
    elif 'sleep_desc' in data:
        updates['sleep_condition'] = data['sleep_desc']
        updates['sleep_desc'] = data['sleep_desc']
    elif 'question_sleep' in data:
        updates['sleep_condition'] = data['question_sleep']
        updates['sleep_desc'] = data['question_sleep']
        
    if 'emotion_desc' in data: updates['emotion_desc'] = data['emotion_desc']
    elif 'question2' in data: updates['emotion_desc'] = data['question2']
        
    if 'emotion_meaning' in data: updates['emotion_meaning'] = data['emotion_meaning']
    elif 'question3' in data: updates['emotion_meaning'] = data['question3']
        
    if 'self_talk' in data: updates['self_talk'] = data['self_talk']
    elif 'question4' in data: updates['self_talk'] = data['question4']

    if 'gratitude_note' in data: updates['gratitude_note'] = data['gratitude_note']

    # 2. Non-Text Fields
    if 'mood_level' in data: updates['mood_level'] = data['mood_level']
    if 'weather' in data: updates['weather'] = data['weather']
    if 'temperature' in data: updates['temperature'] = data['temperature']
    if 'mode' in data: updates['mode'] = data['mode']
    if 'symptoms' in data: updates['symptoms'] = data['symptoms']
    if 'mood_intensity' in data: updates['mood_intensity'] = data['mood_intensity']
    if 'safety_flag' in data: updates['safety_flag'] = data['safety_flag']
    if 'medication_taken' in data: updates['medication_taken'] = data['medication_taken']
    
    # 3. Always Reset AI Analysis on Update (unless client provides it)
    # Check Client-Side Analysis First
    req_ai_pred = data.get('ai_prediction', '').strip()
    req_ai_comment = data.get('ai_comment', '').strip()
    
    is_client_analyzed = (
        req_ai_pred and 
        req_ai_comment and 
        "분석 중" not in req_ai_pred and 
        "기다려주세요" not in req_ai_comment
    )
    
    task_id = None
    
    if is_client_analyzed:
        print(f"📱 [Hybrid-Update] Client provided AI analysis for {id}.")
        updates['ai_prediction'] = req_ai_pred
        updates['ai_comment'] = req_ai_comment
        updates['task_id'] = 'client-side-update'
    else:
        # Check if "re-analysis" is requested. 
        # Ideally, any content update triggers re-analysis.
        # We set placeholders.
        updates['ai_prediction'] = "재분석 중... (잠시만 기다려주세요)"
        updates['ai_comment'] = "AI가 작성된 내용을 다시 읽고 있어요... ✍️"
        # task_id will be set after thread start
    
    # 4. Encrypt specific fields before DB update
    encrypted_updates = encrypt_data(updates)
    
    # 5. Perform Update
    mongo.db.diaries.update_one({'_id': ObjectId(id)}, {'$set': encrypted_updates})
    
    # 6. Trigger Server-Side AI if needed (Using Celery for Queueing)
    if not is_client_analyzed:
        print(f"☁️ [Hybrid-Update] Triggering Server AI Re-analysis for {id}...")
        try:
            # Prepare Text Context for efficiency
            full_text = f"{updates.get('event', diary.get('event',''))} {updates.get('emotion_desc', diary.get('emotion_desc',''))}"
            
            # Dispatch to Celery Queue
            from celery_app import run_ai_analysis_task
            task = run_ai_analysis_task.apply_async(args=[str(id), full_text])
            
            mongo.db.diaries.update_one({'_id': ObjectId(id)}, {'$set': {'task_id': f"queued-{task.id}"}})
            print(f"✅ [Celery] Task {task.id} Dispatched!")
            
        except Exception as e: 
            print(f"❌ [Celery] Failed to dispatch: {e}. Falling back to Thread.")
            # Fallback to Thread
            try:
                threading.Thread(target=analyze_diary_logic, args=(id,)).start()
            except: pass
            
    # 7. Return Updated Document (Decrypted)
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

    # Check Permission
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user: return jsonify({"message": "User not found"}), 404
    
    # Allow if Risk Level >= 3 OR User is Premium
    # Allow if Risk Level >= 3 OR User is Premium OR Linked to Center
    is_linked = user.get('linked_center_code') and str(user.get('linked_center_code')).strip() != ""
    
    if user.get('risk_level', 1) < 3 and not user.get('is_premium', False) and not is_linked:
        return jsonify({"message": "보건소 및 병원 사용자 또는 유료사용자 기능입니다."}), 403

    diaries = list(mongo.db.diaries.find({'user_id': user_id}).sort('created_at', 1))
    
    from datetime import timedelta
    KST = timedelta(hours=9)
    
    stats = {
        'monthly': {},
        'moods': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        'weather': {},
        'daily_sum': {},
        'daily_count': {},
        'timeline': [],
        'symptoms': {},
        'medication_count': 0,
        'medication_total_days': 0
    }
    
    for d in diaries:
        # Full Decryption
        decrypted = decrypt_doc(d)
        
        # Extract Data from Decrypted Doc
        ai_pred_raw = decrypted.get('ai_prediction')
        user_mood = decrypted.get('mood_level')
        weather = decrypted.get('weather')
        created_at = decrypted.get('created_at')
        symptoms = decrypted.get('symptoms', [])
        medication = decrypted.get('medication_taken', False)

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
        
        # Symptoms Check
        if symptoms:
            for s in symptoms:
                stats['symptoms'][s] = stats['symptoms'].get(s, 0) + 1
                
        # Medication Check
        stats['medication_total_days'] += 1
        if medication:
            stats['medication_count'] += 1
        
        stats['timeline'].append({
            'date': date_str,
            'mood_level': mood,
            'ai_label': ai_pred_raw if ai_pred_raw else '',
            'user_mood': user_mood,
            'medication': medication
        })

    daily_moods = {}
    for k in stats['daily_sum']:
        daily_moods[k] = round(stats['daily_sum'][k] / stats['daily_count'][k])

    response_data = {
        'monthly': sorted([{'month': k, 'count': v} for k, v in stats['monthly'].items()], key=lambda x: x['month']),
        'moods': sorted([{'_id': k, 'count': v} for k, v in stats['moods'].items()], key=lambda x: x['_id']),
        'daily': sorted([{'_id': k, 'count': v} for k, v in daily_moods.items()], key=lambda x: x['_id']),
        'timeline': stats['timeline'],
        'timeline': stats['timeline'],
        'weather': [],
        'symptoms': sorted([{'name': k, 'count': v} for k, v in stats['symptoms'].items()], key=lambda x: x['count'], reverse=True),
        'medication_rate': round((stats['medication_count'] / stats['medication_total_days'] * 100), 1) if stats['medication_total_days'] > 0 else 0
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
    # Use the pre-loaded global instance (Singleton)
    global insight_ai
    return insight_ai

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
    
    # Check Permission
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user: return jsonify({"message": "User not found"}), 404
    # Allow if Risk Level >= 3 OR User is Premium OR Linked to Center
    is_linked = user.get('linked_center_code') and str(user.get('linked_center_code')).strip() != ""

    if user.get('risk_level', 1) < 3 and not user.get('is_premium', False) and not is_linked:
        return jsonify({"message": "보건소 및 병원 사용자 또는 유료사용자 기능입니다."}), 403
    
    # 1. Fetch Past Reports (Limit 5 most recent)
    cursor = mongo.db.reports.find({'user_id': user_id, 'type': 'comprehensive'}).sort('created_at', -1).limit(5)
    reports = list(cursor)
    
    # [Rollback] Require at least 2 reports for meaningful long-term analysis
    if len(reports) < 2:
        return jsonify({"message": "장기 기억 패턴을 분석하려면 최소 2개 이상의 심층 리포트가 필요해요.", "code": "NOT_ENOUGH_REPORTS"}), 400
        
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

    # Check Permission
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user: return jsonify({"message": "User not found"}), 404
    # Allow if Risk Level >= 3 OR User is Premium OR Linked to Center
    is_linked = user.get('linked_center_code') and str(user.get('linked_center_code')).strip() != ""
    
    if user.get('risk_level', 1) < 3 and not user.get('is_premium', False) and not is_linked:
        return jsonify({"message": "보건소 및 병원 사용자 또는 유료사용자 기능입니다."}), 403

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

@app.route('/api/report/chat-summary', methods=['GET'])
@jwt_required()
def get_chat_summary():
    user_id = get_jwt_identity()
    
    # Range: Last 7 Days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    # Aggregation Pipeline
    pipeline = [
        {
            "$match": {
                "user_id": user_id, 
                "created_at": {"$gte": start_date}
            }
        },
        {
            "$group": {
                "_id": None,
                "avg_stress": {"$avg": "$analysis.stress_level"},
                "emotions": {"$push": "$analysis.primary_emotion"},
                "keywords": {"$push": "$analysis.keywords"},
                "total_chats": {"$sum": 1}
            }
        }
    ]
    
    try:
        results = list(mongo.db.chat_logs.aggregate(pipeline))
        
        if not results:
            return jsonify({
                "has_data": False,
                "message": "아직 분석 데이터가 충분하지 않아요."
            }), 200
            
        data = results[0]
        
        # Process Emotions (Count Frequency)
        from collections import Counter
        raw_emotions = [e for e in data.get('emotions', []) if e and e != "분석 실패"]
        emotion_counts = Counter(raw_emotions).most_common(3) # Top 3
        
        # Process Keywords (Flatten list of lists)
        raw_keywords = []
        for k_list in data.get('keywords', []):
            if isinstance(k_list, list):
                raw_keywords.extend(k_list)
        keyword_counts = Counter(raw_keywords).most_common(5) # Top 5
        
        summary = {
            "has_data": True,
            "period": "최근 7일",
            "total_chats": data.get('total_chats', 0),
            "avg_stress": round(data.get('avg_stress', 0), 1),
            "top_emotions": [{"emotion": e[0], "count": e[1]} for e in emotion_counts],
            "top_keywords": [{"keyword": k[0], "count": k[1]} for k in keyword_counts]
        }
        
        return jsonify(summary), 200
        
    except Exception as e:
        print(f"Report API Error: {e}")
        return jsonify({"message": "Server Error"}), 500



 

# Standalone Function Injected directly into app.py
def generate_analysis_reaction_standalone(user_text, mode='reaction', history=None):
    print(f"DEBUG: generate_analysis_reaction_standalone (Local) called. Mode={mode}")
    if not user_text: return None
    import re
    import requests
    import random
    
    # 1. Sanitize
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '[EMAIL]', user_text)
    sanitized = text[:300]
    
    # 0. Keyword Risk Detection (Safety Net)
    risk_keywords = ['죽고 싶', '죽고싶', '자살', '자해', '뛰어내', '사라지고 싶', '살기 싫', '죽어버리']
    is_risk = any(k in user_text for k in risk_keywords)
    
    # 2. Prompt Switching with Risk Detection
    if mode == 'question':
        prompt_text = (
            f"내담자의 말: \"{sanitized}\"\n\n"
            "내담자가 너무 짧고 단답형으로 대답했어. 대화를 이끌어낼 꼬리 질문을 해줘.\n"
            "단, 내담자의 말에서 '죽고 싶다', '자살', '자해', '살기 싫다' 같은 **위험 신호**가 감지되면 "
            "반드시 답변 첫머리에 '[RISK]'라고 표기해줘.\n"
            "지시사항:\n"
            "1. 다정하고 궁금해하는 '해요체'.\n"
            "2. 100자 이내.\n\n"
            "답변:"
        )
    else:
        prompt_text = (
            f"내담자의 말: \"{sanitized}\"\n\n"
            "너는 깊은 통찰력을 지닌 따뜻한 심리 상담사야. 내담자의 감정을 분석하고 지지해줘.\n"
            "중요: 내담자의 말에서 '죽음', '자살 충동', '자해' 등 **위험 신호**가 명확하면 "
            "반드시 답변 첫머리에 '[RISK]'라고 적고, 즉시 전문가의 도움이 필요함을 부드럽게 권유해.\n"
            "지시사항:\n"
            "1. 전문적이고 부드러운 '해요체'.\n"
            "2. 150자 이내.\n\n"
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
        

        
    chosen_fallback = random.choice(fallbacks)
    
    if is_risk:
        return f"[RISK] {chosen_fallback}"
        
    return chosen_fallback

# Late Imports at EOF to avoid Circular Dependency
print("DEBUG: REACHING EOF BLOCK...") 
try:
    # from tasks import process_diary_ai, analyze_diary_logic
    # from ai_brain import EmotionAnalysis
    pass
except ImportError:
    pass

# --- Medication & Expansion Routes ---
try:
    from medication_routes import med_bp
    app.register_blueprint(med_bp)
    print("✅ Medication Routes Registered")
except Exception as e:
    print(f"❌ Failed to register Medication Routes: {e}")

# --- B2G Routes ---
try:
    from b2g_routes import b2g_bp
    app.register_blueprint(b2g_bp)
    print("✅ B2G Routes Registered")
except Exception as e:
    print(f"❌ Failed to register B2G Routes: {e}")

if __name__ == '__main__':
    # Use 0.0.0.0 for external access if needed, or default
    app.run(debug=False, host='0.0.0.0', port=5050, threaded=False)
