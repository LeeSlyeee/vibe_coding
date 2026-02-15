from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from haru_on.models import HaruOn
from haru_on.serializers import HaruOnSerializer
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import json
import os
from cryptography.fernet import Fernet

User = get_user_model()

# Encryption Setup (Same as Flask)
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

class PatientListView(views.APIView):
    """
    [Migration] PostgreSQL Implementation (Django ORM)
    Re-using Django Models mapped to PG tables.
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        # 1. Fetch Users (Django ORM over PG)
        # Exclude 'app_' system accounts and superusers
        patients = User.objects.filter(
            is_staff=False,
            is_superuser=False
        ).exclude(
            username__startswith='app_'
        ).annotate(
            diary_count=Count('diaries'),
            risk_count=Count('diaries', filter=Q(diaries__is_high_risk=True))
        )
        
        data = []
        for p in patients:
            data.append({
                'id': p.id, # PG Integer ID
                'username': p.username,
                'name': p.first_name or p.username, # Nickname fallback
                'email': p.email,
                'diary_count': p.diary_count,
                'risk_count': p.risk_count,
                'is_active': p.is_active,
                'joined_at': p.date_joined
            })
            
        return Response(data)

class PatientDetailView(views.APIView):
    """
    [Migration] PostgreSQL Detail View
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request, user_id):
        # user_id is Integer in PG
        try:
            patient = User.objects.get(id=user_id)
        except User.DoesNotExist:
            # Fallback for old clients sending string ID?
            try:
                patient = User.objects.get(username=user_id)
            except:
                return Response({'error': '환자를 찾을 수 없습니다.'}, status=404)
            
        diaries = HaruOn.objects.filter(user=patient).order_by('-created_at')
        
        diaries_data = []
        for d in diaries:
            # Decrypt if needed (Using correct columns)
            content = safe_decrypt(d.content)
            emotion_desc = safe_decrypt(d.emotion_desc)
            ai_comment = safe_decrypt(d.ai_comment)
            ai_emotion = safe_decrypt(d.ai_emotion)

            diaries_data.append({
                'id': d.id,
                'created_at': d.created_at,
                'mood_score': d.mood_score,
                'mood_level': d.mood_score,
                'content': content, 
                'ai_analysis': ai_comment, # Use column directly
                'ai_emotion': ai_emotion,
                'emotion_desc': emotion_desc,
                'is_high_risk': d.is_high_risk
            })
            
        return Response({
            'patient': {
                'id': patient.id,
                'username': patient.username,
                'name': patient.first_name,
                'email': patient.email,
                'joined_at': patient.date_joined
            },
            'diaries': diaries_data
        })

    def post(self, request, user_id):
        # Same Logic
        try:
            patient = User.objects.get(id=user_id)
        except:
             return Response({'error': 'User not found'}, status=404)

        recent_diaries = HaruOn.objects.filter(user=patient).order_by('-created_at')[:10]
        if not recent_diaries:
             return Response({'result': "데이터 부족"})
             
        scores = [d.mood_score for d in recent_diaries]
        avg = sum(scores)/len(scores)
        risk = sum(1 for s in scores if s<=2)
        
        if avg >= 4: msg = f"양호 (평균 {avg:.1f})"
        elif avg >= 2.5: msg = f"주의 (평균 {avg:.1f}, 위험 {risk}회)"
        else: msg = f"위험 (평균 {avg:.1f}, 위험 {risk}회)"
        
        return Response({'result': msg})
