"""
마음온 킥(Kick) 분석 모듈 — 시계열 패턴 감지기
==============================================
Phase 1: 외부 라이브러리 불필요. SQLAlchemy + 기본 Python만 사용.

분석 항목:
1. 미기록 감지 (days_since_last_entry)
2. 기록 빈도 변화 (최근 7일 vs 이전 7일)
3. 마음 온도 추세 (mood_level 연속 하락 감지)
4. 기록 시간대 분석 (새벽 기록 비율)
"""

from datetime import datetime, timedelta
from sqlalchemy import func


def analyze_timeseries(user_id, db_session, Diary, today=None):
    """
    특정 사용자의 시계열 패턴을 분석하여 위기 플래그를 산출한다.
    
    Args:
        user_id: 사용자 ID
        db_session: SQLAlchemy db.session
        Diary: Diary 모델 클래스
        today: 기준일 (테스트용, 기본값=오늘)
    
    Returns:
        dict: 시계열 분석 결과 + 플래그
    """
    if today is None:
        today = datetime.utcnow().date()
    elif isinstance(today, datetime):
        today = today.date()

    # ─── 1. 미기록 감지 ───
    last_diary = (
        db_session.query(Diary)
        .filter(Diary.user_id == user_id)
        .order_by(Diary.date.desc())
        .first()
    )

    if last_diary and last_diary.date:
        try:
            last_date = datetime.strptime(last_diary.date, '%Y-%m-%d').date()
            days_since = (today - last_date).days
        except (ValueError, TypeError):
            days_since = -1  # 파싱 실패
    else:
        days_since = -1  # 기록 없음

    inactivity_flag = days_since >= 7

    # ─── 2. 기록 빈도 변화 ───
    recent_start = (today - timedelta(days=6)).strftime('%Y-%m-%d')
    recent_end = today.strftime('%Y-%m-%d')
    prev_start = (today - timedelta(days=13)).strftime('%Y-%m-%d')
    prev_end = (today - timedelta(days=7)).strftime('%Y-%m-%d')

    recent_count = (
        db_session.query(func.count(Diary.id))
        .filter(
            Diary.user_id == user_id,
            Diary.date >= recent_start,
            Diary.date <= recent_end
        )
        .scalar() or 0
    )

    prev_count = (
        db_session.query(func.count(Diary.id))
        .filter(
            Diary.user_id == user_id,
            Diary.date >= prev_start,
            Diary.date <= prev_end
        )
        .scalar() or 0
    )

    if prev_count > 0:
        frequency_change = round(((recent_count - prev_count) / prev_count) * 100, 1)
    else:
        frequency_change = 0.0  # 이전 기록 없으면 비교 불가

    frequency_drop_flag = prev_count > 0 and frequency_change <= -50.0

    # ─── 3. 마음 온도 추세 ───
    recent_diaries = (
        db_session.query(Diary.mood_level, Diary.date)
        .filter(
            Diary.user_id == user_id,
            Diary.mood_level.isnot(None)
        )
        .order_by(Diary.date.desc())
        .limit(7)
        .all()
    )

    mood_values = [d.mood_level for d in reversed(recent_diaries) if d.mood_level is not None]

    # 연속 하락 일수 계산
    consecutive_decline = 0
    if len(mood_values) >= 2:
        for i in range(len(mood_values) - 1, 0, -1):
            if mood_values[i] < mood_values[i - 1]:
                consecutive_decline += 1
            else:
                break

    current_mood = mood_values[-1] if mood_values else None
    
    # 마음 온도를 5점 척도에서 100점 환산 (mood_level 1~5 → 20~100)
    # mood_level 1=매우나쁨(20), 2=나쁨(40), 3=보통(60), 4=좋음(80), 5=매우좋음(100)
    mood_100 = current_mood * 20 if current_mood else None
    
    decline_flag = consecutive_decline >= 3 and mood_100 is not None and mood_100 <= 40

    # ─── 4. 기록 시간대 분석 ───
    recent_with_time = (
        db_session.query(Diary.created_at)
        .filter(
            Diary.user_id == user_id,
            Diary.created_at.isnot(None),
            Diary.date >= recent_start
        )
        .all()
    )

    total_entries = len(recent_with_time)
    night_entries = 0

    for entry in recent_with_time:
        if entry.created_at and hasattr(entry.created_at, 'hour'):
            if 0 <= entry.created_at.hour <= 5:
                night_entries += 1

    night_ratio = round(night_entries / max(total_entries, 1), 2)
    night_flag = total_entries >= 3 and night_ratio >= 0.5  # 최소 3건 이상일 때만

    # ─── 종합 결과 ───
    flags = []
    if inactivity_flag:
        flags.append({
            'type': 'inactivity',
            'severity': 'high',
            'message': f'{days_since}일간 기록 없음',
            'detail': f'마지막 기록일: {last_diary.date if last_diary else "없음"}'
        })
    if decline_flag:
        flags.append({
            'type': 'mood_decline',
            'severity': 'medium',
            'message': f'마음 온도 {consecutive_decline}일 연속 하락 (현재 {mood_100}°)',
            'detail': f'최근 추이: {" → ".join(str(v * 20) + "°" for v in mood_values[-5:])}'
        })
    if frequency_drop_flag:
        flags.append({
            'type': 'frequency_drop',
            'severity': 'medium',
            'message': f'기록 빈도 {abs(frequency_change)}% 감소',
            'detail': f'최근 7일: {recent_count}건 / 이전 7일: {prev_count}건'
        })
    if night_flag:
        flags.append({
            'type': 'night_recording',
            'severity': 'low',
            'message': f'새벽 기록 비율 {int(night_ratio * 100)}%',
            'detail': f'최근 7일 중 {night_entries}/{total_entries}건이 0~5시 기록'
        })

    return {
        'user_id': user_id,
        'analysis_date': today.strftime('%Y-%m-%d'),
        'timeseries': {
            'days_since_last_entry': days_since,
            'inactivity_flag': inactivity_flag,
            'recent_7d_count': recent_count,
            'prev_7d_count': prev_count,
            'frequency_change_pct': frequency_change,
            'frequency_drop_flag': frequency_drop_flag,
            'mood_trend': {
                'values': mood_values,
                'values_100': [v * 20 for v in mood_values],
                'current_mood_100': mood_100,
                'consecutive_decline_days': consecutive_decline,
                'decline_flag': decline_flag
            },
            'night_recording': {
                'total_entries': total_entries,
                'night_entries': night_entries,
                'night_ratio': night_ratio,
                'night_flag': night_flag
            }
        },
        'flags': flags,
        'flag_count': len(flags),
        'has_critical': any(f['severity'] == 'high' for f in flags)
    }


def analyze_all_users_timeseries(db_session, User, Diary, today=None):
    """
    전체 사용자의 시계열 분석을 수행하고 플래그가 있는 사용자만 반환.
    의료진 대시보드용.
    """
    users = db_session.query(User).all()
    flagged_users = []

    for user in users:
        result = analyze_timeseries(user.id, db_session, Diary, today)
        if result['flag_count'] > 0:
            result['username'] = user.username
            result['real_name'] = user.real_name
            flagged_users.append(result)

    # 심각도 순 정렬: high 먼저, 그 다음 flag_count 높은 순
    flagged_users.sort(
        key=lambda x: (
            -int(x['has_critical']),
            -x['flag_count']
        )
    )

    return {
        'analysis_date': (today or datetime.utcnow().date()).strftime('%Y-%m-%d'),
        'total_users': len(users),
        'flagged_count': len(flagged_users),
        'flagged_users': flagged_users
    }
