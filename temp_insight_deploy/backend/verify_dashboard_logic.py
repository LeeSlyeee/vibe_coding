import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Count, Q

User = get_user_model()

def check_dashboard_logic():
    print("--- Django ORM Check ---")
    
    # 1. Total Raw Count
    raw_count = User.objects.count()
    print(f"Total Raw Users: {raw_count}")
    
    # 2. Filter Logic
    # total_patients = User.objects.filter(is_staff=False).exclude(username__startswith='app_').count()
    
    print("\n[Debugging Filter Logic]")
    all_users = User.objects.all()
    
    for u in all_users:
        is_staff = u.is_staff
        username = u.username
        is_app = username.startswith('app_')
        
        status = "INCLUDED"
        if is_staff: status = "EXCLUDED (is_staff=True)"
        elif is_app: status = "EXCLUDED (app_ prefix)"
        
        print(f"User: {username:<20} | is_staff: {is_staff} | Status: {status}")

    # Final Count
    final_count = User.objects.filter(is_staff=False).exclude(username__startswith='app_').count()
    print(f"\nFinal Dashboard Count: {final_count}")

if __name__ == "__main__":
    check_dashboard_logic()
