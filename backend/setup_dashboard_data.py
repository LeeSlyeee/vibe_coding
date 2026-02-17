import os
import django
from django.conf import settings

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from centers.models import Center, VerificationCode

User = get_user_model()

def setup_data():
    print("🚀 Setting up Dashboard Data (Admin & Center)...")

    # 1. Create Center
    center, created = Center.objects.get_or_create(
        name="마음온 보건소",
        defaults={
            'region': '서울시', 
            'admin_email': 'contact@maumon.com'
        }
    )
    if created:
        print(f"✅ Created Center: {center.name}")
    else:
        print(f"ℹ️ Found Center: {center.name}")

    # 2. Create Verification Code (IV7L90SYBT)
    # This connects the Flask user's center_code to this Center
    vc, created = VerificationCode.objects.get_or_create(
        code="IV7L90SYBT",
        defaults={
            'center': center,
            'is_used': True # Already used by slyeee
        }
    )
    print(f"✅ Verification Code 'IV7L90SYBT' setup. Linked to {center.name}")

    # 3. Create Superuser (maumON_admin)
    try:
        admin_user = User.objects.get(username='maumON_admin')
        print("ℹ️ Admin user 'maumON_admin' already exists.")
    except User.DoesNotExist:
        print("👤 Creating Admin user 'maumON_admin'...")
        admin_user = User.objects.create_superuser(
            username='maumON_admin',
            email='admin@maumon.com',
            password='maumON_1234'
        )
        print("✅ Admin user created.")

    # Link Admin to Center (if applicable, though superuser usually sees all)
    # But if dashboard uses request.user.center...
    admin_user.center = center
    admin_user.save()
    print("✅ Admin linked to Center.")

    # 4. Link 'slyeee' to Center
    try:
        slyeee = User.objects.get(username='slyeee')
        slyeee.center = center
        slyeee.save()
        
        # Also link VC
        vc.used_by = slyeee
        vc.save()
        print(f"✅ User 'slyeee' linked to Center '{center.name}' via code 'IV7L90SYBT'")
    except User.DoesNotExist:
        print("⚠️ User 'slyeee' not found. Please runs sync script again.")

    print("\n🎉 Dashboard Setup Complete!")

if __name__ == '__main__':
    setup_data()
