from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from haru_on.staff_patient_views import PatientListView, PatientDetailView
from haru_on.staff_views import StaffDiaryViewSet # [New] B2G Dashboard
from haru_on.views import StatisticsView

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

urlpatterns = [
    # [Emergency Bypass] 403 방지를 위한 최우선 경로 매핑 (Router 우회)
    # 1. Patient List & Detail (Absolute Paths)
    path("api/v1/diaries/staff/patients/<int:user_id>/", PatientDetailView.as_view()),
    path("api/v1/diaries/staff/patients/", PatientListView.as_view()),
    
    # [Fix] Add simpler alias for frontend compatibility (Direct mapping)
    path("api/staff/patients/", PatientListView.as_view()),
    path("api/staff/patients/<int:user_id>/", PatientDetailView.as_view()),

    # 2. B2G Dashboard Stats (New Strategy)
    path("api/staff/dashboard/stats/", StaffDiaryViewSet.as_view({'get': 'dashboard_stats'})),
    path("api/staff/export/report/", StaffDiaryViewSet.as_view({'get': 'export_report'})),

    path("api/v1/diaries/statistics/", StatisticsView.as_view()),

    path("admin/", admin.site.urls),
    # Accounts (Auth)
    path("api/v1/auth/", include("accounts.urls")),
    # Haru-On (Diary)
    path("api/v1/diaries/", include("haru_on.urls")),
    # Centers & B2G
    path("api/v1/centers/", include("centers.urls")),
    path("api/v1/connect/", include("b2g_sync.urls")),

    # Swagger
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
