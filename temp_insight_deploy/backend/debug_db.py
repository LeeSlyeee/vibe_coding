import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from centers.models import VerificationCode, Center
from django.contrib.auth import get_user_model

User = get_user_model()

print("--- Center Debug ---")
for center in Center.objects.all():
    print(f"Center: {center.id} - {center.name}")

print("\n--- Verification Code Debug ---")
for vc in VerificationCode.objects.order_by('-created_at')[:5]:
    status = "USED" if vc.is_used else "UNUSED"
    print(f"Code: {vc.code}, Center: {vc.center.name}, Used: {vc.is_used}, UsedBy: {vc.used_by}")

print("\n--- User Debug (Last 5) ---")
for user in User.objects.order_by('-date_joined')[:5]:
    print(f"User: {user.username}, Staff: {user.is_staff}, SU: {user.is_superuser}, Active: {user.is_active}, Joined: {user.date_joined}")
