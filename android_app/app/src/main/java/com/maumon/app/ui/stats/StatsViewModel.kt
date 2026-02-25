package com.maumon.app.ui.stats

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.maumon.app.data.model.Diary
import com.maumon.app.data.repository.DiaryRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class StatsUiState(
    val isLoading: Boolean = true,
    val totalDiaries: Int = 0,
    val avgMoodScore: Double = 0.0,
    val avgMoodEmoji: String = "😐",
    val happyCount: Int = 0,
    val calmCount: Int = 0,
    val normalCount: Int = 0,
    val sadCount: Int = 0,
    val angryCount: Int = 0,
    val streak: Int = 0,
    // 흐름 탭: (date, moodLevel) 리스트
    val moodTimeline: List<Pair<String, Int>> = emptyList(),
    // 날씨 탭: weather -> List<(moodLevel, count)>
    val weatherMoods: List<Pair<String, List<Pair<Int, Int>>>> = emptyList(),
    // AI 리포트용 일기 목록
    val diaries: List<Diary> = emptyList(),
)

class StatsViewModel : ViewModel() {
    private val diaryRepo = DiaryRepository()
    private val _uiState = MutableStateFlow(StatsUiState())
    val uiState: StateFlow<StatsUiState> = _uiState

    init { loadStats() }

    private fun loadStats() {
        viewModelScope.launch {
            diaryRepo.fetchDiaries()
                .onSuccess { diaries ->
                    if (diaries.isEmpty()) {
                        _uiState.value = StatsUiState(isLoading = false)
                        return@onSuccess
                    }

                    // 미래 날짜 필터 (iOS fetchStats 동일)
                    val todayStr = java.time.LocalDate.now().toString()
                    val filtered = diaries.filter { (it.date ?: "") <= todayStr }

                    val total = filtered.size
                    val avgMood = filtered.map { it.effectiveMoodLevel }.average()
                    val emoji = when {
                        avgMood >= 4.5 -> "😊"
                        avgMood >= 3.5 -> "🙂"
                        avgMood >= 2.5 -> "😐"
                        avgMood >= 1.5 -> "😢"
                        else -> "😡"
                    }

                    val happy = filtered.count { it.effectiveMoodLevel == 5 }
                    val calm = filtered.count { it.effectiveMoodLevel == 4 }
                    val normal = filtered.count { it.effectiveMoodLevel == 3 }
                    val sad = filtered.count { it.effectiveMoodLevel == 2 }
                    val angry = filtered.count { it.effectiveMoodLevel == 1 }

                    // 타임라인 (흐름 탭)
                    val timeline = filtered
                        .mapNotNull { d -> d.date?.let { it to d.effectiveMoodLevel } }
                        .sortedBy { it.first }

                    // 날씨별 감정 통계
                    val weatherMap = mutableMapOf<String, MutableMap<Int, Int>>()
                    filtered.forEach { d ->
                        val rawW = d.weather
                        if (!rawW.isNullOrBlank() && rawW != "알 수 없음") {
                            // 이모지 제거 + 공백 trim → "맑음 ☀️" == "맑음"
                            val w = rawW.replace(Regex("[^\\p{L}\\p{N}\\s]"), "").trim()
                            if (w.isNotBlank()) {
                                val moodMap = weatherMap.getOrPut(w) { mutableMapOf() }
                                val mood = d.effectiveMoodLevel.coerceIn(1, 5)
                                moodMap[mood] = (moodMap[mood] ?: 0) + 1
                            }
                        }
                    }
                    val weatherMoods = weatherMap.map { (w, moods) ->
                        w to moods.entries.map { it.key to it.value }.sortedBy { it.first }
                    }.sortedBy { it.first }

                    // 연속 기록
                    val sortedDates = filtered.mapNotNull { it.date }.sorted().distinct()
                    var streak = 0
                    val today = java.time.LocalDate.now()
                    var checkDate = today
                    for (dateStr in sortedDates.reversed()) {
                        try {
                            val d = java.time.LocalDate.parse(dateStr)
                            if (d == checkDate || d == checkDate.minusDays(1)) {
                                streak++
                                checkDate = d
                            } else break
                        } catch (_: Exception) { break }
                    }

                    _uiState.value = StatsUiState(
                        isLoading = false,
                        totalDiaries = total,
                        avgMoodScore = avgMood,
                        avgMoodEmoji = emoji,
                        happyCount = happy,
                        calmCount = calm,
                        normalCount = normal,
                        sadCount = sad,
                        angryCount = angry,
                        streak = streak,
                        moodTimeline = timeline,
                        weatherMoods = weatherMoods,
                        diaries = filtered
                    )
                }
                .onFailure {
                    _uiState.value = StatsUiState(isLoading = false)
                }
        }
    }
}
