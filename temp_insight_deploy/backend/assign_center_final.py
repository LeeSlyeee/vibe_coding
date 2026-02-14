import os
import django
from django.conf import settings
from django.apps import apps
from django.contrib.auth import get_user_model

def run():
    try:
        User = get_user_model()
        # Diary, Center models might be in different apps
        try:
            Diary = apps.get_model('diaries', 'Diary')
            Center = apps.get_model('centers', 'Center')
        except LookupError:
            print("ERROR: Models not found in 'diaries' or 'centers' app.")
            return

        # 1. Admin Find
        try:
            admin = User.objects.get(username='slyeee')
            print(f"ADMIN Found: {admin.username} (ID:{admin.id})")
        except User.DoesNotExist:
            print("ADMIN 'slyeee' NOT FOUND! (Check Username)")
            return

        # 2. Add Center
        if not hasattr(admin, 'center') or not admin.center:
            # Check if Center model exists
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
        patients = User.objects.filter(role='patient') # Check role name
        print(f"PATIENTS Total: {patients.count()}")
        
        for p in patients:
            if not getattr(p, 'center', None):
                p.center = admin.center
                p.save()
                print(f"   -> Fixed Center for {p.username}")
            
            d_count = Diary.objects.filter(user=p).count()
            print(f"   - {p.username}: Center={p.center}, Diaries={d_count}")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

run()
