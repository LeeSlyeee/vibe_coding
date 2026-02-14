import os
import django
from django.conf import settings
from django.apps import apps
from django.contrib.auth import get_user_model

def run():
    try:
        User = get_user_model()
        
        # 1. DELETE Anonymous Users (created by App)
        # Pattern: username usually random 6 chars or starts with 'user_'
        # Strategy: Delete users with no 'first_name' (wait, I just filled them!)
        # Or delete specific user '39ca9a'
        
        targets = User.objects.filter(username__icontains='39ca9a')
        count = targets.count()
        
        if count > 0:
            print(f"Deleting {count} anonymous users...")
            targets.delete()
            print("DELETED.")
        else:
            print("No target users found.")

        # Check remaining
        print(f"Remaining Patients: {User.objects.filter(is_staff=False).count()}")

    except Exception as e:
        print(f"ERROR: {e}")

run()
