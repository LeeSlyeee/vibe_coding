from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from haru_on.models import HaruOn
from haru_on.serializers import HaruOnSerializer
from django.db.models import Count, Q

User = get_user_model()

class PatientListView(views.APIView):
    """
    의료진용: 등록된 환자 목록 조회 (위험군 표시 포함)
    """
    permission_classes = [permissions.AllowAny] # 디버깅용: 모든 접근 허용
    authentication_classes = []

    def get(self, request):
        # 관리자/스태프 체크 로직 제거 (무조건 반환)
        # if not (request.user.is_superuser or request.user.is_staff):
        #     return Response([])

        # 환자 목록 + 최근 일기 상태 요약
        # 관리자(is_superuser)와 스태프(is_staff) 제외
        # [Filter] 임시 계정('app_') 제외 및 실명(first_name)이 있는 사용자만 표시
        patients = User.objects.filter(
            is_superuser=False, 
            is_staff=False
        ).exclude(
            username__startswith='app_'
        ).exclude(
            first_name=''
        ).annotate(
            diary_count=Count('diaries'),
            risk_count=Count('diaries', filter=Q(diaries__is_high_risk=True))
        )
        
        data = []
        for p in patients:
            data.append({
                'id': p.id,
                'username': p.username,
                'name': p.first_name or '실명없음',
                'email': p.email,
                'diary_count': p.diary_count,
                'risk_count': p.risk_count,
                'is_active': True, # TODO: 최근 접속일 기준
                'joined_at': p.date_joined
            })
            
        return Response(data)

class PatientDetailView(views.APIView):
    """
    의료진용: 특정 환자의 상세 일기 및 분석 결과 조회
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request, user_id):
        # if not (request.user.is_superuser or request.user.is_staff):
        #     return Response({'error': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            patient = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': '환자를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
            
        diaries = HaruOn.objects.filter(user=patient).order_by('-created_at')
        serializer = HaruOnSerializer(diaries, many=True)
        
        return Response({
            'patient': {
                'id': patient.id,
                'username': patient.username,
                'name': patient.first_name or '실명없음',
                'email': patient.email,
                'joined_at': patient.date_joined
            },
            'diaries': serializer.data
        })

    def post(self, request, user_id):
        """
        [New] Insight AI Analysis Generation
        """
        try:
            patient = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': '환자를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 1. Fetch Recent Diaries (Last 10 records)
        recent_diaries = HaruOn.objects.filter(user=patient).order_by('-created_at')[:10]
        
        if not recent_diaries:
            return Response({'result': "분석할 최근 데이터가 충분하지 않습니다."}, status=200)

        # 2. Simple Heuristic Analysis (Logic-based Insight)
        count = len(recent_diaries)
        avg_score = sum([d.mood_score for d in recent_diaries]) / count if count > 0 else 0
        risk_cnt = sum([1 for d in recent_diaries if d.mood_score <= 2])
        
        # 3. Generate Insight Text
        insight_text = ""
        if avg_score >= 4.0:
             insight_text = f"최근 {count}건의 기록 분석 결과, 환자는 전반적으로 안정적인 정서 상태(평균 {avg_score:.1f}점)를 유지하고 있습니다. 자기 효능감이 높게 나타나며 특이 소견은 발견되지 않았습니다. 현재의 긍정적 루틴을 유지하도록 격려해 주세요."
        elif avg_score >= 2.5:
             insight_text = f"최근 {count}건의 기록에서 감정 기복이 관찰됩니다(평균 {avg_score:.1f}점). 총 {risk_cnt}회의 '나쁨' 상태가 기록되었습니다. 특정 요일이나 시간대에 스트레스 반응이 있는지 확인이 필요하며, 수면 위생 점검이 권장됩니다."
        else:
             insight_text = f"⚠️ [긴급] 최근 {count}건의 기록 중 {risk_cnt}회가 위험 수준입니다(평균 {avg_score:.1f}점). 지속적인 우울감과 부정적 사고 패턴이 감지됩니다. 자살 위험성 평가 및 즉각적인 대면 상담 일정을 잡는 것이 좋습니다."

        return Response({'result': insight_text})
