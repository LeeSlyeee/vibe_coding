from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        center_code = None
        if hasattr(user, 'center') and user.center:
             center_code = getattr(user.center, 'code', None)

        return Response({
            'username': user.username,
            # [Fix] Fallback to first_name if nickname field missing in Django User model
            'nickname': getattr(user, 'nickname', user.first_name) or user.username,
            # [Fix] Map is_staff to role string
            'role': getattr(user, 'role', 'admin' if user.is_staff else 'user'),
            # [Fix] Access via user.center.code
            'center_code': center_code,
            'linked_center_code': center_code
        })


class LegacyLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [] # No auth required for login

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        # Django Auth
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Generate JWT
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            # Legacy Format Response
            center_code = None
            if hasattr(user, 'center') and user.center:
                 center_code = getattr(user.center, 'code', None)

            return Response({
                'access_token': access_token, # Keep key 'access_token' for legacy frontend
                'refresh_token': str(refresh), # Extra
                'username': user.username,
                'center_code': center_code,
                'linked_center_code': center_code,
                'role': 'user' # Default or map from user.is_staff
            })
        else:
            return Response({'msg': '아이디 또는 비밀번호가 올바르지 않습니다.'}, status=401)
