"""
마음온 AI 분석 리포트 라우트
================================
비동기 AI 분석 (주간/장기), 파일 기반 리포트 저장/조회.
app.py에서 분리됨.
"""
import os
import json
import threading
from datetime import datetime
from flask import Blueprint, jsonify, request, make_response, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Diary, User

report_bp = Blueprint('report', __name__)

basedir = os.path.abspath(os.path.dirname(__file__))
REPORT_DIR = os.path.join(basedir, 'reports')
if not os.path.exists(REPORT_DIR):
    os.makedirs(REPORT_DIR)


def _get_safe_decrypt():
    """app.py의 safe_decrypt 함수를 가져온다."""
    from app import safe_decrypt
    return safe_decrypt


def _get_safe_encrypt():
    """app.py의 safe_encrypt 함수를 가져온다."""
    from app import safe_encrypt
    return safe_encrypt


def save_report(user_id, mode, data):
    try:
        filename = os.path.join(REPORT_DIR, f"{user_id}_{mode}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ [Save Report Error] {e}")


def load_report(user_id, mode):
    filename = os.path.join(REPORT_DIR, f"{user_id}_{mode}.json")
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # [Date Schema Fix] Ensure 'insight' exists for legacy files
                if 'report' in data and 'insight' not in data:
                    data['insight'] = data['report']
                return data
        except Exception:
            return None
    return None


