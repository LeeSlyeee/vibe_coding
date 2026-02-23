"""L4 2FA: 관리자 PIN 인증 시스템"""

# 1. AdminPin 모델 추가
models_path = "/home/ubuntu/backend_new/admin_api/models.py"
with open(models_path, "r") as f:
    content = f.read()

if "AdminPin" not in content:
    pin_model = '''

class AdminPin(models.Model):
    """L4 중앙 관리자 2FA PIN"""
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="admin_pin")
    pin_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "관리자 PIN"

    def set_pin(self, raw_pin):
        from django.contrib.auth.hashers import make_password
        self.pin_hash = make_password(raw_pin)
        self.save()

    def check_pin(self, raw_pin):
        from django.contrib.auth.hashers import check_password
        return check_password(raw_pin, self.pin_hash)
'''
    with open(models_path, "a") as f:
        f.write(pin_model)
    print("AdminPin model added")
else:
    print("AdminPin already exists")

# 2. 2FA 검증 API 뷰
views_path = "/home/ubuntu/backend_new/admin_api/views.py"
with open(views_path, "r") as f:
    vc = f.read()

if "TwoFactorVerifyView" not in vc:
    tfa_view = '''

class TwoFactorVerifyView(APIView):
    """L4 2FA PIN 검증"""
    permission_classes = [IsCentralAdmin]

    def post(self, request):
        pin = request.data.get("pin", "")
        user = request.user

        try:
            from .models import AdminPin
            admin_pin = AdminPin.objects.get(user=user)
            if admin_pin.check_pin(pin):
                from django.core.cache import cache
                cache.set(f"2fa_verified:{user.id}", True, 3600)  # 1시간 유효
                return Response({"verified": True, "message": "2FA 인증 성공"})
            else:
                return Response({"verified": False, "error": "PIN이 일치하지 않습니다"}, status=400)
        except AdminPin.DoesNotExist:
            # PIN 미설정 시 설정 요청
            return Response({"verified": False, "needs_setup": True, "error": "PIN 설정이 필요합니다"}, status=400)

    def put(self, request):
        """PIN 설정/변경"""
        new_pin = request.data.get("pin", "")
        if len(new_pin) < 4 or len(new_pin) > 8:
            return Response({"error": "PIN은 4~8자리 숫자여야 합니다"}, status=400)
        if not new_pin.isdigit():
            return Response({"error": "PIN은 숫자만 입력 가능합니다"}, status=400)

        from .models import AdminPin
        admin_pin, created = AdminPin.objects.get_or_create(user=request.user)
        admin_pin.set_pin(new_pin)
        return Response({"message": "PIN이 설정되었습니다", "created": created})
'''
    with open(views_path, "a") as f:
        f.write(tfa_view)
    print("TwoFactorVerifyView added")
else:
    print("TwoFactorVerifyView already exists")

# 3. 2FA 검증 미들웨어 (L4 API 접근 시 2FA 확인)
mw_path = "/home/ubuntu/backend_new/admin_api/middleware.py"
with open(mw_path, "r") as f:
    mw = f.read()

if "TwoFactorMiddleware" not in mw:
    tfa_mw = '''

class TwoFactorMiddleware(MiddlewareMixin):
    """L4 중앙 관리자 API 접근 시 2FA 인증 확인"""

    EXEMPT_PATHS = [
        "/api/v1/admin/me/",
        "/api/v1/admin/2fa/",
        "/api/v1/auth/",
    ]

    def process_request(self, request):
        if not request.path.startswith("/api/v1/admin/"):
            return None
        if any(request.path.startswith(p) for p in self.EXEMPT_PATHS):
            return None

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None
        if getattr(user, "admin_level", "") != "central_admin":
            return None

        from django.core.cache import cache
        if not cache.get(f"2fa_verified:{user.id}"):
            from django.http import JsonResponse
            return JsonResponse(
                {"error": "2FA 인증이 필요합니다", "requires_2fa": True},
                status=403,
            )
        return None
'''
    with open(mw_path, "a") as f:
        f.write(tfa_mw)
    print("TwoFactorMiddleware added")
else:
    print("TwoFactorMiddleware already exists")

# 4. URL 추가
urls_path = "/home/ubuntu/backend_new/admin_api/urls.py"
with open(urls_path, "r") as f:
    urls = f.read()

if "2fa" not in urls:
    urls = urls.replace(
        "    path('audit-logs/', views.AuditLogView.as_view(), name='audit-logs'),",
        "    path('audit-logs/', views.AuditLogView.as_view(), name='audit-logs'),\n    path('2fa/', views.TwoFactorVerifyView.as_view(), name='two-factor'),"
    )
    with open(urls_path, "w") as f:
        f.write(urls)
    print("2FA URL added")
else:
    print("2FA URL already exists")

# 5. 2FA 미들웨어를 settings에 추가
with open("/home/ubuntu/backend_new/config/settings.py", "r") as f:
    settings = f.read()

if "TwoFactorMiddleware" not in settings:
    settings = settings.replace(
        "'admin_api.middleware.AuditLogMiddleware',",
        "'admin_api.middleware.AuditLogMiddleware',\n    'admin_api.middleware.TwoFactorMiddleware',"
    )
    with open("/home/ubuntu/backend_new/config/settings.py", "w") as f:
        f.write(settings)
    print("TwoFactorMiddleware added to settings")

# 6. DB 테이블 생성
import subprocess
result = subprocess.run(
    ["bash", "-c", """cd /home/ubuntu/backend_new && source .env && PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
CREATE TABLE IF NOT EXISTS admin_api_adminpin (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES accounts_user(id) ON DELETE CASCADE,
    pin_hash VARCHAR(128) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);" """],
    capture_output=True, text=True
)
print("DB:", result.stdout.strip(), result.stderr.strip() if result.stderr else "")

print("ALL 2FA PATCHES DONE")
