"""L2 보건소 관리자가 소속 상담사를 등록하는 API 추가"""
import os, sys, django
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
sys.path.insert(0, "/home/ubuntu/backend_new")
django.setup()

# views.py에 StaffRegisterView 추가
views_path = "/home/ubuntu/backend_new/accounts/views.py"
with open(views_path, "r") as f:
    content = f.read()

if "StaffRegisterView" not in content:
    view_code = '''

class StaffRegisterView(APIView):
    """L2 보건소 관리자가 소속 상담사를 등록"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """소속 보건소의 상담사 목록 조회"""
        user = request.user
        if not user.is_staff:
            return Response({"error": "권한 없음"}, status=403)
        center = user.center
        if not center:
            return Response({"error": "소속 보건소가 없습니다"}, status=400)
        staff = User.objects.filter(center=center, is_staff=True).values(
            "id", "username", "first_name", "email", "admin_level", "date_joined"
        )
        return Response(list(staff))

    def post(self, request):
        """새 상담사 계정 생성"""
        user = request.user
        if not user.is_staff:
            return Response({"error": "권한 없음"}, status=403)
        center = user.center
        if not center:
            return Response({"error": "소속 보건소가 없습니다"}, status=400)

        username = request.data.get("username", "").strip()
        password = request.data.get("password", "").strip()
        first_name = request.data.get("first_name", "").strip()
        email = request.data.get("email", "").strip()

        if not username or not password:
            return Response({"error": "아이디와 비밀번호는 필수입니다"}, status=400)
        if len(password) < 6:
            return Response({"error": "비밀번호는 6자 이상이어야 합니다"}, status=400)
        if User.objects.filter(username=username).exists():
            return Response({"error": "이미 사용 중인 아이디입니다"}, status=400)

        new_staff = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            email=email,
            is_staff=True,
            center=center,
            admin_level="counselor",
        )
        return Response({
            "id": new_staff.id,
            "username": new_staff.username,
            "first_name": new_staff.first_name,
            "center": center.name,
            "message": f"{first_name or username} 상담사가 등록되었습니다"
        }, status=201)
'''
    # Check imports
    if "from rest_framework.views import APIView" not in content:
        content = content.replace(
            "from rest_framework import generics",
            "from rest_framework import generics\nfrom rest_framework.views import APIView"
        )
    if "from rest_framework.permissions import IsAuthenticated" not in content:
        # It might have AllowAny but not IsAuthenticated
        if "IsAuthenticated" not in content:
            content = content.replace(
                "from rest_framework.permissions import AllowAny",
                "from rest_framework.permissions import AllowAny, IsAuthenticated"
            )

    content += view_code
    with open(views_path, "w") as f:
        f.write(content)
    print("StaffRegisterView added to views.py")
else:
    print("StaffRegisterView already exists")

# urls.py에 라우트 추가
urls_path = "/home/ubuntu/backend_new/accounts/urls.py"
with open(urls_path, "r") as f:
    urls = f.read()

if "staff/manage" not in urls:
    # Add import
    if "StaffRegisterView" not in urls:
        urls = urls.replace(
            "from .views import",
            "from .views import StaffRegisterView,"
        )
    # Add URL
    urls = urls.replace(
        "]\n",
        "    path('staff/manage/', StaffRegisterView.as_view(), name='staff-manage'),\n]\n",
        1
    )
    with open(urls_path, "w") as f:
        f.write(urls)
    print("URL route added")
else:
    print("URL already exists")

print("DONE")
