from django.contrib.auth import get_user_model
from diaries.models import Diary, Center # Center model required

User = get_user_model()

try:
    admin = User.objects.get(username='slyeee')
    print(f"ADMIN: {admin.username} (ID:{admin.id})")
    print(f" - Center: {admin.center}")

    if not admin.center:
        # Create or Get Center
        center, created = Center.objects.get_or_create(
            code='dobong', 
            defaults={'name': '도봉구정신건강복지센터', 'region': 'Seoul'}
        )
        admin.center = center
        admin.save()
        print(f" -> Assigned Center: {center} (Created: {created})")

    # Patients Check
    patients = User.objects.filter(role='patient')
    print(f"PATIENTS Total: {patients.count()}")
    
    for p in patients:
        print(f" - {p.username}: Center={p.center}")
        if not p.center:
            p.center = admin.center # Assign same center
            p.save()
            print(f"   -> Fixed Center for {p.username}")
        
        # Check Diaries
        d_count = Diary.objects.filter(user=p).count()
        print(f"   -> Diaries: {d_count}")

except Exception as e:
    print(f"ERROR: {e}")
