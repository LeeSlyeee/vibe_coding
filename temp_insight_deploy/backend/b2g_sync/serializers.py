from rest_framework import serializers
from .models import B2GConnection
from centers.serializers import CenterSerializer

class B2GConnectionSerializer(serializers.ModelSerializer):
    center_info = CenterSerializer(source='center', read_only=True)
    
    class Meta:
        model = B2GConnection
        fields = ('id', 'user', 'center', 'center_info', 'status', 'consented_at')
        read_only_fields = ('user', 'status', 'consented_at')
