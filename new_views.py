from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import MaumOn
from .serializers import MaumOnSerializer
from rest_framework.views import APIView
import requests
import os
import threading
from cryptography.fernet import Fernet
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# [Sync] Helper function
def sync_to_vibe_coding(instance):
    def _sync():
        try:
            # 1. Decrypt/Prepare Content
            content = instance.content
            key = os.getenv('ENCRYPTION_KEY')
            if key and content and content.startswith('gAAAA'):
                try:
                    content = Fernet(key).decrypt(content.encode()).decode()
                except:
                    pass

            ar = instance.analysis_result or {}
            
            # Map mood score to string (Fallback)
            mood_map = {1:"angry", 2:"sad", 3:"neutral", 4:"calm", 5:"happy"}
            mood_str = mood_map.get(instance.mood_score, "neutral")

            # 2. Map payload (For demo, mapping to vibe_coding fields)
            payload = {
                "date": instance.created_at.strftime('%Y-%m-%d'),
                "mood": mood_str, 
                "question1": content, 
                "question2": ar.get('emotion_desc', ''),
                "question3": ar.get('emotion_meaning', ''),
                "question4": ar.get('self_talk', ''),
                "weather": ar.get('weather', ''),
                "temperature": ar.get('temperature', 20),
                "sleep_condition": ar.get('sleep_condition', 'good'),
                
                # Extra fields
                "mode": "green",
                "mood_intensity": instance.mood_score * 10,
                "symptoms": [],
                "gratitude_note": "",
                "safety_flag": instance.is_high_risk
            }

            print(f"[Sync-217] Attempting push for {payload['date']}...")

            # 3. Login
            session = requests.Session()
            login_url = "https://217.142.253.35.nip.io/api/login"
            creds = {"username": "test", "password": "password123"}
            
            resp = session.post(login_url, json=creds, verify=False, timeout=10)
            if resp.status_code == 200:
                token = resp.json().get('token')
                headers = {"Authorization": f"Bearer {token}"}
                
                # 4. Push (POST)
                push_url = "https://217.142.253.35.nip.io/api/diaries"
                res = session.post(push_url, json=payload, headers=headers, verify=False, timeout=10)
                print(f"[Sync-217] Push Result: {res.status_code} {res.text}")
            else:
                print(f"[Sync-217] Login Failed: {resp.status_code} {resp.text}")

        except Exception as e:
            print(f"[Sync-217] Error: {e}")

    # Fire and forget thread
    threading.Thread(target=_sync).start()

# [Sync] Enhanced Sync with Dynamic Password
def sync_to_vibe_coding_v2(instance, user_password):
    def _sync():
        try:
            # 1. Prepare Content
            content = instance.content
            key = os.getenv('ENCRYPTION_KEY')
            if key and content and content.startswith('gAAAA'):
                try: content = Fernet(key).decrypt(content.encode()).decode()
                except: pass

            ar = instance.analysis_result or {}
            mood_map = {1:"angry", 2:"sad", 3:"neutral", 4:"calm", 5:"happy"}
            mood_str = mood_map.get(instance.mood_score, "neutral")

            payload = {
                "date": instance.created_at.strftime('%Y-%m-%d'),
                "mood": mood_str, 
                "question1": content, 
                "question2": ar.get('emotion_desc', ''),
                "question3": ar.get('emotion_meaning', ''),
                "question4": ar.get('self_talk', ''),
                "weather": ar.get('weather', ''),
                "temperature": ar.get('temperature', 20),
                "sleep_condition": ar.get('sleep_condition', 'good'),
                "mode": "green",
                "mood_intensity": instance.mood_score * 10,
                "symptoms": [],
                "gratitude_note": "",
                "safety_flag": instance.is_high_risk
            }

            target_user = instance.user.username
            target_pass = user_password
            
            print(f"[Sync-217] Target: {target_user}, PW_Len: {len(target_pass)}")

            # 2. Register/Login Logic
            session = requests.Session()
            base_url = "https://217.142.253.35.nip.io/api"
            
            # A. Try Login
            login_resp = session.post(f"{base_url}/login", json={"username": target_user, "password": target_pass}, verify=False, timeout=5)
            
            token = None
            if login_resp.status_code == 200:
                token = login_resp.json().get('token')
            else:
                # B. Login Failed -> Try Register
                print(f"[Sync-217] Login Failed ({login_resp.status_code}), attempting Register...")
                reg_resp = session.post(f"{base_url}/register", json={"username": target_user, "password": target_pass}, verify=False, timeout=5)
                
                if reg_resp.status_code in [200, 201]:
                    # C. Register Success -> Retry Login
                     login_retry = session.post(f"{base_url}/login", json={"username": target_user, "password": target_pass}, verify=False, timeout=5)
                     if login_retry.status_code == 200:
                         token = login_retry.json().get('token')
            
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                push_res = session.post(f"{base_url}/diaries", json=payload, headers=headers, verify=False, timeout=10)
                print(f"[Sync-217] Push Result: {push_res.status_code} {push_res.text}")
            else:
                print("[Sync-217] Final Auth Failed. Cannot sync.")

        except Exception as e:
            print(f"[Sync-217] Error: {e}")

    threading.Thread(target=_sync).start()