def run_async_analysis(user_id, mode='daily'):
    """
    Background worker for AI analysis.
    mode: 'daily' (Recent 10 diaries summary), 'longterm' (30 days deep analysis)
    """
    from analysis_worker import call_llm_hybrid
    
    try:
        from app import app
        with app.app_context():
            safe_decrypt = _get_safe_decrypt()
            
            # [Fix] 사용자 이름을 조회하여 프롬프트에 명시 (LLM이 주변 인물을 내담자로 오인하는 버그 방지)
            user_display_name = "내담자"
            try:
                user_obj = User.query.get(user_id)
                if user_obj:
                    user_display_name = user_obj.real_name or user_obj.nickname or "내담자"
            except Exception as name_err:
                print(f"⚠️ [Analysis] 사용자 이름 조회 실패: {name_err}")
            
            print(f"🧵 [Analysis] Starting {mode} analysis for user {user_id} ({user_display_name})...")
            
            # Fetch Data
            limit = 30 if mode == 'longterm' else 10
            diaries = Diary.query.filter_by(user_id=user_id).order_by(Diary.date.desc()).limit(limit).all()
            
            if not diaries:
                result = {"status": "completed", "report": "분석할 데이터가 없습니다. 일기를 먼저 작성해주세요."}
                save_report(user_id, mode, result)
                return

            # Prepare Context
            context_text = ""
            for d in reversed(diaries):  # Chronological order
                content = safe_decrypt(d.event)
                emotion = safe_decrypt(d.emotion_desc)
                context_text += f"- {d.date}: {content} (감정: {emotion})\n"
            
            # Prompt Engineering (Professional Report Format)
            if mode == 'longterm':
                if len(diaries) < 3:
                     result = {"status": "completed", "report": "장기 분석을 위해서는 최소 3일 이상의 일기 데이터가 필요합니다."}
                     save_report(user_id, mode, result)
                     return
                     
                system_prompt = (
                    "당신은 20년 이상 임상 경험을 가진 저명한 감정 분석 전문가이자 데이터 분석 전문가입니다. "
                    "내담자의 지난 30일간의 일기 데이터를 정밀 분석하여, 전문적이고 깊이 있는 '월간 심층 감정 분석 보고서'를 작성해야 합니다.\n\n"
                    f"### [중요] 본 보고서의 내담자(일기를 작성한 사람)의 이름은 '{user_display_name}'입니다.\n"
                    "일기 내용이나 관계 분석에 등장하는 다른 인물(예: 친구, 가족, 동료 등)의 이름은 내담자가 아닌 '주변 인물'입니다. "
                    f"반드시 '{user_display_name}씨' 또는 '내담자'라고만 지칭하십시오. 주변 인물의 이름을 내담자로 착각하지 마십시오.\n\n"
                    "### 보고서 작성 지침:\n"
                    "1. **형식**: 줄글이 아닌, 아래의 섹션별로 명확히 구분하여 작성하십시오.\n"
                    "   - **1. [종합 소견]**: 내담자의 한 달간의 감정 상태를 3~4문장으로 요약하고, 핵심 키워드를 제시하십시오.\n"
                    "   - **2. [감정 흐름 및 패턴 분석]**: 감정의 기복, 주된 정서, 그리고 특정한 상황에서의 반응 패턴을 심층적으로 분석하십시오.\n"
                    "   - **3. [내면의 발견]**: 일기 속에 숨겨진 내담자의 무의식적 욕구, 가치관, 혹은 반복되는 갈등 요소를 통찰력 있게 짚어주십시오.\n"
                    "   - **4. [전문가 제언]**: 현재 상태에 가장 필요한 구체적인 감정 케어 방법(예: 마음챙김 명상, 자기 기록, 소통 연습 등)을 실천 가능한 형태로 제안하십시오.\n"
                    "2. **톤앤매너**: 매우 전문적이고 권위 있으면서도, 인간적인 따뜻함과 신뢰를 잃지 않는 어조를 유지하십시오.\n"
                    "3. **분량**: 각 섹션마다 충분한 근거와 상세한 서술을 포함하여 풍부하게 작성하십시오.\n"
                    "4. **주의사항**: 이 분석은 참고용이며 전문 의료 서비스를 대체하지 않습니다."
                )
            else:  # Daily / Summary
                system_prompt = (
                    "당신은 통찰력 있고 섬세한 AI 감정 분석 전문가입니다. "
                    "내담자의 최근 일기 기록(최근 10건)을 바탕으로, 현재의 감정 상태를 분석하는 '주간 감정 케어 리포트'를 작성해주세요.\n\n"
                    f"### [중요] 본 리포트의 내담자(일기를 작성한 사람)의 이름은 '{user_display_name}'입니다.\n"
                    "일기에 등장하는 다른 인물의 이름은 내담자의 '주변 인물'이지, 내담자 본인이 아닙니다. "
                    f"반드시 '{user_display_name}씨' 또는 '내담자'라고만 지칭하세요.\n\n"
                    "### 리포트 구성:\n"
                    "1. **[현재 마음 날씨]**: 최근 내담자의 감정을 날씨에 비유하여 표현하고, 그 이유를 설명하십시오.\n"
                    "2. **[주요 감정 이슈]**: 최근 반복적으로 나타나는 고민이나 감정의 원인을 분석하십시오.\n"
                    "3. **[오늘의 힐링 메시지]**: 내담자에게 가장 필요한 위로와 격려, 그리고 긍정적인 에너지를 주는 메시지를 전하십시오.\n"
                    "**작성 원칙**: 단순한 요약이 아니라, 내담자가 미처 깨닫지 못한 부분을 짚어주는 **전문적인 통찰**을 제공해야 합니다.\n"
                    "**주의사항**: 이 분석은 참고용이며 전문 의료 서비스를 대체하지 않습니다."
                )
            
            prompt = f"{system_prompt}\n\n[내담자의 최근 일기 데이터]\n{context_text}\n"

            # [킥 인사이트 주입] 시계열 + 언어 지문 + 관계 지형도
            try:
                kick_context = ""
                # Phase 1: 시계열
                from kick_analysis import analyze_timeseries
                ts = analyze_timeseries(user_id, db.session, Diary)
                if ts.get('flags'):
                    kick_context += "[시계열 패턴 감지]\n"
                    for f in ts['flags']:
                        kick_context += f"- ⚠️ {f['message']} ({f['detail']})\n"
                # Phase 2: 언어 지문
                from kick_analysis.linguistic import analyze_linguistic
                lg = analyze_linguistic(user_id, db.session, Diary, crypto_decrypt=safe_decrypt)
                if lg.get('status') == 'completed' and lg.get('linguistic', {}).get('deviation'):
                    dev = lg['linguistic']['deviation']
                    kick_context += "\n[언어 패턴 변화 (Baseline 대비)]\n"
                    key_labels = {'ttr': '어휘 다양성', 'self_focus': '자기 집중도',
                                  'negation_ratio': '부정어 비율', 'char_count': '일기 분량'}
                    for key, label in key_labels.items():
                        d = dev.get(key, {})
                        if d.get('change_pct') and abs(d['change_pct']) >= 20:
                            kick_context += f"- {label}: {d['change_pct']:+.0f}% 변화\n"
                if lg.get('flags'):
                    for f in lg['flags']:
                        kick_context += f"- ⚠️ {f['message']}\n"
                # Phase 3: 관계 지형도
                from kick_analysis.relational import analyze_relational
                rl = analyze_relational(user_id, db.session, Diary, crypto_decrypt=safe_decrypt)
                if rl.get('status') == 'completed':
                    rel_data = rl.get('relational', {})
                    total = rel_data.get('total_unique_people', 0)
                    timeline = rel_data.get('social_density_timeline', [])
                    if timeline:
                        recent = timeline[-1]
                        kick_context += f"\n[관계 지형도 — 내담자의 '주변 인물' 목록 (이 사람들은 내담자가 아님)]\n"
                        kick_context += f"- 30일간 일기에 등장한 주변 인물: 총 {total}명\n"
                        kick_context += f"- 최근 주 등장 주변 인물: {recent['unique_people']}명 ({', '.join(recent.get('people_names', [])[:5])})\n"
                if rl.get('flags'):
                    for f in rl['flags']:
                        kick_context += f"- ⚠️ {f['message']}\n"
                
                # 마음 컨디션 (Phase 1~3 교차 분석 종합)
                from kick_analysis.condition import generate_condition
                cond = generate_condition(user_id, db.session, Diary, crypto_decrypt=safe_decrypt)
                cond_data = cond.get('condition', {})
                kick_context += f"\n[마음 컨디션] {cond_data.get('icon', '')} {cond_data.get('label', '')} ({cond_data.get('score', '?')}/100)\n"
                signals = cond.get('signals', [])
                if signals and signals[0] != '현재 특이사항 없음':
                    kick_context += f"- 근거: {', '.join(signals)}\n"

                if kick_context:
                    prompt += f"\n[AI 킥 분석 인사이트 (프롬프트 참고용)]\n{kick_context}\n"
            except Exception as kick_err:
                print(f"⚠️ Kick Context Injection: {kick_err}")

            prompt += "\n[전문가 분석 보고서]"
            
            # Call LLM
            options = {"temperature": 0.5, "num_predict": 2000}
            ai_response = call_llm_hybrid(prompt, options=options)
            
            if not ai_response:
                ai_response = "AI 분석 서버 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요."
            
            # Save Result
            result = {
                "status": "completed", 
                "report": ai_response,
                "insight": ai_response,
                "timestamp": datetime.now().isoformat()
            }
            save_report(user_id, mode, result)
            print(f"✅ [Analysis] {mode} analysis completed for user {user_id}")
            
    except Exception as e:
        print(f"❌ [Analysis Error] {e}")
        error_msg = str(e)
        error_result = {
            "status": "failed", 
            "report": f"분석 중 오류가 발생했습니다: {error_msg}",
            "insight": f"분석 중 오류가 발생했습니다: {error_msg}"
        }
        save_report(user_id, mode, error_result)
        import traceback
        traceback.print_exc()


