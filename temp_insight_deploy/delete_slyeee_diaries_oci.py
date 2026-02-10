import os
import django
from django.conf import settings

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from haru_on.models import HaruOn

User = get_user_model()
USERNAME = "slyeee"

def cleanup():
    print("--- [OCI 150 Server] Cleanup for user: slyeee ---")
    try:
        user = User.objects.get(username=USERNAME)
        print(f"Target User Found: {user.username} (ID: {user.id})")
        
        # Count before deletion
        count = HaruOn.objects.filter(user=user).count()
        print(f"Current Diary Count: {count}")
        
        if count > 0:
            print("Deleting all diary entries for user 'slyeee'...")
            # We use delete() on queryset which is efficient
            cnt, _ = HaruOn.objects.filter(user=user).delete()
            print(f"✅ Successfully deleted {cnt} diary entries.")
        else:
            print("ℹ️ No diary entries found to delete.")
            
        # Verify
        remaining = HaruOn.objects.filter(user=user).count()
        if remaining == 0:
            print("Verification: 0 entries remain. Clean state confirmed.")
        else:
            print(f"⚠️ Verification Failed: {remaining} entries still remain.")

    except User.DoesNotExist:
        print(f"❌ User '{USERNAME}' does not exist on this server.")

if __name__ == "__main__":
    cleanup()