class MaumOnViewSet(viewsets.ModelViewSet):
    serializer_class = MaumOnSerializer
    permission_classes = [permissions.AllowAny] 

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return MaumOn.objects.none()
        return MaumOn.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='date/(?P<date>[^/.]+)')
    def get_by_date(self, request, date=None):
        try:
            y, m, d = date.split('-')
            candidates = list(MaumOn.objects.filter(
                user=request.user, 
                created_at__year=y, 
                created_at__month=m, 
                created_at__day=d
            ).order_by('id'))
            
            if not candidates:
                recent = MaumOn.objects.filter(user=request.user).order_by('-created_at')[:30]
                for entry in recent:
                    if str(entry.created_at).startswith(date):
                        candidates.append(entry)
                candidates.sort(key=lambda x: x.id)

            if candidates:
                target_diary = candidates[-1] 
                if len(candidates) > 1:
                    for entry in reversed(candidates):
                        ar = entry.analysis_result or {}
                        if ar.get('weather') or ar.get('ai_comment') or ar.get('comment'):
                            target_diary = entry
                            break
                    for entry in candidates:
                        if entry.id != target_diary.id:
                            entry.delete()
                
                serializer = self.get_serializer(target_diary)
                return Response(serializer.data)
                
        except Exception:
            pass
        return Response({"detail": "Not found."}, status=404)

    def perform_create(self, serializer):
        mood_score = serializer.validated_data.get('mood_score', 5)
        is_high_risk = mood_score <= 3
        client_analysis = serializer.validated_data.get('analysis_result')
        if not client_analysis:
            client_analysis = {"comment": "AI 분석 모듈 연결 예정"}

        instance = serializer.save(
            user=self.request.user,
            is_high_risk=is_high_risk,
            analysis_result=client_analysis
        )
        # Extract Sync Password from Header
        sync_pass = self.request.META.get('HTTP_X_SYNC_PASSWORD', 'default_sync_pass_1234')
        sync_to_vibe_coding_v2(instance, sync_pass)

    def perform_update(self, serializer):
        instance = serializer.save()
        sync_pass = self.request.META.get('HTTP_X_SYNC_PASSWORD', 'default_sync_pass_1234')
        sync_to_vibe_coding_v2(instance, sync_pass)

    @action(detail=False, methods=['post'], url_path='sync_all')
    def sync_all(self, request):
        sync_pass = request.META.get('HTTP_X_SYNC_PASSWORD')
        if not sync_pass:
             print("⚠️ [Sync-All] Password Header Missing. Using fallback.")
             sync_pass = "default_sync_pass_1234" # Or require it? For now fallback.
        
        diaries = MaumOn.objects.filter(user=request.user)
        count = diaries.count()
        print(f"🔄 [Sync-All] Triggering sync for {count} diaries...")
        
        def _bulk_worker():
            for diary in diaries:
                # Reuse the logic (creates a thread inside, but we can call inner _sync if rewritten? 
                # No, sync_to_vibe_coding_v2 spawns a thread. 
                # Let's call it. It will spawn N threads. 
                # To avoid explosion, let's sleep a tiny bit?
                # Or better: Extract logic. But for now, just call it.
                sync_to_vibe_coding_v2(diary, sync_pass)
        
        # Run loop in a thread to return response immediately
        threading.Thread(target=_bulk_worker).start()
        
        return Response({"message": f"Syncing {count} diaries to Web..."})


class StatisticsView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = [] 

    def get(self, request):
        return Response({
            "timeline": [],
            "daily": [],
            "moods": [],
            "weather": [],
            "message": "통계 데이터 조회 성공 (Demo Access)"
        })
