"""로그인 시도 제한 미들웨어 + JWT admin_level 클레임 패치"""

# 1. Login Rate Limiter
rate_limit_code = '''import time
import logging
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class LoginRateLimitMiddleware(MiddlewareMixin):
    """로그인 브루트포스 방어: 5회 실패 시 15분 잠금"""
    MAX_ATTEMPTS = 5
    LOCKOUT_SECONDS = 900  # 15분

    def process_request(self, request):
        if request.path.rstrip("/") != "/api/v1/auth/login":
            return None
        if request.method != "POST":
            return None

        ip = self._get_ip(request)
        cache_key = f"login_fail:{ip}"
        attempts = cache.get(cache_key, 0)

        if attempts >= self.MAX_ATTEMPTS:
            ttl = cache.ttl(cache_key) if hasattr(cache, "ttl") else self.LOCKOUT_SECONDS
            return JsonResponse(
                {"error": f"로그인 시도 초과. {ttl // 60}분 후 다시 시도해주세요."},
                status=429,
            )
        return None

    def process_response(self, request, response):
        if request.path.rstrip("/") != "/api/v1/auth/login":
            return response
        if request.method != "POST":
            return response

        ip = self._get_ip(request)
        cache_key = f"login_fail:{ip}"

        if response.status_code == 401 or response.status_code == 400:
            attempts = cache.get(cache_key, 0) + 1
            cache.set(cache_key, attempts, self.LOCKOUT_SECONDS)
            remaining = self.MAX_ATTEMPTS - attempts
            if remaining > 0:
                logger.warning(f"Login failed for IP {ip} (attempt {attempts}/{self.MAX_ATTEMPTS})")
            else:
                logger.warning(f"IP {ip} LOCKED OUT after {self.MAX_ATTEMPTS} failed attempts")
        elif response.status_code == 200:
            cache.delete(cache_key)

        return response

    def _get_ip(self, request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR", "0.0.0.0")
'''

with open("/home/ubuntu/backend_new/accounts/middleware.py", "w") as f:
    f.write(rate_limit_code)
print("LoginRateLimitMiddleware created")

# 2. Add to settings MIDDLEWARE
with open("/home/ubuntu/backend_new/config/settings.py", "r") as f:
    settings = f.read()

if "LoginRateLimitMiddleware" not in settings:
    settings = settings.replace(
        "'admin_api.middleware.AuditLogMiddleware',",
        "'admin_api.middleware.AuditLogMiddleware',\n    'accounts.middleware.LoginRateLimitMiddleware',"
    )
    with open("/home/ubuntu/backend_new/config/settings.py", "w") as f:
        f.write(settings)
    print("LoginRateLimitMiddleware added to settings")
else:
    print("Already in settings")

# 3. JWT admin_level claim - CustomTokenObtainPairSerializer
jwt_patch = '''
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT 토큰에 admin_level, center, region 정보 포함"""
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["admin_level"] = getattr(user, "admin_level", "counselor")
        token["is_staff"] = user.is_staff
        if hasattr(user, "center") and user.center:
            token["center_id"] = user.center.id
        if hasattr(user, "managed_region") and user.managed_region:
            token["managed_region_id"] = user.managed_region.id
        return token
'''

jwt_views_path = "/home/ubuntu/backend_new/accounts/jwt_custom.py"
with open(jwt_views_path, "w") as f:
    f.write(jwt_patch)
print("CustomTokenObtainPairSerializer created")

# 4. Update login URL to use custom serializer
urls_path = "/home/ubuntu/backend_new/accounts/urls.py"
with open(urls_path, "r") as f:
    urls = f.read()

if "CustomTokenObtainPairSerializer" not in urls:
    # Add import
    if "from .jwt_custom" not in urls:
        urls = "from .jwt_custom import CustomTokenObtainPairSerializer\nfrom rest_framework_simplejwt.views import TokenObtainPairView\n" + urls

    # Replace login path if it exists with simple JWT
    if "TokenObtainPairView" in urls and "CustomTokenObtainPairSerializer" not in urls:
        urls = urls.replace(
            "TokenObtainPairView.as_view()",
            "TokenObtainPairView.as_view(serializer_class=CustomTokenObtainPairSerializer)"
        )

    with open(urls_path, "w") as f:
        f.write(urls)
    print("Custom JWT login applied")
else:
    print("Already applied")

print("ALL SECURITY PATCHES DONE")
