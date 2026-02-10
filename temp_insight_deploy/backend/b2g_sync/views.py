from rest_framework import viewsets, permissions, status, views
from rest_framework.response import Response
from .models import B2GConnection
from .serializers import B2GConnectionSerializer
from centers.models import Center, VerificationCode
from django.db import transaction

class ConnectionRequestView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        center_id = request.data.get('center_id')
        verification_code_id = request.data.get('verification_code_id') # 프론트에서 전달해야 함

        if not center_id:
            return Response({'error': '센터 ID가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 이미 연동되어 있는지 확인
        if B2GConnection.objects.filter(user=request.user, center_id=center_id, status='ACTIVE').exists():
             return Response({'error': '이미 연동된 기관입니다.'}, status=status.HTTP_409_CONFLICT)

        try:
            with transaction.atomic():
                # 1. 연동 생성
                connection = B2GConnection.objects.create(
                    user=request.user,
                    center_id=center_id,
                    status=B2GConnection.Status.ACTIVE
                )
                
                # 2. 일회용 코드 사용 처리
                # 코드 ID가 있으면 처리, 없으면(구버전 or 테스트) 패스할 수도 있지만 엄격하게 하려면 필수
                if verification_code_id:
                    v_code = VerificationCode.objects.get(id=verification_code_id)
                    v_code.is_used = True
                    v_code.used_by = request.user
                    v_code.used_at = connection.consented_at
                    v_code.save()

                serializer = B2GConnectionSerializer(connection)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except VerificationCode.DoesNotExist:
             return Response({'error': '유효하지 않은 인증 코드 ID입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MyConnectionsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        connections = B2GConnection.objects.filter(user=request.user)
        serializer = B2GConnectionSerializer(connections, many=True)
        return Response(serializer.data)
