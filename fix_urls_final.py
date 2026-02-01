code = """from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MaumOnViewSet, StatisticsView, GetConfigView, AssessmentView
from .staff_views import StaffDiaryViewSet
from .staff_patient_views import PatientListView, PatientDetailView

router = DefaultRouter()
router.register(r'staff/diaries', StaffDiaryViewSet, basename='staff-diaries')
router.register(r'', MaumOnViewSet, basename='maumon')

urlpatterns = [
    path('config/', GetConfigView.as_view(), name='config'),
    path('assessment/', AssessmentView.as_view(), name='assessment'),
    
    # 환자 관리 API
    path('staff/patients/', PatientListView.as_view(), name='staff-patient-list'),
    path('staff/patients/<int:user_id>/', PatientDetailView.as_view(), name='staff-patient-detail'),

    path('statistics/', StatisticsView.as_view(), name='statistics'),
    
    path('', include(router.urls)), 
]
"""

with open('/home/ubuntu/InsightMind/backend/maum_on/urls.py', 'w') as f:
    f.write(code)
    
print("Successfully overwrote maum_on/urls.py")
