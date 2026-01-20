# Task: 504 Timeout on "Past Record Integrated Analysis" (과거 기록 통합 분석)

## Status: Completed

## Issues Identified

- The 504 Gateway Timeout error was caused by a long-running synchronous `POST /api/report/longterm` request.
- The backend was waiting for the AI generation (Gemini API) to complete before responding, which exceeded the Nginx/Server timeout (typically 60s).

## Changes Implemented

### Backend (`app.py`)

- Refactored `generate_long_term_report` into an asynchronous workflow:
  - **Created `start_long_term_report` (`/api/report/longterm/start`)**:
    - Initiates the AI generation in a background thread.
    - Immediately returns `202 Accepted` to the frontend.
  - **Created `check_long_term_report_status` (`/api/report/longterm/status`)**:
    - Allows the frontend to poll for the result.
    - Returns `{ status: 'processing' | 'completed' | 'failed', insight: ... }`.
  - **Added `background_long_term_task`**: The function that actually runs the heavy AI logic.

### Frontend (`StatsPage.vue` & `api.js`)

- Updated `diaryAPI` to use the new endpoints.
- Modified `handleGenerateLongTermReport` in `StatsPage.vue`:
  - Now calls `start` and then sets up a polling interval (`setInterval`).
- Added `checkLongTermStatus` function to handle the polling logic.
- Ensures polling continues even if the user refreshes the page (checks status on mount).

## Verification

- Click the "과거 기록 통합 분석" button.
- It should now immediately show a "processing" state (e.g., "분석 중...") instead of hanging and showing a browser error.
- After a minute or so, the result should appear automatically via polling.
