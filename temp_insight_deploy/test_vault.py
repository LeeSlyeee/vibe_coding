import json
import datetime
from django.test import RequestFactory
from centers.views import SyncDataView
from haru_on.models import HaruOn
from django.contrib.auth import get_user_model

u = get_user_model().objects.get(username='slyeee')
target_date_str = '2026-01-28'
print(f"--- VAULT POLICY INTEGRITY TEST (Target: {target_date_str}) ---")

# 1. Snapshot Initial State
# Filter for Jan 28 (UTC sensitive check)
start = datetime.datetime(2026, 1, 28, 0, 0, tzinfo=datetime.timezone.utc)
end = datetime.datetime(2026, 1, 29, 0, 0, tzinfo=datetime.timezone.utc)
initial_record = HaruOn.objects.filter(user=u, created_at__range=(start, end)).order_by('-created_at').first()

if not initial_record:
    print("SKIP: No record found for Jan 28 to test against.")
    exit()

print(f"[Before Attack] Content: '{initial_record.content[:30]}...'")
print(f"[Before Attack] AI Data Len: {len(str(initial_record.analysis_result))}")

# 2. Simulate Malicious/Accidental Sync (Overwrite Attempt)
# Trying to overwrite with "Hacked Data" and empty AI
attack_data = [{
    'date': target_date_str, 
    'content': '⚠️ HACKED DATA ⚠️', 
    'event': '⚠️ HACKED DATA ⚠️',
    'score': 1,
    'created_at': f'{target_date_str}T12:00:00Z',
    'mood_metrics': [] # Empty AI
}]

factory = RequestFactory()
request = factory.post(
    '/api/sync', 
    data={'sync_data': json.dumps(attack_data)}, 
    content_type='application/x-www-form-urlencoded'
)
request.user = u

print("\n>>> EXECUTE ATTACK: Sending 'Hacked Data' payload to SyncDataView...")
try:
    response = SyncDataView.as_view()(request)
    print(f"Server Response: {response.status_code} (Likely 200 OK because logic should handle it gracefully)")
except Exception as e:
    print(f"Server Error during attack: {e}")

# 3. Verify Integrity
initial_record.refresh_from_db()

print(f"\n[After Attack] Content: '{initial_record.content[:30]}...'")
print(f"[After Attack] AI Data Len: {len(str(initial_record.analysis_result))}")

if initial_record.content != '⚠️ HACKED DATA ⚠️' and len(str(initial_record.analysis_result)) > 20:
    print("\n✅ TEST PASSED: Server successfully rejected the overwrite attempt.")
    print("   Original data is SAFE.")
else:
    print("\n❌ TEST FAILED: Data was overwritten!")
