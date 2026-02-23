import re

file_path = "/home/ubuntu/backend_new/admin_api/views.py"
with open(file_path, "r") as f:
    content = f.read()

if "from django.core.cache import cache" not in content:
    old_imports = "from .serializers import RegionSerializer, PolicyBroadcastSerializer"
    new_imports = old_imports + "\nfrom django.core.cache import cache"
    content = content.replace(old_imports, new_imports)

old_get = """    def get(self, request):
        regions = Region.objects.filter(is_active=True)
        centers = Center.objects.filter(is_active=True)"""
new_get = """    def get(self, request):
        cache_key = "national_summary"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        regions = Region.objects.filter(is_active=True)
        centers = Center.objects.filter(is_active=True)"""
content = content.replace(old_get, new_get)

old_return = """        return Response({
            'summary': {
                'total_regions': regions.count(),
                'total_centers': centers.count(),
                'total_patients': User.objects.filter(is_staff=False, is_superuser=False).count(),
                'total_staff': User.objects.filter(is_staff=True, is_superuser=False).count(),
                'total_high_risk': User.objects.filter(risk_level='HIGH', is_staff=False).count(),
                'total_diaries': MaumOn.objects.count(),
            },
            'regions': region_stats,
        })"""
new_return = """        result = {
            'summary': {
                'total_regions': regions.count(),
                'total_centers': centers.count(),
                'total_patients': User.objects.filter(is_staff=False, is_superuser=False).count(),
                'total_staff': User.objects.filter(is_staff=True, is_superuser=False).count(),
                'total_high_risk': User.objects.filter(risk_level='HIGH', is_staff=False).count(),
                'total_diaries': MaumOn.objects.count(),
            },
            'regions': region_stats,
        }
        cache.set(cache_key, result, 300)
        return Response(result)"""
content = content.replace(old_return, new_return)

with open(file_path, "w") as f:
    f.write(content)

print("Patch applied to NationalSummaryView")
