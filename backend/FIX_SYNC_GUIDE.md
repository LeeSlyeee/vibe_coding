# 🛠 Slyeee Diary Sync Fix Guide (217 Server)

## Problem

- Diary entries for `slyeee` created in Jan/Feb 2026 were missing from the 217 server.
- The iOS app (connected to 217) showed zero recent entries.
- The 150 server (InsightMind) has the correct data properly backed up.

## Solution

We have created a recovery script that:

1. Links the `slyeee` user to the correct center code (`SEOUL-001`).
2. Pulls missing diary entries directly from the 150 server via the B2G Sync API.
3. Automatically encrypts and stores them in the 217 database.

## Instructions

### 1. If running locally (Mac/Dev):

Run the script directly:

```bash
cd backend
source venv/bin/activate
python sync_slyeee_217.py
```

### 2. If running on 217 Server (Remote):

1. Copy `backend/sync_slyeee_217.py` to the server.

   ```bash
   scp -i /path/to/key backend/sync_slyeee_217.py opc@217.142.253.35:/home/opc/vibe_coding/backend/
   ```

   _(Adjust user/path as necessary)_

2. SSH into the server and run:
   ```bash
   ssh -i /path/to/key opc@217.142.253.35
   cd /home/opc/vibe_coding/backend
   source venv/bin/activate
   python sync_slyeee_217.py
   ```

### Verification

After running the script, the output should show:

- `✅ Updated Link: slyeee -> SEOUL-001`
- `📥 [B2G Web] Fetched XX items from Server.`
- `✅ [B2G Web] Pulled & Restored XX missing diaries.`

Then verify in the iOS App (pull to refresh).
