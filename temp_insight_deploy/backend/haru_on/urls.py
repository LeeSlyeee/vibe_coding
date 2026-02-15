from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HaruOnViewSet, StatisticsView
from .staff_views import StaffDiaryViewSet
from .staff_patient_views import PatientListView, PatientDetailView

router = DefaultRouter()
router.register(r'staff/diaries', StaffDiaryViewSet, basename='staff-diaries')
# r'' registration needs to be handled carefully. 
# Ideally, we should register it last or rely on DRF's ordering.
router.register(r'', HaruOnViewSet, basename='haruon')

urlpatterns = [
    # 환자 관리 API (가장 먼저 매칭)
    path('staff/patients/', PatientListView.as_view(), name='staff-patient-list'),
    path('staff/patients/<str:user_id>/', PatientDetailView.as_view(), name='staff-patient-detail'),

    path('statistics/', StatisticsView.as_view(), name='statistics'), # [OCI Logic] 통계 API 추가
    path('', include(router.urls)), 
]
