
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

def check_user():
    User = get_user_model()
    try:
        user = User.objects.get(id=1)
        print(f"✅ ID 1 User Found:")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Is Staff: {user.is_staff}")
        print(f"First Name: {user.first_name}")
        print(f"Last Name: {user.last_name}")
    except User.DoesNotExist:
        print("❌ ID 1 User Not Found")

if __name__ == "__main__":
    check_user()
