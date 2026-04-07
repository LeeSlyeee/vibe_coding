"""
마음온 통계/마음온도/인사이트 라우트
================================
통계 조회, 마음 온도 산정, 날씨 인사이트, PHQ-9 어세스먼트.
app.py에서 분리됨.
"""
import random
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Diary

stats_bp = Blueprint('stats', __name__)


def _get_safe_decrypt():
    """app.py의 safe_decrypt 함수를 가져온다."""
    from app import safe_decrypt
    return safe_decrypt


# ─────────────────────────────────────────────
# [Feature] 마음 온도 (Mood Temperature)
# ─────────────────────────────────────────────
def calculate_mood_temperature(user_id):
    """
    마음 온도 산정 로직 (0~100°)
    - 기분 레벨 (40%): 최근 7일 mood_level 평균 (1~5 → 0~100 매핑)
    - 기록 빈도 (20%): 최근 7일 중 기록 일수 비율
    - 수면 상태 (20%): sleep_condition 텍스트 기반 긍정/부정 분석
    - 안정성 (20%): safety_flag 및 기분 안정도 (분산 기반)
    """
    safe_decrypt = _get_safe_decrypt()
    
    recent_cutoff = datetime.utcnow() - timedelta(days=7)
    recent_diaries = Diary.query.filter(
        Diary.user_id == user_id,
        Diary.created_at >= recent_cutoff
    ).order_by(Diary.date.desc()).all()
    
    # 데이터가 없으면 기본값 36.5° (건강한 체온 비유)
    if not recent_diaries:
        return {
            "temperature": 36.5,
            "label": "측정 중",
            "description": "일기를 작성하면 마음 온도가 측정돼요!",
            "color": "#86868b",
            "diary_count": 0,
            "factors": {
                "mood_score": 0,
                "frequency_score": 0,
                "sleep_score": 0,
                "stability_score": 0
            }
        }
    
    # 1. 기분 레벨 점수 (40%)
    mood_levels = [d.mood_level or 3 for d in recent_diaries]
    avg_mood = sum(mood_levels) / len(mood_levels)
    mood_score = ((avg_mood - 1) / 4) * 100  # 1~5 → 0~100
    
    # 2. 기록 빈도 점수 (20%)
    unique_dates = set(d.date for d in recent_diaries if d.date)
    frequency_score = min((len(unique_dates) / 7) * 100, 100)
    
    # 3. 수면 상태 점수 (20%)
    sleep_positive = ["잘", "충분", "숙면", "편안", "좋"]
    sleep_negative = ["못", "불면", "뒤척", "힘들", "나쁘", "잠을 못"]
    sleep_scores = []
    for d in recent_diaries:
        sleep_text = safe_decrypt(d.sleep_condition) if d.sleep_condition else ""
        if not sleep_text:
            sleep_scores.append(50)  # 기본값
            continue
        pos = sum(1 for kw in sleep_positive if kw in sleep_text)
        neg = sum(1 for kw in sleep_negative if kw in sleep_text)
        if pos > neg:
            sleep_scores.append(80)
        elif neg > pos:
            sleep_scores.append(30)
        else:
            sleep_scores.append(50)
    sleep_score = sum(sleep_scores) / len(sleep_scores) if sleep_scores else 50
    
    # 4. 안정성 점수 (20%) - 기분 분산 + safety_flag
    if len(mood_levels) > 1:
        mean = sum(mood_levels) / len(mood_levels)
        variance = sum((x - mean) ** 2 for x in mood_levels) / len(mood_levels)
        stability_score = max(0, 100 - (variance * 25))
    else:
        stability_score = 50
    
    # safety_flag가 있으면 안정성 감점
    has_safety_flag = any(
        getattr(d, 'safety_flag', None) in [True, 'need_help', 'danger']
        for d in recent_diaries
    )
    if has_safety_flag:
        stability_score = max(0, stability_score - 30)
    
    # 종합 점수 계산 (가중 평균)
    raw_score = (
        mood_score * 0.40 +
        frequency_score * 0.20 +
        sleep_score * 0.20 +
        stability_score * 0.20
    )
    
    # 0~100 → 마음 온도 매핑 (20°~45° 범위, 36.5°가 건강한 중심)
    temperature = 20 + (raw_score / 100) * 25
    temperature = round(temperature, 1)
    
    # 라벨 및 색상 결정
    if temperature >= 40:
        label = "뜨거움 🔥"
        description = "마음이 매우 활발해요! 열정이 가득합니다."
        color = "#ff6b6b"
    elif temperature >= 37.5:
        label = "따뜻함 ☀️"
        description = "마음이 따뜻하고 안정적이에요."
        color = "#ffa726"
    elif temperature >= 35:
        label = "건강 💚"
        description = "마음이 균형 잡혀 있어요. 좋은 상태입니다!"
        color = "#66bb6a"
    elif temperature >= 30:
        label = "서늘함 🌤"
        description = "조금 차분한 상태에요. 따뜻한 활동을 해보세요."
        color = "#42a5f5"
    else:
        label = "차가움 ❄️"
        description = "마음이 많이 지쳐 있어요. 주변에 도움을 요청해보세요."
        color = "#7e57c2"
    
    return {
        "temperature": temperature,
        "label": label,
        "description": description,
        "color": color,
        "diary_count": len(recent_diaries),
        "factors": {
            "mood_score": round(mood_score, 1),
            "frequency_score": round(frequency_score, 1),
            "sleep_score": round(sleep_score, 1),
            "stability_score": round(stability_score, 1)
        }
    }


