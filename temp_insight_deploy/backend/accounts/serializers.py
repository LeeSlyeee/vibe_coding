from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()
from centers.models import Center

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'center_id', 'risk_level')
    
    center_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            risk_level=validated_data.get('risk_level', 'LOW')
        )
        
        center_id = validated_data.get('center_id')
        if center_id:
            try:
                center = Center.objects.get(id=center_id)
                user.center = center
                user.save()
            except Center.DoesNotExist:
                pass
                
        return user

class PasswordResetSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        # 사용자 확인
        try:
            user = User.objects.get(username=data['username'], first_name=data['first_name'])
        except User.DoesNotExist:
            raise serializers.ValidationError("입력하신 정보와 일치하는 사용자가 없습니다.")
        
        return data

    def save(self):
        username = self.validated_data['username']
        user = User.objects.get(username=username)
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
