import os
import django
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

User = get_user_model()

def reset_password(username, new_password):
    try:
        user = User.objects.get(username=username)
        user.set_password(new_password)
        user.save()
        print(f"✅ Password for user '{username}' has been reset to '{new_password}'.")
        
        # Verify
        u = User.objects.get(username=username)
        print(f"Verify Check: {u.check_password(new_password)}")
        
    except User.DoesNotExist:
        print(f"❌ User '{username}' does not exist.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    reset_password('slyeee', '1234')
