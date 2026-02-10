import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def check():
    try:
        u = User.objects.get(username="app_Guest")
        print(f"User found: {u.username}")
        is_ok = u.check_password("ios_auto_password_1234")
        print(f"Password Check Result: {is_ok}")
    except User.DoesNotExist:
        print("User app_Guest not found")

if __name__ == '__main__':
    check()
