import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def fix_admin_role():
    print("--- Fixing Admin Role ---")
    
    # 1. Demote 'professor' (if exists)
    try:
        prof = User.objects.get(username='professor')
        prof.is_staff = False
        prof.is_superuser = False
        prof.save()
        print("Demoted 'professor' to normal user.")
    except User.DoesNotExist:
        print("'professor' user not found (okay).")

    # 2. Ensure 'slyeee' is Patient
    try:
        sly = User.objects.get(username='slyeee')
        sly.is_staff = False
        sly.is_superuser = False
        sly.save()
        print("Ensured 'slyeee' is Patient.")
    except User.DoesNotExist:
        print("CRITICAL: 'slyeee' not found!")

    # 3. Restore/Create 'admin'
    try:
        admin_user = User.objects.get(username='admin')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        print("Promoted existing 'admin' to Superuser.")
    except User.DoesNotExist:
        print("'admin' user missing. Creating 'admin'...")
        # Create superuser 'admin' with password 'vibe1234' (default convention)
        admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'vibe1234')
        print("Created 'admin' user with password 'vibe1234'.")

if __name__ == "__main__":
    fix_admin_role()
