import os
import django
from django.conf import settings
from django.apps import apps
from django.contrib.auth import get_user_model

def run():
    try:
        User = get_user_model()
        Center = apps.get_model('centers', 'Center')

        try:
            Diary = apps.get_model('haru_on', 'HaruOn')
            print("Diary Model Found: 'HaruOn' (in haru_on app)")
        except LookupError:
            print("CRITICAL: 'HaruOn' model not found in 'haru_on' app!")
            return

        # 1. Admin Find
        try:
            admin = User.objects.get(username='slyeee')
            print(f"ADMIN Found: {admin.username} (ID:{admin.id})")
        except User.DoesNotExist:
            print("ADMIN 'slyeee' NOT FOUND! (Check Username)")
            return

        # 2. Add Center
        if not getattr(admin, 'center', None):
            center, created = Center.objects.get_or_create(
                code='dobong',
                defaults={'name': '도봉구정신건강복지센터'}
            )
            admin.center = center
            admin.save()
            print(f" -> Assigned Admin Center: {center.name}")
        else:
            print(f" -> Admin Center Exists: {admin.center.name}")

        # 3. Fix Patients
        # Use is_staff=False as role field does not exist
        patients = User.objects.filter(is_staff=False, is_superuser=False)
        print(f"PATIENTS Total: {patients.count()}")
        
        for p in patients:
            if not getattr(p, 'center', None):
                p.center = admin.center
                p.save()
                print(f"   -> Fixed Center for {p.username}")
            
            d_count = Diary.objects.filter(user=p).count()
            print(f"   - {p.username}: Center={p.center}, Diaries={d_count}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"CRITICAL ERROR: {e}")

run()