# ─────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────

@report_bp.route('/api/report/start', methods=['POST'])
@jwt_required()
def start_report():
    user_id = int(get_jwt_identity())
    
    save_report(user_id, 'daily', {
        "status": "processing", 
        "report": "분석을 준비하고 있습니다...",
        "insight": "분석을 준비하고 있습니다..."
    })
    
    threading.Thread(target=run_async_analysis, args=(user_id, 'daily')).start()
    return jsonify({"message": "종합 분석이 시작되었습니다.", "status": "processing"}), 202


@report_bp.route('/api/report/status', methods=['GET'])
@jwt_required()
def get_report_status():
    user_id = int(get_jwt_identity())
    report = load_report(user_id, 'daily')
    
    response_data = None
    if report:
        response_data = report
    else:
        last_diary = Diary.query.filter_by(user_id=user_id).order_by(Diary.date.desc()).first()
        if not last_diary:
             response_data = {"status": "completed", "report": "아직 기록이 없어요. 괜찮아요, 편안할 때 한마디 남겨보세요. 🌿", "insight": "아직 기록이 없어요. 괜찮아요, 편안할 때 한마디 남겨보세요. 🌿"}
        else:
             response_data = {"status": "processing", "report": "분석을 준비하고 있습니다...", "insight": "분석을 준비하고 있습니다..."}
    
    resp = make_response(jsonify(response_data), 200)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@report_bp.route('/api/report/longterm/start', methods=['POST'])
@jwt_required()
def start_longterm_report():
    user_id = int(get_jwt_identity())
    
    save_report(user_id, 'longterm', {
        "status": "processing", 
        "report": "심층 분석을 수행 중입니다. (약 1~2분 소요)",
        "insight": "심층 분석을 수행 중입니다. (약 1~2분 소요)"
    })
    
    threading.Thread(target=run_async_analysis, args=(user_id, 'longterm')).start()
    return jsonify({"message": "장기 심층 분석이 시작되었습니다.", "status": "processing"}), 202


@report_bp.route('/api/report/longterm/status', methods=['GET'])
@jwt_required()
def get_longterm_report_status():
    user_id = int(get_jwt_identity())
    report = load_report(user_id, 'longterm')
    
    response_data = None
    if report:
        response_data = report
    else:
        response_data = {"status": "processing", "report": "심층 분석을 수행 중입니다. (약 1~2분 소요)", "insight": "심층 분석을 수행 중입니다. (약 1~2분 소요)"}

    resp = make_response(jsonify(response_data), 200)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp
