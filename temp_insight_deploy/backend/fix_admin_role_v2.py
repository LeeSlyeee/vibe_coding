import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def fix_admin_role_v2():
    print("--- Fixing Admin Role (v2) ---")
    
    # 1. Demote 'professor'
    try:
        prof = User.objects.get(username='professor')
        prof.is_staff = False
        prof.is_superuser = False
        prof.role = 'student' # Ensure specific role
        prof.save()
        print("Demoted 'professor'.")
    except User.DoesNotExist:
        pass

    # 2. Ensure 'slyeee' is Patient
    try:
        sly = User.objects.get(username='slyeee')
        sly.is_staff = False
        sly.is_superuser = False
        sly.role = 'student'
        sly.save()
        print("Ensured 'slyeee' is Patient.")
    except User.DoesNotExist:
        pass

    # 3. Restore/Create 'admin'
    try:
        if User.objects.filter(username='admin').exists():
            admin_user = User.objects.get(username='admin')
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.role = 'admin' # Explicitly set role
            admin_user.save()
            print("Promoted existing 'admin'.")
        else:
            print("Creating 'admin'...")
            # Create user manually to set 'role' field which is required
            admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'vibe1234')
            admin_user.role = 'admin'
            admin_user.save()
            print("Created 'admin' user.")
            
    except Exception as e:
        print(f"Error creating admin: {e}")
        # Manual fallback using raw SQL if ORM fails due to constraints
        if 'violates not-null constraint' in str(e):
             print("Trying raw SQL fallback...")
             from django.db import connection
             with connection.cursor() as cursor:
                 cursor.execute("INSERT INTO users_user (password, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined, role) VALUES ('pbkdf2_sha256$260000$....', true, 'admin', '', '', 'admin@example.com', true, true, now(), 'admin') ON CONFLICT (username) DO UPDATE SET is_staff=true, is_superuser=true, role='admin';")
                 
if __name__ == "__main__":
    fix_admin_role_v2()
