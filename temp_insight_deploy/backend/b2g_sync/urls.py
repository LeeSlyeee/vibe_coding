from django.urls import path
from .views import ConnectionRequestView, MyConnectionsView

urlpatterns = [
    path('request/', ConnectionRequestView.as_view(), name='connection-request'),
    path('my/', MyConnectionsView.as_view(), name='my-connections'),
]
