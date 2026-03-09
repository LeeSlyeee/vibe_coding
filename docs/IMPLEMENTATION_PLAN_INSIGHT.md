# Implementation Plan: Pre-writing Mindset Insight

## Objective

To analyze the user's past diary entries and provide a guiding comment or "mindset suggestion" _before_ they start writing a new diary entry. This aims to help the user reflect on their recent patterns and approach their new entry with a constructive perspective.

## 1. Backend Implementation (Python)

### 1.1. AI Logic Update (`backend/ai_analysis.py`)

- **New Function**: `generate_pre_write_insight(recent_diaries)`
  - **Input**: A list of the user's diary entries from the **last 3 weeks**.
  - **Logic**:
    - Limit text length of each entry to avoid token limits.
    - Construct a prompt:
      > "Here are the user's diary entries from the past 3 weeks. Analyze their overall emotional trend, recurring themes, and stress points.
      > Provide a **short, warm, and constructive one-sentence advice** on what mindset they should have while writing their diary today, helping them find a positive or reflective direction. (Korean)"
  - **Output**: A text string (the insight).

### 1.2. API Endpoint (`backend/app.py`)

- **New Route**: `GET /api/insight`
  - **Authentication**: Requires login (`@login_required`).
  - **Process**:
    1. Calculate the date 3 weeks ago from today.
    2. Query the database for all diary entries created by the current user **since that date**.
    3. If no diaries exist in this period, return a generic welcoming message (e.g., "첫 기록을 시작해보세요! 솔직한 마음을 담으면 됩니다.").
    4. Call `ai_analysis.generate_pre_write_insight`.
    5. Return the result as JSON: `{ "message": "..." }`.

## 2. Frontend Implementation (Vue.js)

### 2.1. API Service (`frontend/src/services/api.js`)

- Add `getMindsetInsight()` method to the `diaryAPI` object.

### 2.2. UI Update (`frontend/src/components/DiaryModal.vue`)

- **State**: Add `mindsetInsight` (string) and `isLoadingInsight` (boolean).
- **Trigger**:
  - When the modal opens in **Write Mode** (or when switching to write mode), immediately call `getMindsetInsight()`.
- **Display**:
  - Place a "Mindset Card" or "Bubble" at the very top of the writing form.
  - **Design**:
    - Icon: 💡 or 🧘‍♀️.
    - Style: Gentle background color (soft purple or yellow), distinct from the input fields.
    - Animation: Fade in when loaded.
  - **Loading State**: Show a skeleton loader or a "Analyzing your recent mood..." text.

## 3. Execution Steps

1.  **Modify Backend**: Implement `ai_analysis.py` logic and `app.py` route.
2.  **Verify Backend**: Test the `/api/insight` endpoint with `curl` or Postman.
3.  **Modify Frontend**: Update `api.js` and `DiaryModal.vue`.
4.  **Test**: Verified that opening the write modal shows a relevant comment based on DB data.

## Note

- Ensure the API call doesn't block the user from starting to type. It should load asynchronously.
- Handle cases where the AI service might be slow or fail (show nothing or a default message).
