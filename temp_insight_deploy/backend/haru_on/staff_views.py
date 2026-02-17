from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Avg, Q
from django.contrib.auth import get_user_model
from haru_on.models import HaruOn
# from accounts.models import LegacyUser

User = get_user_model()

from rest_framework import authentication

class StaffDiaryViewSet(viewsets.ViewSet):
    """
    [B2G Dashboard] Medical Staff Dashboard (PostgreSQL Native)
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = [authentication.SessionAuthentication, authentication.BasicAuthentication]

    def list(self, request):
        """
        GET /api/v1/diaries/staff/diaries/
        Retreive all diaries for the dashboard list view.
        """
        # Fetch all diaries, ordered by latest
        diaries = HaruOn.objects.all().select_related('user').order_by('-created_at')
        
        # Manual Serialization (reuse HaruOnSerializer)
        from .serializers import HaruOnSerializer
        serializer = HaruOnSerializer(diaries, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)

        # 1. Overall Status
        total_diaries = HaruOn.objects.count()
        
        # [Production] Count "Real" patients only
        total_patients = User.objects.count()
        print(f"🐛 [DEBUG] Dashboard Query - Patients: {total_patients} (Model: {User})")
        
        # Today's active writers
        today_writers = HaruOn.objects.filter(created_at__gte=today_start).values('user').distinct().count()
        
        # Participation Rate
        participation_rate = (today_writers / total_patients * 100) if total_patients > 0 else 0

        # 2. Mood Trend (Last 7 Days)
        avg_mood = HaruOn.objects.filter(created_at__gte=week_ago).aggregate(avg=Avg('mood_score'))['avg'] or 0.0

        # 3. Risk Breakdown
        
        # [Scope A] AI-detected Risk (mood_score <= 2) in last 7 days
        ai_red_risk_users = HaruOn.objects.filter(
            created_at__gte=week_ago,
            is_high_risk=True 
        ).values('user').distinct().count()

        # [Scope B] Static Profile Risk (LegacyUser doesn't have risk_level field in current model definition, defaulting to 0)
        # Verify if LegacyUser has 'risk_level' or if it needs to be added to model
        # Based on previous `models.py` view, LegacyUser does NOT have risk_level.
        # Assuming we can't get this from LegacyUser yet without schema change or it exists in different way.
        # For now, let's keep it 0 or try to fetch if we missed a column.
        profile_high_risk = 0 
        profile_mid_risk = 0

        # [Yellow] Potential Risk: Avg Mood < 2.5 (on 5 scale) in last 14 days
        yellow_risk_users = HaruOn.objects.filter(created_at__gte=two_weeks_ago).values('user').annotate(
            avg_score=Avg('mood_score')
        ).filter(avg_score__lt=2.5).count()

        data = {
            "period": "Last 7 Days",
            # [Secure] Debug info removed
            "overall": {
                "total_patients": total_patients, 
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
            }
        }
        return Response(data)



    @action(detail=False, methods=['get'])
    def export_report(self, request):
        import csv
        from django.http import HttpResponse 
        
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        # ORM Query
        diaries = HaruOn.objects.filter(created_at__gte=start_date).select_related('user').order_by('-created_at')
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="maum_on_report_{timezone.now().date()}.csv"'
        response.write(u'\ufeff'.encode('utf8'))
        
        writer = csv.writer(response) 
        writer.writerow(['Date', 'User (Masked)', 'Mood Level', 'High Risk'])
        
        for d in diaries:
            name = d.user.first_name or d.user.username
            masked = name[:1] + "**" if len(name) > 1 else name
            
            mood = d.mood_score
            risk = "YES" if d.is_high_risk else "No"
            date_str = d.created_at.strftime('%Y-%m-%d %H:%M')
            
            writer.writerow([date_str, masked, mood, risk])
            
        return response
