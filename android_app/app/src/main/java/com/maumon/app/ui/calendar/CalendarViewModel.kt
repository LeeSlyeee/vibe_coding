package com.maumon.app.ui.calendar

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.maumon.app.data.model.Diary
import com.maumon.app.data.repository.DiaryRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class CalendarUiState(
    val isLoading: Boolean = false,
    val diaries: List<Diary> = emptyList(),
    val errorMessage: String? = null,
)

class CalendarViewModel : ViewModel() {

    private val diaryRepo = DiaryRepository()

    private val _uiState = MutableStateFlow(CalendarUiState())
    val uiState: StateFlow<CalendarUiState> = _uiState

    init {
        fetchDiaries()
    }

    fun fetchDiaries() {
        _uiState.value = _uiState.value.copy(isLoading = true)
        viewModelScope.launch {
            val result = diaryRepo.fetchDiaries()
            result.onSuccess { diaries ->
                android.util.Log.d("CalendarVM", "✅ 일기 ${diaries.size}개 수신")
                diaries.forEach { d ->
                    android.util.Log.d("CalendarVM", "  📅 ${d.date} mood=${d.moodLevel} event=${d.displayContent.take(20)}")
                }
                _uiState.value = CalendarUiState(diaries = diaries)
            }.onFailure { e ->
                android.util.Log.e("CalendarVM", "❌ 일기 로드 실패: ${e.message}")
                _uiState.value = CalendarUiState(errorMessage = e.message)
            }
        }
    }

    /** 특정 날짜의 일기 찾기 */
    fun getDiaryForDate(dateStr: String): Diary? {
        return _uiState.value.diaries.find { it.date == dateStr }
    }

    /** 감정 레벨 → 이모지 */
    fun moodEmoji(level: Int): String {
        return when (level) {
            5 -> "😊"
            4 -> "🙂"
            3 -> "😐"
            2 -> "😢"
            1 -> "😡"
            else -> ""
        }
    }
}
