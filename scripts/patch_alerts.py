import os

models_path = "/home/ubuntu/backend_new/admin_api/models.py"
with open(models_path, "r") as f:
    existing = f.read()

if "AlertNotification" not in existing:
    model_code = '''

class AlertNotification(models.Model):
    """고위험 환자 실시간 알림"""
    ALERT_TYPES = [
        ("HIGH_RISK", "고위험 환자 감지"),
        ("CRISIS", "위기 개입 필요"),
        ("NEW_PATIENT", "신규 환자 등록"),
        ("SYSTEM", "시스템 알림"),
    ]
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    patient = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="alert_patient")
    region_code = models.CharField(max_length=20, blank=True)
    center_code = models.CharField(max_length=50, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "알림"

    def __str__(self):
        return f"[{self.alert_type}] {self.title}"
'''
    with open(models_path, "a") as f:
        f.write(model_code)
    print("AlertNotification model added")
else:
    print("Already exists")

# Add alert API views
views_path = "/home/ubuntu/backend_new/admin_api/views.py"
with open(views_path, "r") as f:
    vc = f.read()

if "AlertNotificationView" not in vc:
    alert_view = '''

class AlertNotificationView(views.APIView):
    """알림 목록 조회 및 읽음 처리"""
    permission_classes = [IsCentralAdmin]

    def get(self, request):
        from .models import AlertNotification
        alerts = AlertNotification.objects.filter(is_read=False)[:50]
        data = [{
            "id": a.id,
            "type": a.alert_type,
            "title": a.title,
            "message": a.message,
            "region_code": a.region_code,
            "center_code": a.center_code,
            "created_at": a.created_at.isoformat(),
        } for a in alerts]
        return Response({"alerts": data, "unread_count": AlertNotification.objects.filter(is_read=False).count()})

    def post(self, request):
        from .models import AlertNotification
        alert_id = request.data.get("alert_id")
        if alert_id == "all":
            AlertNotification.objects.filter(is_read=False).update(is_read=True)
        elif alert_id:
            AlertNotification.objects.filter(id=alert_id).update(is_read=True)
        return Response({"status": "ok"})
'''
    with open(views_path, "a") as f:
        f.write(alert_view)
    print("AlertNotificationView added")
else:
    print("AlertNotificationView already exists")

# Add URL route
urls_path = "/home/ubuntu/backend_new/admin_api/urls.py"
with open(urls_path, "r") as f:
    uc = f.read()

if "alerts" not in uc:
    uc = uc.replace("from .views import", "from .views import AlertNotificationView,")
    # Add to urlpatterns
    uc = uc.replace("]\n", "    path('alerts/', AlertNotificationView.as_view(), name='admin-alerts'),\n]\n", 1)
    with open(urls_path, "w") as f:
        f.write(uc)
    print("URL route added")
else:
    print("URL already exists")

print("ALL DONE")
