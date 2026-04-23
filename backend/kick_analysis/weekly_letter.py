import json
import requests
from datetime import datetime, timedelta
from sqlalchemy import desc

from kick_analysis import analyze_timeseries
from kick_analysis.linguistic import analyze_linguistic
from kick_analysis.relational import analyze_relational
from models import WeeklyLetter

def generate_weekly_letter_for_user(user_id, db_session, User, Diary, crypto_decrypt=None, target_date=None):
    """
    특정 사용자의 지난 1주일 데이터를 기반으로 AI 주간 편지를 생성하여 DB에 저장.
    """
    if target_date is None:
        target_date = datetime.utcnow().date()
        
    start_date = target_date - timedelta(days=7)
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = target_date.strftime('%Y-%m-%d')
    
    # 이미 생성된 주간 편지가 있는지 확인 (중복 방지)
    existing_letter = db_session.query(WeeklyLetter).filter_by(
        user_id=user_id, start_date=start_str, end_date=end_str
    ).first()
    
    if existing_letter:
        return {"status": "skipped", "message": f"Letter for {start_str}~{end_str} already exists."}
    
    # 일기 데이터 개수 확인
    recent_diaries = db_session.query(Diary).filter(
        Diary.user_id == user_id,
        Diary.date >= start_str,
        Diary.date <= end_str
    ).count()
    
    if recent_diaries == 0:
        return {"status": "skipped", "message": "No diaries found in this week."}

    # 1. 시계열 분석 요약
    ts = analyze_timeseries(user_id, db_session, Diary)
    ts_summary = []
    for f in ts.get('flags', []):
        ts_summary.append(f)
        
    # 2. 언어 지문 요약
    lg = analyze_linguistic(user_id, db_session, Diary, crypto_decrypt=crypto_decrypt)
    lg_summary = []
    if lg.get('status') == 'completed':
        dev = lg.get('linguistic', {}).get('deviation', {})
        labels = {'ttr': '어휘 다양성', 'self_focus': '자기 집중도',
                  'char_count': '일기 분량', 'negation_ratio': '부정어 비율'}
        for key, label in labels.items():
            d = dev.get(key, {})
            if d.get('change_pct') and abs(d['change_pct']) >= 20:
                lg_summary.append(f"{label} {d['change_pct']:+.0f}% 변화")
                
    # 3. 관계 지형도 요약
    rl = analyze_relational(user_id, db_session, Diary, crypto_decrypt=crypto_decrypt, skip_llm_ner=True)
    rl_summary = []
    if rl.get('status') == 'completed':
        rel = rl.get('relational', {})
        timeline = rel.get('social_density_timeline', [])
        if timeline:
            recent_week = timeline[-1]
            names = recent_week.get('people_names', [])
            if names:
                rl_summary.append(f"등장 인물: {', '.join(names)}")
                for p, emo_info in recent_week.get('people_emotions', {}).items():
                    val = emo_info.get('valence')
                    if val == 'negative':
                        rl_summary.append(f"[{p}]와의 관계에서 주로 부정적 감정 보임")
                    elif val == 'positive':
                        rl_summary.append(f"[{p}]와의 관계에서 주로 긍정적 감정 보임")
                        
    # 프롬프트 생성
    prompt = f"""
당신은 마음온의 따뜻한 AI 상담사입니다. 사용자의 지난 한 주간의 무의식적인 패턴을 읽고, 다정한 어조로 주간 편지를 써주세요.
분석적인 보고서 형식이 아님에 주의하세요. 진짜 사람이 써준 손편지처럼 진심이 담겨야 합니다.

[지난 1주의 분석 데이터]
1. 시계열(기록 및 수면): {', '.join([f['message'] for f in ts_summary]) if ts_summary else '특이사항 없음'}
2. 언어 습관 변화: {', '.join(lg_summary) if lg_summary else '큰 변화 없음'}
3. 등장 인물과 관계: {', '.join(rl_summary) if rl_summary else '타인 언급이 적었음'}

위 데이터를 바탕으로:
- 인삿말
- 지난 일주일 간의 마음 날씨와 관계에서의 특징 짚어주기 (예: "이번 주에는 팀장님과의 일로 일기 분량이 짧아질 만큼 스트레스가 컸네요. 하지만 옆에서 강아지가 큰 위로가 되는 게 보였어요.")
- 따뜻한 위로와 다음 주를 위한 가벼운 제안
- 작성자: 마음온 AI 드림

반드시 이 형식에 맞춰 편지 본문 텍스트만 출력하세요.
"""
    
    # LLM 호출 (Ollama)
    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma4:2b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.5, "num_predict": 500}
            },
            timeout=60
        )
        if res.status_code == 200:
            letter_content = res.json().get('response', '').strip()
            
            # DB 저장
            new_letter = WeeklyLetter(
                user_id=user_id,
                start_date=start_str,
                end_date=end_str,
                title=f"{start_date.strftime('%m월 %d일')} ~ {target_date.strftime('%m월 %d일')} 마음 편지",
                content=letter_content
            )
            db_session.add(new_letter)
            db_session.commit()
            
            # 푸시 알림 발송 (편지 도착 알림)
            try:
                from push_service import send_push, is_push_available
                if is_push_available():
                    user = db_session.query(User).filter_by(id=user_id).first()
                    if user and getattr(user, 'fcm_token', None):
                        send_push(
                            fcm_token=user.fcm_token,
                            title="💌 마음온 주간 편지가 도착했어요",
                            body="이번 한 주의 마음을 담은 편지가 왔어요. 지금 읽어보세요!",
                            data={
                                "type": "weekly_letter",
                                "letter_id": str(new_letter.id),
                            },
                            apns_token=getattr(user, 'apns_token', None),
                        )
                        print(f"📮 주간 편지 푸시 발송 완료: user={user_id}, letter={new_letter.id}")
            except Exception as push_err:
                print(f"⚠️ 주간 편지 푸시 발송 실패 (편지 생성은 정상): {push_err}")
            
            return {"status": "success", "letter_id": new_letter.id}
        else:
            return {"status": "error", "message": f"LLM error: {res.status_code}"}
    except Exception as e:
        print(f"⚠️ Weekly Letter Generation LLM Failed: {e}")
        return {"status": "error", "message": str(e)}

