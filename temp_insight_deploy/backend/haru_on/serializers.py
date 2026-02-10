from rest_framework import serializers
from .models import HaruOn

class HaruOnSerializer(serializers.ModelSerializer):
    ai_comment = serializers.CharField(write_only=True, required=False, allow_blank=True)
    ai_advice = serializers.CharField(write_only=True, required=False, allow_blank=True)
    ai_analysis = serializers.CharField(write_only=True, required=False, allow_blank=True)
    ai_prediction = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    user_info = serializers.SerializerMethodField()

    class Meta:
        model = HaruOn
        fields = ('id', 'user', 'user_info', 'content', 'mood_score', 'analysis_result', 'is_high_risk', 'created_at', 
                  'ai_comment', 'ai_advice', 'ai_analysis', 'ai_prediction')
        read_only_fields = ('is_high_risk', 'user', 'user_info')

    def get_user_info(self, obj):
        return {
            'username': obj.user.username,
            'name': obj.user.first_name or '실명없음'
        }
    
    def create(self, validated_data):
        # Extract AI fields if present (though create usually doesn't have them yet)
        ai_data = {}
        for key in ['ai_comment', 'ai_advice', 'ai_analysis', 'ai_prediction']:
            if key in validated_data:
                ai_data[key] = validated_data.pop(key)
        
        if ai_data:
            validated_data['analysis_result'] = ai_data

        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Extract AI fields and merge into analysis_result
        ai_data = instance.analysis_result or {}
        
        has_ai_update = False
        for key in ['ai_comment', 'ai_advice', 'ai_analysis', 'ai_prediction']:
            if key in validated_data:
                val = validated_data.pop(key)
                if val:  # Only update if not empty
                    ai_data[key] = val
                    has_ai_update = True
        
        if has_ai_update:
            instance.analysis_result = ai_data
            
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # 암호화된 content 복호화
        try:
            import os
            from cryptography.fernet import Fernet
            
            key = os.getenv('ENCRYPTION_KEY')
            content = instance.content
            
            # gAAAA로 시작하면 암호문으로 간주
            if key and content and content.startswith('gAAAA'):
                f = Fernet(key)
                ret['content'] = f.decrypt(content.encode()).decode()
        except Exception as e:
            # 복호화 실패 시 원문 유지 (혹은 로깅)
            # print(f"Decryption failed: {e}")
            pass
            
        return ret
