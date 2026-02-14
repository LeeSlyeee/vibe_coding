import os
import django
from django.conf import settings
from django.apps import apps

# Django Setup (if needed explicitly, though shell handles it)
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# django.setup()

    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        Diary = apps.get_model('diaries', 'Diary')
        Center = apps.get_model('centers', 'Center')
        
        # 1. Admin Find
        try:
            admin = User.objects.get(username='slyeee')
            print(f"ADMIN Found: {admin.username}")
        except User.DoesNotExist:
            print("ADMIN 'slyeee' NOT FOUND!")
            return

        # 2. Add Center
        if not admin.center:
            center, created = Center.objects.get_or_create(
                code='dobong',
                defaults={'name': '도봉구정신건강복지센터'}
            )
            admin.center = center
            admin.save()
            print(f" -> Assigned Admin Center: {center.name} (New: {created})")
        else:
            print(f" -> Admin Center Exists: {admin.center.name}")

        # 3. Fix Patients
        patients = User.objects.filter(role='patient')
        print(f"PATIENTS Total: {patients.count()}")
        
        for p in patients:
            if not p.center:
                p.center = admin.center
                p.save()
                print(f"   -> Fixed Center for {p.username}")
            
            d_count = Diary.objects.filter(user=p).count()
            print(f"   - {p.username}: Center={p.center}, Diaries={d_count}")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

run()