def generate_all_weekly_letters(db_session, User, Diary, crypto_decrypt=None):
    """
    모든 사용자에 대해 이번 주 주간 편지 배치 생성 (Cron 작업용).
    """
    users = db_session.query(User).all()
    results = []
    
    for user in users:
        res = generate_weekly_letter_for_user(
            user.id, db_session, User, Diary, crypto_decrypt=crypto_decrypt
        )
        results.append({"user_id": user.id, "result": res})
        
    return results

def process_all_users_weekly_letter():
    """
    Fetches all distinct user_ids from diaries (over last 7 days) and generates weekly letters for them.
    Returns dict of success/failures.
    """
    from app import app
    from models import db, User, Diary
    from datetime import datetime, timedelta
    
    with app.app_context():
        end_date_time = datetime.utcnow()
        start_date_time = end_date_time - timedelta(days=7)
        
        start_str = start_date_time.strftime('%Y-%m-%d')
        end_str = end_date_time.strftime('%Y-%m-%d')
        
        # SQL에서 7일 내 일기를 쓴 유저 ID 조회
        recent_diaries = db.session.query(Diary.user_id).filter(
            Diary.date >= start_str, Diary.date <= end_str
        ).distinct().all()
        
        user_ids = [d[0] for d in recent_diaries]
        
        results = {"success": 0, "failed": 0, "errors": []}
        
        for user_id in user_ids:
            print(f"🔄 Processing letter for user {user_id}...")
            try:
                # 앱이 crypto_manager를 주입한다고 가정하거나 그대로 패스.
                # (여기서는 기본 복호화 없이 실행하거나 app.crypto_manager 사용)
                from crypto_utils import crypto_manager
                result = generate_weekly_letter_for_user(
                    user_id=user_id, 
                    db_session=db.session, 
                    User=User, 
                    Diary=Diary, 
                    crypto_decrypt=crypto_manager.decrypt if hasattr(crypto_manager, 'decrypt') else None,
                    target_date=end_date_time.date()
                )
                
                if result.get("status") == "error":
                     results["failed"] += 1
                     results["errors"].append({"user_id": user_id, "error": result["message"]})
                     print(f"❌ User {user_id} failed: {result['message']}")
                else:
                     results["success"] += 1
                     print(f"✅ User {user_id} success: {result.get('status')}")
                     
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"user_id": user_id, "error": str(e)})
                print(f"❌ User {user_id} exception: {e}")
                
        return results

