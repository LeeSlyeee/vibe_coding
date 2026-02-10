from rest_framework import serializers
from .models import Center

class CenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Center
        fields = ('id', 'name', 'region')
        read_only_fields = ('id', 'name', 'region')
