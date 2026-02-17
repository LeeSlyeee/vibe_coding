from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Haru-On API",
      default_version='v1',
      description="하루-ON 보건소 연동 시스템 API 문서",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@haruon.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

from haru_on.staff_patient_views import PatientListView, PatientDetailView
from haru_on.staff_views import StaffDiaryViewSet # [New] B2G Dashboard
from haru_on.b2g_views import CenterVerifyView, CenterConnectView # [Fix] B2G API
from haru_on.views import StatisticsView, HaruOnViewSet
from accounts.legacy_views import LegacyLoginView, UserMeView

urlpatterns = [
    # [Emergency Bypass] 403 방지를 위한 최우선 경로 매핑 (Router 우회)
    # 0. B2G Verification (Legacy Flask API Porting)
    path("api/centers/verify-code/", CenterVerifyView.as_view()),
    path("api/v1/centers/verify-code/", CenterVerifyView.as_view()), # Alias
    path("api/b2g_sync/connect/", CenterConnectView.as_view()),
    path("api/v1/b2g_sync/connect/", CenterConnectView.as_view()), # Alias

    # 1. Patient List & Detail (Fix 404)
    path("api/v1/diaries/staff/patients/<str:username>/", PatientDetailView.as_view()),
    path("api/v1/diaries/staff/patients/", PatientListView.as_view()),
    
    # [Fix] Add simpler alias for frontend compatibility
    path("api/staff/patients/", PatientListView.as_view()),
    path("api/staff/patients/<str:username>/", PatientDetailView.as_view()),

    # 2. B2G Dashboard Stats (New Strategy)
    path("api/staff/dashboard/stats/", StaffDiaryViewSet.as_view({'get': 'dashboard_stats'})),
    path("api/staff/export/report/", StaffDiaryViewSet.as_view({'get': 'export_report'})),

    path("api/v1/diaries/statistics/", StatisticsView.as_view()),

    path("admin/", admin.site.urls),
    # Accounts (Auth)
    path("api/v1/auth/", include("accounts.urls")),
    # Haru-On (Diary)
    path("api/v1/diaries/", include("haru_on.urls")),
    
    # [Fix] Request from Legacy Frontend (Flask-style URL /api/diaries)
    # Handle optional trailing slash with re_path to allow POST without redirect
    re_path(r'^api/diaries/?$', HaruOnViewSet.as_view({'get': 'list', 'post': 'create'})),
    re_path(r'^api/diaries/(?P<pk>\d+)/?$', HaruOnViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    
    # [Fix] Legacy Login Support
    path("api/login", LegacyLoginView.as_view()),
    path("api/user/me", UserMeView.as_view()), # [Fix] User Info API
    
    # Centers & B2G
    path("api/v1/centers/", include("centers.urls")),
    path("api/v1/connect/", include("b2g_sync.urls")),
    # Shared Friend Logic
    path("api/v1/share/", include("share.urls")),

    # Swagger
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
import sys
print("DEBUG: urls.py loaded", file=sys.stderr)
for p in urlpatterns:
    print(f"DEBUG URL: {p}", file=sys.stderr)