# ─────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────

@stats_bp.route('/api/mood-temperature', methods=['GET'])
@jwt_required()
def get_mood_temperature():
    """마음 온도 조회 API"""
    user_id = int(get_jwt_identity())
    user = User.query.filter_by(id=user_id).first()
    
    if not user:
        return jsonify({'msg': '사용자를 찾을 수 없습니다.'}), 404
    
    result = calculate_mood_temperature(user_id)
    return jsonify(result), 200


@stats_bp.route('/api/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    try:
        current_user_id = int(get_jwt_identity())
        diaries = Diary.query.filter_by(user_id=current_user_id).order_by(Diary.date.asc()).all()
        
        # 1. Daily Stats (Calendar uses _id, count)
        daily_stats = []
        # 2. Timeline Stats (Chart uses date, mood_level)
        timeline_stats = []
        
        for d in diaries:
            if d.date and d.mood_level:
                daily_stats.append({'_id': d.date, 'count': d.mood_level})
                timeline_stats.append({'date': d.date, 'mood_level': d.mood_level})
        
        # 3. Mood Distribution
        mood_map = {}
        for d in diaries:
            if d.mood_level and 1 <= d.mood_level <= 5:
                mood_map[d.mood_level] = mood_map.get(d.mood_level, 0) + 1
        formatted_moods = [{'_id': k, 'count': v} for k, v in mood_map.items()]

        # 4. Weather Distribution (Nested Moods)
        weather_map = {}
        for d in diaries:
            if d.weather:
                w = d.weather.strip()
                if not w:
                    continue
                if w not in weather_map:
                    weather_map[w] = {}
                if d.mood_level:
                    weather_map[w][d.mood_level] = weather_map[w].get(d.mood_level, 0) + 1
        
        formatted_weather = []
        for w, m_counts in weather_map.items():
            m_list = [{'mood': k, 'count': v} for k, v in m_counts.items()]
            formatted_weather.append({'_id': w, 'moods': m_list})

        return jsonify({
            'daily': daily_stats,
            'timeline': timeline_stats,
            'moods': formatted_moods, 
            'weather': formatted_weather
        }), 200

    except Exception as e:
        print(f"❌ [Stats Error] {e}")
        return jsonify({'daily': [], 'timeline': [], 'moods': [], 'weather': []}), 200


@stats_bp.route('/api/insight', methods=['GET'])
@jwt_required()
def get_mindset_insight():
    quotes = [
        "오늘 하루도 당신의 속도대로 나아가세요.",
        "작은 성취가 모여 큰 변화를 만듭니다.",
        "당신은 충분히 잘하고 있습니다.",
        "힘든 순간도 결국 지나갑니다. 스스로를 믿으세요.",
        "잠시 쉬어가도 괜찮습니다. 마음의 소리를 들어보세요."
    ]
    return jsonify({"content": random.choice(quotes)}), 200


@stats_bp.route('/api/weather-insight', methods=['GET'])
@jwt_required()
def get_weather_insight():
    weather = request.args.get('weather', '')
    content = "날씨가 마음에 영향을 줄 수 있어요. 따뜻한 차 한 잔 어떠세요?"
    
    if '맑음' in weather or 'Sun' in weather:
        content = "햇살처럼 밝은 하루 되세요! 산책을 추천해요."
    elif '비' in weather or 'Rain' in weather:
        content = "빗소리를 들으며 차분하게 마음을 정리해보세요."
    elif '구름' in weather or 'Cloud' in weather:
        content = "흐린 날엔 좋아하는 음악으로 기분을 전환해보세요."
        
    return jsonify({"content": content}), 200


# ─────────────────────────────────────────────
# [Assessment] PHQ-9 초기 감정 체크 결과 수신
# ─────────────────────────────────────────────
@stats_bp.route('/api/assessment', methods=['POST'])
@jwt_required()
def submit_assessment():
    """iOS AppAssessmentView에서 전송하는 PHQ-9 점수 수신"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}
    score = data.get('score', 0)

    # PHQ-9 기준 risk_level 판정
    if score >= 15:
        risk = 'high'
    elif score >= 10:
        risk = 'moderate'
    else:
        risk = 'low'

    print(f"📊 [Assessment] user={user.username}, score={score}, risk={risk}")

    return jsonify({
        'status': 'ok',
        'score': score,
        'risk_level': risk,
        'message': '감정 체크가 완료되었습니다.'
    }), 200


# ─────────────────────────────────────────────
# [Feature] 감성 무드 캘린더 (Emotional Mood Calendar)
# ─────────────────────────────────────────────

def _temperature_to_weather(temp):
    """마음 온도 → 날씨 이모지/라벨/색상 매핑."""
    if temp >= 40:
        return {'emoji': '☀️', 'label': '화창', 'color': '#ff6b6b'}
    elif temp >= 37.5:
        return {'emoji': '🌤️', 'label': '맑음', 'color': '#ffa726'}
    elif temp >= 35:
        return {'emoji': '⛅', 'label': '구름살짝', 'color': '#66bb6a'}
    elif temp >= 30:
        return {'emoji': '🌥️', 'label': '흐림', 'color': '#42a5f5'}
    else:
        return {'emoji': '🌧️', 'label': '비', 'color': '#7e57c2'}


def _calculate_daily_temperature(diaries_for_day, safe_decrypt):
    """
    특정 날짜의 일기 목록으로부터 마음 온도를 산출한다.
    calculate_mood_temperature()의 일별 축소 버전.
    """
    if not diaries_for_day:
        return None

    # 1. 기분 레벨 점수 (60%) — 일별이므로 빈도/안정성 가중치 축소
    mood_levels = [d.mood_level or 3 for d in diaries_for_day]
    avg_mood = sum(mood_levels) / len(mood_levels)
    mood_score = ((avg_mood - 1) / 4) * 100

    # 2. 수면 점수 (40%)
    sleep_positive = ["잘", "충분", "숙면", "편안", "좋"]
    sleep_negative = ["못", "불면", "뒤척", "힘들", "나쁘", "잠을 못"]
    sleep_scores = []
    for d in diaries_for_day:
        sleep_text = safe_decrypt(d.sleep_condition) if d.sleep_condition else ""
        if not sleep_text:
            sleep_scores.append(50)
            continue
        pos = sum(1 for kw in sleep_positive if kw in sleep_text)
        neg = sum(1 for kw in sleep_negative if kw in sleep_text)
        if pos > neg:
            sleep_scores.append(80)
        elif neg > pos:
            sleep_scores.append(30)
        else:
            sleep_scores.append(50)
    sleep_score = sum(sleep_scores) / len(sleep_scores) if sleep_scores else 50

    raw_score = mood_score * 0.60 + sleep_score * 0.40
    temperature = 20 + (raw_score / 100) * 25
    return round(temperature, 1)


@stats_bp.route('/api/mood-calendar', methods=['GET'])
@jwt_required()
def get_mood_calendar():
    """
    감성 무드 캘린더 API.
    지정된 year/month에 해당하는 일별 마음 온도 + 날씨 이모지를 반환한다.
    
    Query Params:
        year (int): 연도 (기본: 올해)
        month (int): 월 (기본: 이번 달)
    
    Response:
        {
            "year": 2026, "month": 3,
            "days": {
                "2026-03-01": {"mood_level": 4, "temperature": 38.2, "emoji": "🌤️", ...},
                "2026-03-02": null,  // 미기록
                ...
            }
        }
    """
    user_id = int(get_jwt_identity())
    now = datetime.utcnow()
    year = request.args.get('year', now.year, type=int)
    month = request.args.get('month', now.month, type=int)

    # 유효성 검증
    if not (2020 <= year <= 2100) or not (1 <= month <= 12):
        return jsonify({'error': '유효하지 않은 연/월입니다.'}), 400

    safe_decrypt = _get_safe_decrypt()

    # 해당 월의 일기 전부 조회
    month_start = f"{year:04d}-{month:02d}-01"
    if month == 12:
        month_end = f"{year + 1:04d}-01-01"
    else:
        month_end = f"{year:04d}-{month + 1:02d}-01"

    diaries = Diary.query.filter(
        Diary.user_id == user_id,
        Diary.date >= month_start,
        Diary.date < month_end
    ).order_by(Diary.date.asc()).all()

    # 날짜별 그룹핑
    from collections import defaultdict
    daily_map = defaultdict(list)
    for d in diaries:
        if d.date:
            daily_map[d.date].append(d)

    # 해당 월의 전체 일수
    import calendar
    _, days_in_month = calendar.monthrange(year, month)

    days = {}
    for day_num in range(1, days_in_month + 1):
        date_str = f"{year:04d}-{month:02d}-{day_num:02d}"
        day_diaries = daily_map.get(date_str, [])

        if not day_diaries:
            days[date_str] = None  # 미기록
            continue

        temp = _calculate_daily_temperature(day_diaries, safe_decrypt)
        if temp is None:
            days[date_str] = None
            continue

        weather = _temperature_to_weather(temp)
        mood_levels = [d.mood_level for d in day_diaries if d.mood_level]
        avg_mood = round(sum(mood_levels) / len(mood_levels), 1) if mood_levels else None

        days[date_str] = {
            'mood_level': avg_mood,
            'temperature': temp,
            'emoji': weather['emoji'],
            'label': weather['label'],
            'color': weather['color'],
            'diary_count': len(day_diaries),
        }

    return jsonify({
        'year': year,
        'month': month,
        'days': days,
    }), 200
