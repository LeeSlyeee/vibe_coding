from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Avg, Q
from django.contrib.auth import get_user_model
from haru_on.models import HaruOn

User = get_user_model()

class StaffDiaryViewSet(viewsets.ViewSet):
    """
    [B2G Dashboard] Medical Staff Dashboard (PostgreSQL Native)
    Replaces MongoDB/Direct-Query logic with Django ORM for PG.
    """
    permission_classes = [permissions.AllowAny] # In production, restrict to Staff

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)

        # 1. Overall Status
        total_diaries = HaruOn.objects.count()
        total_patients = User.objects.filter(is_staff=False).exclude(username__startswith='app_').count()
        
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
            is_high_risk=True # Using mapped 'safety_flag'
        ).values('user').distinct().count()

        # [Scope B] Static Profile Risk
        # Assumes user.risk_level exists or similar. 
        # Accounts User model has 'risk_level' charfield.
        profile_high_risk = User.objects.filter(risk_level__in=['HIGH', 'severe']).count()
        profile_mid_risk = User.objects.filter(risk_level__in=['MID', 'moderate']).count()

        # [Yellow] Potential Risk: Avg Mood < 2.5 (on 5 scale) in last 14 days
        # Annotated aggregate per user
        yellow_risk_users = HaruOn.objects.filter(created_at__gte=two_weeks_ago).values('user').annotate(
            avg_score=Avg('mood_score')
        ).filter(avg_score__lt=2.5).count()

        data = {
            "period": "Last 7 Days",
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
