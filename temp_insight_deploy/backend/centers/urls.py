from django.urls import path
from .views import verify_center_code, GenerateVerificationCodeView, SyncDataView, CenterListView

urlpatterns = [
    path('verify-code/', verify_center_code, name='verify-center-code'), # iOS와 경로 통일

    path('generate/', GenerateVerificationCodeView.as_view(), name='generate-verification-code'),
    path('sync-data/', SyncDataView.as_view(), name='sync-center-data'),
    path('list/', CenterListView.as_view(), name='center-list'),
]
