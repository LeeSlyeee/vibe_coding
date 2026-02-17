from rest_framework import serializers
from .models import HaruOn

class HaruOnSerializer(serializers.ModelSerializer):
    ai_comment = serializers.CharField(write_only=True, required=False, allow_blank=True)
    ai_advice = serializers.CharField(write_only=True, required=False, allow_blank=True)
    ai_analysis = serializers.CharField(write_only=True, required=False, allow_blank=True)
    ai_prediction = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    # [Fix] Allow YYYY-MM-DD format from frontend
    created_at = serializers.DateTimeField(required=False, input_formats=['%Y-%m-%d', 'iso-8601', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ'])
    
    # [Fix] Allow empty content (users might just log mood)
    content = serializers.CharField(required=False, allow_blank=True)

    user_info = serializers.SerializerMethodField()

    class Meta:
        model = HaruOn
        fields = ('id', 'user', 'user_info', 'content', 'mood_score', 'analysis_result', 'is_high_risk', 'created_at', 
                  'ai_comment', 'ai_advice', 'ai_analysis', 'ai_prediction',
                  'sleep_condition', 'weather', 'temperature', 'gratitude_note', 
                  'emotion_desc', 'emotion_meaning', 'self_talk')
        read_only_fields = ('is_high_risk', 'user', 'user_info')

    def to_internal_value(self, data):
        print(f"📥 [Serializer] Raw Data in: {data}") # DEBUG LOG
        
        # [Legacy Support] Map Frontend fields to Backend Input
        data = data.copy() # Make mutable copy
        
        # Frontend sends 'event', Backend needs 'content'
        if 'event' in data and 'content' not in data:
            data['content'] = data['event']
        
        # Frontend sends 'mood_level', Backend needs 'mood_score'
        if 'mood_level' in data and 'mood_score' not in data:
            data['mood_score'] = data['mood_level']
            
        try:
            return super().to_internal_value(data)
        except Exception as e:
            print(f"❌ [Serializer] Validation Error: {e}")
            raise e

    def get_user_info(self, obj):
        return {
            'username': obj.user.username,
            'name': obj.user.first_name or '실명없음'
        }
    
    def create(self, validated_data):
        # [Fix] Date Handling: Use frontend 'date' if provided
        request = self.context.get('request')
        if request and 'date' in request.data:
            client_date = request.data['date']
            try:
                # Naive Date parsing (YYYY-MM-DD)
                from datetime import datetime
                y, m, d = map(int, client_date.split('-'))
                # Set time to 12:00:00 to avoid timezone edge cases
                validated_data['created_at'] = datetime(y, m, d, 12, 0, 0)
            except Exception:
                pass # Fallback to auto_now_add (current time)

        # Extract AI fields if present
        ai_data = {}
        for key in ['ai_comment', 'ai_advice', 'ai_analysis', 'ai_prediction']:
            if key in validated_data:
                ai_data[key] = validated_data.pop(key)
        
        if ai_data:
            current_analysis = validated_data.get('analysis_result', {})
            if isinstance(current_analysis, dict):
                current_analysis.update(ai_data)
                validated_data['analysis_result'] = current_analysis
            else:
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
        """
        [Fix] Frontend Compatibility & Decryption Layer
        """
        ret = super().to_representation(instance)
        
        # --- [Logic 1] Decryption ---
        try:
            import os
            from cryptography.fernet import Fernet
            
            key = os.getenv('ENCRYPTION_KEY')
            content = instance.content
            
            # Decrypt content if it starts with gAAAA
            if key and content and content.startswith('gAAAA'):
                f = Fernet(key)
                ret['content'] = f.decrypt(content.encode()).decode()
        except Exception as e:
            pass # Keep original content on error

        # --- [Logic 2] Frontend Mapping ---
        # 1. Map 'mood_score' -> 'mood' (Integer to String Key)
        mood_map = {
            5: 'happy',
            4: 'calm',
            3: 'neutral',
            2: 'sad',
            1: 'angry'
        }
        
        if 'mood_score' in ret:
            score = ret['mood_score']
            # If integer, map to string. If string, keep it.
            if isinstance(score, int):
                ret['mood'] = mood_map.get(score, 'neutral')
            else:
                ret['mood'] = score
            
            # [Fix] Also provide 'mood_level' (Legacy Frontend expects this field too)
            ret['mood_level'] = score
            
        # 2. Flatten 'analysis_result' if root fields are null
        analysis = ret.get('analysis_result') or {}
        if not isinstance(analysis, dict):
            analysis = {}
        
        legacy_fields = [
            'weather', 'temperature', 'sleep_condition', 
            'emotion_desc', 'emotion_meaning', 'self_talk',
            'ai_comment', 'ai_advice', 'ai_prediction', 'ai_emotion'
        ]
        
        for field in legacy_fields:
            if not ret.get(field) and field in analysis:
                ret[field] = analysis[field]
                
        return ret
