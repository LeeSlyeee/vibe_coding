# Task: Per-Field Voice Recording UI

## Status: Completed

## User Objective

- The user found "Auto-Categorization" confusing or inaccurate.
- Requested to record voice separately for each diary setion (Question 1, 2, 3, 4).

## Solution

- **Frontend Refactor**:
  - Removed the single global "Voice Record" button.
  - Added a "Microphone" button to **each** question field (inside the accordion header).
  - When clicked, it records audio ONLY for that specific field.
  - The transcription is appended directly to that field's text box.
  - Auto-categorization (`auto_fill`) is disabled for this flow.

## Changes Implemented

### Frontend (`QuestionAccordion.vue`)

- Added `recording` prop (Boolean) to show active state.
- Added `@record` emit event.
- Added a circular Microphone button in the header.
- Added CSS for recording permission state (pulsing orange).

### Frontend (`DiaryModal.vue`)

- Removed global voice logic.
- Implemented `activeField` state to track which question is being recorded.
- passing `activeField === 'questionX'` to each Accordion.
- Updated `startRecording`/`stopRecording` to handle target fields.
- Updated API call to send `auto_fill='false'`.

## Verification

1. Open "Write Diary".
2. You will see a 🎙️ icon next to "Question 1".
3. Click it -> It turns Orange/Pulsing.
4. Speak: "Today I went to the park."
5. Click it again -> Stops.
6. "Today I went to the park" appears in Question 1's text box.
7. Repeat for Question 2 with different content.
