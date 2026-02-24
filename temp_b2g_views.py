from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from centers.models import Center
# from accounts.models import User (Circular import risk, use get_user_model)
from django.contrib.auth import get_user_model

User = get_user_model()

class CenterVerifyView(views.APIView):
    """
    [B2G] Verify Center Code API
    Mapping: POST /api/centers/verify-code/
    """
    permission_classes = [permissions.AllowAny] # Code verification is public

    def post(self, request):
        code = (request.data.get('center_code') or request.data.get('code', '')).strip().upper()
        
        if not code:
            return Response({"valid": False, "message": "코드를 입력해주세요."}, status=400)

        # 1. Find Center by Code
        try:
            center = Center.objects.get(code=code)
            return Response({
                "valid": True,
                "center": {
                    "name": center.name,
                    "region": center.region,
                    "id": str(center.id)
                },
                "center_id": str(center.id),
                "user": {} 
            }, status=200)
        except Center.DoesNotExist:
            return Response({
                "valid": False,
                "message": "유효하지 않은 기관 코드입니다."
            }, status=404)

class CenterConnectView(views.APIView):
    """
    [B2G] Connect User to Center API
    Mapping: POST /api/b2g_sync/connect/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        center_id = request.data.get('center_id')

        if not center_id:
             return Response({"message": "Center ID missing"}, status=400)
        
        # 1. Find Center
        center = None
        # Try ID first
        if str(center_id).isdigit():
            center = Center.objects.filter(id=int(center_id)).first()
        
        # Try Code if ID fails
        if not center:
             center = Center.objects.filter(code=str(center_id)).first()

        if not center:
             return Response({"message": "Center not found"}, status=404)

        # 2. Update User
        try:
            with transaction.atomic():
                user.center = center
                # [Fix] Also mark PHQ-9 as tested if connecting (Implied logic)
                # But 'is_tested' field is not in User Model yet (Need to add to User Model first or ignore)
                # Assuming simple connection only for now.
                user.save()
                
                print(f"✅ [B2G] User {user.username} connected to Center {center.name}")

            return Response({
                "message": "Successfully connected",
                "center": {
                    "name": center.name,
                    "id": center.id
                }
            }, status=200)

        except Exception as e:
            print(f"❌ [B2G] Connection Failed: {e}")
            return Response({"message": "Internal Server Error"}, status=500)
