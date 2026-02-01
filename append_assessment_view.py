path = '/home/ubuntu/InsightMind/backend/maum_on/views.py'
with open(path, 'r') as f:
    content = f.read()

new_view = """
from django.contrib.auth import get_user_model

class AssessmentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        score = request.data.get('score', 0)
        
        # User 모델의 risk_level 업데이트
        # Choices: LOW, MID, HIGH
        level = 'LOW'
        if score >= 10:
            level = 'HIGH'
        elif score >= 5:
            level = 'MID'
            
        # user.risk_level 필드가 있는지 확인 필요하나, Serializer에서 확인됨.
        if hasattr(user, 'risk_level'):
            user.risk_level = level
            user.save()
            
        return Response({"message": "Assessment saved", "risk_level": level})
"""

if 'class AssessmentView' not in content:
    with open(path, 'a') as f:
        f.write(new_view)
    print("AssessmentView added.")
else:
    print("AssessmentView already exists.")
