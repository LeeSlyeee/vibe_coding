from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model # [Correction] User model needed
from .models import HaruOn
from .serializers import HaruOnSerializer
# from b2g_sync.models import B2GConnection # Connection model check if needed

class StaffDiaryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    [B2G Dashboard] 의료진 전용: 실명 기반의 정밀 대시보드 API
    Endpoint: /api/staff/diaries/
    """
    serializer_class = HaruOnSerializer
    permission_classes = [permissions.AllowAny] # [Security Warning] Should be IsAdminUser in Production

    def get_queryset(self):
        # 최신순 정렬
        return HaruOn.objects.all().order_by('-created_at')

    @action(detail=False, methods=['get'])
    def high_risk(self, request):
        """[Filter] 고위험군(Red) 일기만 필터링 (기존 유지)"""
        queryset = self.get_queryset().filter(is_high_risk=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """
        [B2G Strategy] ROI Dashboard Statistics
        - Overall Status: Registered Patients, Participation
        - Risk Monitoring: Red (Immediate) / Yellow (Potential)
        """
        User = get_user_model()
        
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)

        # 1. Overall Status
        total_diaries = HaruOn.objects.count()
        
        # [Correction] Count ALL patients, not just diary writers
        total_patients = User.objects.filter(is_staff=False).count()
        
        # Today's active writers
        today_writers = HaruOn.objects.filter(created_at__gte=today_start).values('user').distinct().count()
        
        # Participation Rate
        participation_rate = (today_writers / total_patients * 100) if total_patients > 0 else 0

        # 2. Mood Trend (Last 7 Days)
        weekly_mood = HaruOn.objects.filter(created_at__gte=week_ago).aggregate(avg_score=Avg('mood_score'))
        avg_mood = weekly_mood['avg_score'] or 0.0

        # 3. Risk Breakdown (Hybrid Approach: AI + User Profile)
        
        # [Scope A] AI-detected Risk (Dynamic) in last 7 days
        ai_red_risk_users = HaruOn.objects.filter(
            created_at__gte=week_ago, 
            is_high_risk=True
        ).values('user').distinct().count()

        # [Scope B] Static Profile Risk (User.risk_level)
        profile_high_risk = User.objects.filter(is_staff=False, risk_level='HIGH').count()
        profile_mid_risk = User.objects.filter(is_staff=False, risk_level='MID').count()

        # [Yellow] Potential Risk: Avg Mood < 4.0 in last 14 days
        yellow_candidates = HaruOn.objects.filter(created_at__gte=two_weeks_ago).values('user').annotate(
            user_avg_mood=Avg('mood_score')
        ).filter(user_avg_mood__lt=4.0)
        
        yellow_risk_users = yellow_candidates.count()

        # 4. Positive Indicators
        positive_keywords = ["긍정", "행복", "감사"] # Placeholder

        data = {
            "period": "Last 7 Days",
            "overall": {
                "total_patients": total_patients, # Corrected Label
                "total_diaries": total_diaries,
                "today_participation_rate": round(participation_rate, 1),
                "weekly_avg_mood": round(avg_mood, 1)
            },
            "risk_analysis": {
                "ai_detected_high_risk": ai_red_risk_users,
                "potential_depression_risk": yellow_risk_users,
                "profile_risk_counts": {
                    "HIGH": profile_high_risk,
                    "MID": profile_mid_risk
                },
                "status": "Safe" if (ai_red_risk_users == 0 and profile_high_risk == 0) else "Warning"
            },
            "positive_indicators": {
                "top_keywords": positive_keywords
            }
        }
        return Response(data)
    @action(detail=False, methods=['get'])
    def export_report(self, request):
        """
        [B2G Strategy] Excel/CSV Export
        - Privacy: Masked Usernames
        - Content: Summary only
        - Audit: Log this action
        """
        import csv
        from django.http import HttpResponse
        
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        # [Audit] Log who requested this
        requester = request.user.username if request.user.is_authenticated else "Anonymous_Staff"
        print(f"🚨 [Audit] Report Export Requested by {requester}. Range: Last {days} days.")
        
        # Query Data
        queryset = HaruOn.objects.filter(created_at__gte=start_date).order_by('-created_at')
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="maum_on_report_{timezone.now().date()}.csv"'
        
        # Add BOM for Excel (Korean encoding)
        response.write(u'\ufeff'.encode('utf8'))
        
        writer = csv.writer(response)
        writer.writerow(['Date', 'User (Masked)', 'Mood Score', 'High Risk', 'Content (Summary)'])
        
        for diary in queryset:
            # Privacy Masking
            username = diary.user.username
            masked_name = username[:3] + "***" if len(username) > 3 else username + "***"
            
            summary = (diary.content[:30] + "...") if len(diary.content) > 30 else diary.content
            
            writer.writerow([
                diary.created_at.strftime('%Y-%m-%d %H:%M'),
                masked_name,
                diary.mood_score,
                "YES" if diary.is_high_risk else "No",
                summary.replace('\n', ' ') # Remove newlines for CSV safety
            ])
            
        return response
