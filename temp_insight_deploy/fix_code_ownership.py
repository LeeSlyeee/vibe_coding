
from centers.models import VerificationCode, Center
from django.contrib.auth import get_user_model

User = get_user_model()

try:
    slyeee = User.objects.get(username='slyeee')
except User.DoesNotExist:
    # Fallback to ID if username mismatch (though list showed it)
    slyeee = User.objects.get(pk=21)

print(f"Target User: {slyeee.username} (ID: {slyeee.id})")

# 1. Fix SEOUL-001
try:
    code_seoul = VerificationCode.objects.get(code='SEOUL-001')
    code_seoul.used_by = slyeee
    code_seoul.save()
    print(f"Success: 'SEOUL-001' is now owned by {slyeee.username}")
except VerificationCode.DoesNotExist:
    center = Center.objects.first()
    VerificationCode.objects.create(code='SEOUL-001', center=center, is_used=True, used_by=slyeee)
    print(f"Created 'SEOUL-001' and assigned to {slyeee.username}")

# 2. Cleanup TestUser codes
try:
    test_user = User.objects.get(id=38) # app_TestUser
    bad_codes = VerificationCode.objects.filter(used_by=test_user).exclude(code='SEOUL-001')
    for c in bad_codes:
        c.used_by = None
        c.is_used = False
        c.save()
        print(f"Released code '{c.code}' from TestUser")
except User.DoesNotExist:
    pass

