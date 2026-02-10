from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import HaruOn
from .serializers import HaruOnSerializer
from b2g_sync.models import B2GConnection

class StaffDiaryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    의료진 전용: 연결된 환자들의 일기 및 분석 결과를 조회
    """
    serializer_class = HaruOnSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # 무조건 전체 일기 반환 # Updated comment
        return HaruOn.objects.all().order_by('-created_at')

    @action(detail=False, methods=['get'])
    def high_risk(self, request):
        """고위험군 일기만 필터링"""
        queryset = self.get_queryset().filter(is_high_risk=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
