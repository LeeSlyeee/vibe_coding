import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def reset_ios_passwords():
    # iOS App uses this hardcoded password for auto-login
    IOS_DEFAULT_PASSWORD = "ios_auto_password_1234"
    
    # Target users created by iOS App (pattern: app_*)
    target_users = User.objects.filter(username__startswith='app_')
    
    print(f"Found {target_users.count()} users matching 'app_*'.")
    if target_users.count() == 0:
        print("No iOS app users found. Please check if users were imported correctly.")
        return

    updated_count = 0
    for user in target_users:
        # We reset the password regardless of current value to ensure it matches
        user.set_password(IOS_DEFAULT_PASSWORD)
        user.save()
        print(f" - Password reset for: {user.username}")
        updated_count += 1
        
    print(f"\nSuccessfully reset passwords for {updated_count} users to '{IOS_DEFAULT_PASSWORD}'.")
    print("iOS App should now be able to login automatically.")

if __name__ == '__main__':
    reset_ios_passwords()
