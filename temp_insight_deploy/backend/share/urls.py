from django.urls import path
from .views import GenerateCodeView, ConnectView, ConnectionListView, DisconnectView, SharedInsightsView

urlpatterns = [
    # 내 공유 코드 생성/조회 (POST)
    path('code', GenerateCodeView.as_view(), name='share-code'),
    
    # 코드로 연결하기 (POST)
    path('connect', ConnectView.as_view(), name='share-connect'),
    
    # 연결 목록 조회 (GET ?user_id=...&role=viewer|sharer)
    path('list', ConnectionListView.as_view(), name='share-list'),
    
    # 연결 해제 (POST)
    path('disconnect', DisconnectView.as_view(), name='share-disconnect'),
    
    # 공유된 사용자의 통계 (GET /insights/<target_id>)
    path('insights/<int:target_id>', SharedInsightsView.as_view(), name='share-insights'),
]
