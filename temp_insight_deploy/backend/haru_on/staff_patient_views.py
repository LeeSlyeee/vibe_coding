from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from haru_on.models import HaruOn
from django.db.models import Count, Q
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
import os
from cryptography.fernet import Fernet
import json

User = get_user_model()

# Encryption Setup
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
cipher_suite = Fernet(ENCRYPTION_KEY) if ENCRYPTION_KEY else None

def safe_decrypt(text):
    if not text or not cipher_suite:
        return text
    try:
        if isinstance(text, str):
            text = text.encode()
        return cipher_suite.decrypt(text).decode()
    except Exception:
        return text

# from accounts.models import LegacyUser

class PatientListView(views.APIView):
    """
    [PostgreSQL Native] Patient List View
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # 1. Fetch Users (Active User Model)
        # Exclude admin users (is_staff=False) to show only patients
        patients = User.objects.filter(is_staff=False).annotate(
            diary_count=Count('diaries'),
            risk_count=Count('diaries', filter=Q(diaries__is_high_risk=True))
        ).order_by('-date_joined')
        
        data = []
        for p in patients:
            # [Fix] Add Center Info
            center_name = p.center.name if p.center else None
            center_code = getattr(p.center, 'code', None) if p.center else None
            
            data.append({
                'id': p.id,
                'username': p.username,
                'name': p.first_name or p.username, # User has first_name/last_name
                'email': p.email,
                'diary_count': p.diary_count,
                'risk_count': p.risk_count,
                'center_name': center_name,
                'center_code': center_code,
                'is_active': p.is_active,
                'joined_at': p.date_joined
            })
            
        return Response(data)

class PatientDetailView(views.APIView):
    """
    [PostgreSQL Native] Patient Detail View
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @method_decorator(never_cache)
    @method_decorator(never_cache)
    def get(self, request, username):
        # username is String
        print(f"🔍 [PatientDetail] Requested Username: {username}")
        try:
            patient = User.objects.get(username=username)
            print(f"🔍 [PatientDetail] Found User: {patient.username} (ID: {patient.id}, Email: {patient.email})")
            
            # [Fix] Admin Protection: Do not show staff detail view
            if patient.is_staff:
                return Response({'error': '관리자 계정의 상세 정보는 조회할 수 없습니다.'}, status=403)
                
        except User.DoesNotExist:
            return Response({'error': '환자를 찾을 수 없습니다.'}, status=404)
            
        diaries = HaruOn.objects.filter(user=patient).order_by('-created_at')
        
        diaries_data = []
        for d in diaries:
            # Check if decryption is needed
            content = safe_decrypt(d.content)
            emotion_desc = safe_decrypt(d.emotion_desc) or ''
            ai_comment = safe_decrypt(d.ai_comment) or ''
            ai_emotion = safe_decrypt(d.ai_emotion) or ''
            
            emotion_meaning = safe_decrypt(d.emotion_meaning) or ''
            self_talk = safe_decrypt(d.self_talk) or ''
            sleep_condition = safe_decrypt(d.sleep_condition) or ''
            gratitude_note = safe_decrypt(d.gratitude_note) or ''

            diaries_data.append({
                'id': d.id,
                'created_at': d.created_at,
                'mood_score': d.mood_score,
                'mood_level': d.mood_score,
                'content': content, 
                'ai_analysis': ai_comment, 
                'ai_emotion': ai_emotion,
                'emotion_desc': emotion_desc,
                'emotion_meaning': emotion_meaning,
                'self_talk': self_talk,
                'is_high_risk': d.is_high_risk,
                'weather': d.weather,
                # 'temperature': d.temperature, # Removed
                'sleep_condition': sleep_condition,
                'gratitude_note': gratitude_note,
                'mode': d.mode,
                'analysis_result': d.analysis_result # Pass raw JSON for frontend fallback
            })
            
        return Response({
            'patient': {
                'id': patient.id,
                'username': patient.username,
                'name': patient.first_name or patient.username, 
                'email': patient.email,
                'joined_at': patient.date_joined
            },
            'diaries': diaries_data
        })

    def post(self, request, username):
        try:
            patient = User.objects.get(username=username)
        except User.DoesNotExist:
             return Response({'error': 'User not found'}, status=404)

        recent_diaries = HaruOn.objects.filter(user=patient).order_by('-created_at')[:10]
        if not recent_diaries:
             return Response({'result': "데이터 부족"})
             
        scores = [d.mood_score for d in recent_diaries if d.mood_score is not None]
        if not scores:
             return Response({'result': "데이터 부족 (점수 없음)"})

        avg = sum(scores)/len(scores)
        risk = sum(1 for s in scores if s<=2)
        
        if avg >= 4: msg = f"양호 (평균 {avg:.1f})"
        elif avg >= 2.5: msg = f"주의 (평균 {avg:.1f}, 위험 {risk}회)"
        else: msg = f"위험 (평균 {avg:.1f}, 위험 {risk}회)"
        
        return Response({'result': msg})
