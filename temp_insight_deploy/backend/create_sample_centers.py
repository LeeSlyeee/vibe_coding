import os
import django
import sys

# 프로젝트 루트 경로를 path에 추가 (필요 시)
# sys.path.append('/Users/slyeee/Desktop/DATA/DATA2/InsightMind/backend')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from centers.models import Center

def create_sample_centers():
    centers_data = [
        {"name": "도봉구 정신건강복지센터", "code": "DOBONG01", "region": "서울특별시 도봉구"},
        {"name": "강남구 보건소", "code": "GANGNAM01", "region": "서울특별시 강남구"},
        {"name": "마포구 마음치유센터", "code": "MAPO01", "region": "서울특별시 마포구"},
    ]

    for data in centers_data:
        center, created = Center.objects.get_or_create(
            name=data["name"],
            defaults={
                "region": data["region"],
                "admin_email": f"admin@{data['code'].lower()}.kr"
            }
        )
        if created:
            print(f"Created center: {center.name}")
        else:
            print(f"Center already exists: {center.name}")

if __name__ == '__main__':
    create_sample_centers()
