"""
Phase 4-3: 보안 감사 미들웨어 + Audit Log API 패치
"""

# 1. AuditLogMiddleware 생성
middleware_code = '''import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class AuditLogMiddleware(MiddlewareMixin):
    """관리자 API 접근에 대한 감사 로그 자동 기록"""

    AUDIT_PATHS = ["/api/v1/admin/"]

    def process_response(self, request, response):
        if not any(request.path.startswith(p) for p in self.AUDIT_PATHS):
            return response

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return response

        try:
            from admin_api.models import AuditLog
            action = self._get_action(request.method)
            AuditLog.objects.create(
                user=user,
                action=action,
                target_type=self._get_target(request.path),
                target_id=0,
                ip_address=self._get_ip(request),
                detail={"method": request.method, "path": request.path, "status": response.status_code},
            )
        except Exception as e:
            logger.warning(f"AuditLog write failed: {e}")

        return response

    def _get_action(self, method):
        return {"GET": "VIEW", "POST": "CREATE", "PUT": "UPDATE", "PATCH": "UPDATE", "DELETE": "DELETE"}.get(method, "OTHER")

    def _get_target(self, path):
        parts = path.strip("/").split("/")
        for p in reversed(parts):
            if p and not p.isdigit():
                return p
        return "unknown"

    def _get_ip(self, request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR", "0.0.0.0")
'''

with open("/home/ubuntu/backend_new/admin_api/middleware.py", "w") as f:
    f.write(middleware_code)
print("Middleware created")

# 2. Add middleware to settings.py
with open("/home/ubuntu/backend_new/config/settings.py", "r") as f:
    settings = f.read()

if "AuditLogMiddleware" not in settings:
    old = "'django.middleware.clickjacking.XFrameOptionsMiddleware',"
    new = old + "\n    'admin_api.middleware.AuditLogMiddleware',"
    settings = settings.replace(old, new)
    with open("/home/ubuntu/backend_new/config/settings.py", "w") as f:
        f.write(settings)
    print("Middleware added to settings")
else:
    print("Middleware already in settings")

# 3. Add AuditLog list API view
with open("/home/ubuntu/backend_new/admin_api/views.py", "r") as f:
    views = f.read()

if "AuditLogView" not in views:
    audit_view = '''

class AuditLogView(views.APIView):
    """감사 로그 조회 API"""
    permission_classes = [IsCentralAdmin]

    def get(self, request):
        from .models import AuditLog
        days = int(request.query_params.get("days", 7))
        from django.utils import timezone
        from datetime import timedelta
        since = timezone.now() - timedelta(days=days)
        logs = AuditLog.objects.filter(timestamp__gte=since).select_related("user")[:100]
        data = [{
            "id": l.id,
            "user": l.user.username if l.user else "unknown",
            "action": l.action,
            "target_type": l.target_type,
            "ip_address": str(l.ip_address),
            "timestamp": l.timestamp.isoformat(),
            "detail": l.detail,
        } for l in logs]
        return Response({"logs": data, "total": len(data)})
'''
    # Need to avoid name collision with "views" module
    audit_view = audit_view.replace("class AuditLogView(views.APIView):", "class AuditLogView(APIView):")
    
    # Check if APIView is imported directly
    if "from rest_framework.views import APIView" not in views:
        views = views.replace("from rest_framework import views", "from rest_framework import views\nfrom rest_framework.views import APIView")

    views += audit_view
    with open("/home/ubuntu/backend_new/admin_api/views.py", "w") as f:
        f.write(views)
    print("AuditLogView added")
else:
    print("AuditLogView already exists")

# 4. Add URL route
with open("/home/ubuntu/backend_new/admin_api/urls.py", "r") as f:
    urls = f.read()

if "audit-logs" not in urls:
    urls = urls.replace(
        "    path('alerts/', views.AlertNotificationView.as_view(), name='admin-alerts'),",
        "    path('alerts/', views.AlertNotificationView.as_view(), name='admin-alerts'),\n    path('audit-logs/', views.AuditLogView.as_view(), name='audit-logs'),"
    )
    with open("/home/ubuntu/backend_new/admin_api/urls.py", "w") as f:
        f.write(urls)
    print("Audit URL added")
else:
    print("Audit URL already exists")

print("ALL DONE")
