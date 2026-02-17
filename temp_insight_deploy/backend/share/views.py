from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import get_user_model
from .models import ShareCode, ShareConnection
from haru_on.models import HaruOn as Diary

User = get_user_model()

# 1. 내 공유 코드 생성
class GenerateCodeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        code_obj, created = ShareCode.objects.get_or_create(user=user)
        # 만약 이미 있으면 기존 코드 반환 (변경하려면 delete 필요)
        return Response({'code': code_obj.code}, status=status.HTTP_200_OK)

# 2. 코드로 연결하기 (나는 보호자, 상대는 환자)
class ConnectView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        viewer = request.user # 나 (보호자)
        code = request.data.get('code')
        
        if not code:
            return Response({'error': 'Code is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            target_code = ShareCode.objects.get(code=code)
            sharer = target_code.user # 상대방 (환자)
            
            if sharer == viewer:
                return Response({'error': 'Cannot connect to yourself'}, status=status.HTTP_400_BAD_REQUEST)
                
            # 이미 연결되었는지 확인
            if ShareConnection.objects.filter(sharer=sharer, viewer=viewer).exists():
                return Response({'message': 'Already connected'}, status=status.HTTP_200_OK)
                
            ShareConnection.objects.create(sharer=sharer, viewer=viewer)
            return Response({'message': f'Connected to {sharer.username}'}, status=status.HTTP_201_CREATED)
            
        except ShareCode.DoesNotExist:
            return Response({'error': 'Invalid code'}, status=status.HTTP_404_NOT_FOUND)

# 3. 연결 목록 조회
class ConnectionListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        # role param: 'viewer' (내가 보는 사람 목록) or 'sharer' (나를 보는 사람 목록 = 내 보호자)
        role = request.query_params.get('role', 'viewer')
        
        if role == 'viewer':
            # 내가 보호자인 관계들 -> sharer 목록 반환
            connections = ShareConnection.objects.filter(viewer=user)
            data = []
            for conn in connections:
                data.append({
                    'id': str(conn.sharer.id),
                    'name': conn.sharer.username, # 실명 있으면 실명 사용
                    'role': 'sharer', # 상대방 역할
                    'birth_date': getattr(conn.sharer, 'birth_date', None), # 커스텀 유저 모델 필드 가정
                    'connected_at': conn.connected_at
                })
        else:
            # 내가 환자인 관계들 -> viewer 목록 반환 (내 보호자들)
            connections = ShareConnection.objects.filter(sharer=user)
            data = []
            for conn in connections:
                data.append({
                    'id': str(conn.viewer.id),
                    'name': conn.viewer.username,
                    'role': 'viewer',
                    'birth_date': getattr(conn.viewer, 'birth_date', None),
                    'connected_at': conn.connected_at
                })
                
        return Response({'data': data}, status=status.HTTP_200_OK)

# 4. 연결 해제
class DisconnectView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        target_id = request.data.get('target_id')
        
        if not target_id:
            return Response({'error': 'Target ID required'}, status=status.HTTP_400_BAD_REQUEST)
            
        # 내가 sharer일 수도, viewer일 수도 있음
        deleted_count, _ = ShareConnection.objects.filter(sharer_id=target_id, viewer=user).delete()
        if deleted_count == 0:
             deleted_count, _ = ShareConnection.objects.filter(sharer=user, viewer_id=target_id).delete()
             
        return Response({'success': True}, status=status.HTTP_200_OK)

# 5. 간단 통계 (Insights)
class SharedInsightsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, target_id):
        user = request.user
        # 권한 확인: 내가 이 사람의 보호자인가?
        if not ShareConnection.objects.filter(sharer_id=target_id, viewer=user).exists():
             return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
             
        target_user = get_object_or_404(User, id=target_id)
        
        # 최근 기분 가져오기 (Diary 모델 의존)
        recent_diaries = Diary.objects.filter(user=target_user).order_by('-date')[:7]
        moods = []
        for d in recent_diaries:
            moods.append({
                'date': str(d.date),
                'mood': d.mood_level,
                'label': d.emotion_desc
            })
            
        return Response({
            'user_name': target_user.username,
            'recent_moods': moods,
            'last_sync': timezone.now()
        })
