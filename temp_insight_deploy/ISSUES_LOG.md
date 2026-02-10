# InsightMind (haruON) Issue Tracking

## 🔴 Urgent (Current Task)

1. **Sync -> Code Disconnect Bug**
   - **Symptoms**: "Force Sync" triggers code removal and failure message.
   - **Status**: Server patched (Auto-Resolve, Timeout Guard, Code Key Fix). Waiting for client verification.
   - **Blocker**: App sending invalid token (`401 Unauthorized`) or using old build.
   - **Proposed Fix**: Log out -> Re-login (Refresh Token), then retry Sync.

## 🟠 Pending (To Be Addressed Later)

2. **Login -> Code Link Failure** (Reported 2026-02-08)
   - **Symptoms**: User enters code during login, but after login, code is not linked in Settings.
   - **Suspected Cause**: `LoginView` or Onboarding flow not calling `VerifyView` properly. To be investigated.
