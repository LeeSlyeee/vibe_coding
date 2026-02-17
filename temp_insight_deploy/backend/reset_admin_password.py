import os
import django
from django.contrib.auth.hashers import make_password

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def reset_admin_password():
    try:
        if User.objects.filter(username='admin').exists():
            admin_user = User.objects.get(username='admin')
            # Set password properly using Django's hasher
            admin_user.set_password('vibe1234')
            admin_user.role = 'admin'
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            print("Successfully reset 'admin' password to 'vibe1234'.")
        else:
            print("User 'admin' does not exist!")
    except Exception as e:
        print(f"Error resetting password: {e}")

if __name__ == "__main__":
    reset_admin_password()
