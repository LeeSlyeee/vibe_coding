package com.maumon.app.ui.diary

import android.app.Application
import android.content.Context
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.maumon.app.data.model.Diary
import com.maumon.app.data.repository.DiaryRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject
import java.net.URL

data class DiaryWriteUiState(
    val mood: Int = 3,
    val event: String = "",
    val emotionDesc: String = "",
    val emotionMeaning: String = "",
    val selfTalk: String = "",
    val sleepDesc: String = "",
    val weather: String = "맑음 ☀️",
    val temperature: Double = 20.0,
    val medicationTaken: Boolean = false,
    val isSaving: Boolean = false,
    val isSaved: Boolean = false,
    val errorMessage: String? = null,
    // 수정 모드
    val editDiaryId: String? = null,
    // 마음 가이드 (iOS Insight View 대응)
    val showMindGuide: Boolean = true,
    val isLoadingGuide: Boolean = true,
    val guideMessage: String = "",
    val isWeatherLoaded: Boolean = false,
    // 약물 관리 (iOS MedicationSettingView 대응)
    val savedMedications: List<String> = emptyList(),  // 등록된 약 목록
    val takenMedications: Set<String> = emptySet(),    // 오늘 복용한 약
    val showMedSettings: Boolean = false,               // 약물 설정 다이얼로그 표시
    // [Crisis Detection] 위기감지 SOS 다이얼로그
    val showCrisisSOSDialog: Boolean = false,
) {
    val isEditMode: Boolean get() = editDiaryId != null
    val canSave: Boolean get() = emotionDesc.isNotBlank()
    /** 약물 설명 문자열 (iOS medication_desc 대응) */
    val medicationDesc: String?
        get() = if (savedMedications.isNotEmpty() && takenMedications.isNotEmpty()) {
            takenMedications.joinToString(", ")
        } else null
    /** 최종 복용 여부 */
    val finalMedicationTaken: Boolean
        get() = if (savedMedications.isNotEmpty()) {
            takenMedications.isNotEmpty()
        } else {
            medicationTaken
        }
}

class DiaryWriteViewModel(app: Application) : AndroidViewModel(app) {
    private val diaryRepo = DiaryRepository()
    private val prefs = app.getSharedPreferences("maumon_meds", Context.MODE_PRIVATE)

    private val _uiState = MutableStateFlow(DiaryWriteUiState())
    val uiState: StateFlow<DiaryWriteUiState> = _uiState

    init {
        // 앱 시작 시 저장된 약물 목록 로드 (iOS loadMedications 대응)
        loadMedications()
    }

    fun updateMood(mood: Int) { _uiState.update { it.copy(mood = mood) } }
    fun updateEvent(v: String) { _uiState.update { it.copy(event = v) } }
    fun updateEmotionDesc(v: String) { _uiState.update { it.copy(emotionDesc = v) } }
    fun updateEmotionMeaning(v: String) { _uiState.update { it.copy(emotionMeaning = v) } }
    fun updateSelfTalk(v: String) { _uiState.update { it.copy(selfTalk = v) } }
    fun updateSleep(v: String) { _uiState.update { it.copy(sleepDesc = v) } }
    fun updateWeather(v: String) { _uiState.update { it.copy(weather = v) } }
    fun updateMedication(v: Boolean) { _uiState.update { it.copy(medicationTaken = v) } }

    /** 마음 가이드 건너뛰고 바로 폼으로 전환 */
    fun skipToForm() {
        _uiState.update { it.copy(showMindGuide = false) }
    }

    // ═══════════════════════════════════════════
    // 약물 관리 (iOS MedicationSettingView 대응)
    // ═══════════════════════════════════════════

    /** 약물 설정 다이얼로그 열기/닫기 */
    fun showMedSettings() { _uiState.update { it.copy(showMedSettings = true) } }
    fun hideMedSettings() {
        _uiState.update { it.copy(showMedSettings = false) }
        loadMedications() // 설정 닫을 때 다시 로드 (iOS onDismiss 대응)
    }

    /** 저장된 약물 목록 로드 (SharedPreferences) */
    fun loadMedications() {
        val json = prefs.getString("savedMedications", null)
        val meds = if (json != null) {
            try {
                val arr = JSONArray(json)
                (0 until arr.length()).map { arr.getString(it) }
            } catch (_: Exception) {
                emptyList()
            }
        } else {
            emptyList()
        }
        _uiState.update { it.copy(savedMedications = meds) }
    }

    /** 약물 추가 (iOS addMedication 대응) */
    fun addMedication(name: String) {
        val trimmed = name.trim()
        if (trimmed.isEmpty()) return
        val current = _uiState.value.savedMedications.toMutableList()
        if (current.contains(trimmed)) return // 중복 방지
        current.add(trimmed)
        saveMedications(current)
        _uiState.update { it.copy(savedMedications = current) }
    }

    /** 약물 삭제 (iOS deleteMedication 대응) */
    fun removeMedication(name: String) {
        val current = _uiState.value.savedMedications.toMutableList()
        current.remove(name)
        saveMedications(current)
        // 복용 목록에서도 제거
        val taken = _uiState.value.takenMedications.toMutableSet()
        taken.remove(name)
        _uiState.update { it.copy(savedMedications = current, takenMedications = taken) }
    }

    /** 개별 약물 복용 토글 (iOS takenMeds toggle 대응) */
    fun toggleMedTaken(name: String) {
        val taken = _uiState.value.takenMedications.toMutableSet()
        if (taken.contains(name)) taken.remove(name) else taken.add(name)
        _uiState.update { it.copy(takenMedications = taken) }
    }

    /** SharedPreferences에 약물 목록 저장 (iOS UserDefaults 대응) */
    private fun saveMedications(meds: List<String>) {
        val arr = JSONArray()
        meds.forEach { arr.put(it) }
        prefs.edit().putString("savedMedications", arr.toString()).apply()
    }

    /** 수정 모드: 기존 일기 데이터로 폼 채우기 (iOS onAppear diaryToEdit 대응) */
    fun loadFromDiary(diary: Diary) {
        // 수정 시 medication_desc에서 개별 약물 복원
        val takenSet = if (!diary.medicationDesc.isNullOrEmpty()) {
            diary.medicationDesc.split(", ").toSet()
        } else {
            emptySet()
        }

        _uiState.value = DiaryWriteUiState(
            mood = diary.effectiveMoodLevel,
            event = diary.event ?: diary.content ?: "",
            emotionDesc = diary.emotionDesc ?: "",
            emotionMeaning = diary.emotionMeaning ?: "",
            selfTalk = diary.selfTalk ?: "",
            sleepDesc = diary.sleepDesc ?: diary.sleepCondition ?: "",
            weather = diary.weather ?: "맑음 ☀️",
            temperature = diary.temperature ?: 20.0,
            medicationTaken = diary.medicationTaken ?: diary.medication ?: false,
            editDiaryId = diary.realId,
            // 수정 모드에서는 가이드 건너뜀
            showMindGuide = false,
            isLoadingGuide = false,
            // 약물 복원
            savedMedications = _uiState.value.savedMedications, // 기존 목록 유지
            takenMedications = takenSet,
        )
    }

    /**
     * 날씨 자동 가져오기 + 마음 가이드 생성
     * iOS fetchWeather() → fetchInsight() 체인 대응
     */
    fun fetchWeatherAndGuide() {
        viewModelScope.launch {
            try {
                // Step 1: IP 기반 위치 파악 (iOS ipapi.co 대응)
                var lat = 37.5665  // 서울 기본값
                var lon = 126.9780

                try {
                    val ipData = fetchUrl("https://ipapi.co/json/")
                    if (ipData != null) {
                        val json = JSONObject(ipData)
                        lat = json.optDouble("latitude", lat)
                        lon = json.optDouble("longitude", lon)
                    }
                } catch (_: Exception) { }

                // Step 2: Open-Meteo API로 날씨 가져오기 (iOS 동일 API)
                try {
                    val weatherUrl = "https://api.open-meteo.com/v1/forecast?latitude=$lat&longitude=$lon&current_weather=true&timezone=auto"
                    val weatherData = fetchUrl(weatherUrl)
                    if (weatherData != null) {
                        val json = JSONObject(weatherData)
                        val current = json.optJSONObject("current_weather")
                        if (current != null) {
                            val code = current.optInt("weathercode", 0)
                            val temp = current.optDouble("temperature", 20.0)
                            val weatherDesc = weatherCodeToDesc(code)
                            _uiState.update { it.copy(
                                weather = weatherDesc,
                                temperature = temp,
                                isWeatherLoaded = true
                            ) }
                        }
                    }
                } catch (_: Exception) { }

                // Step 3: 마음 가이드 메시지 생성
                val quotes = listOf(
                    "오늘 하루도 수고 많으셨어요.",
                    "당신의 감정은 소중합니다.",
                    "천천히, 편안하게 기록해보세요.",
                    "오늘의 날씨처럼 마음도 변할 수 있어요.",
                    "작은 기록이 큰 변화를 만듭니다.",
                    "지금 이 순간, 당신은 충분합니다.",
                    "감정에 옳고 그름은 없어요.",
                    "오늘의 나에게 따뜻한 말 한마디를 건네보세요."
                )

                _uiState.update { it.copy(
                    isLoadingGuide = false,
                    guideMessage = quotes.random(),
                ) }

            } catch (e: Exception) {
                _uiState.update { it.copy(
                    isLoadingGuide = false,
                    guideMessage = "오늘 하루도 수고 많으셨어요.",
                ) }
            }
        }
    }

    /** URL에서 String 가져오기 */
    private suspend fun fetchUrl(urlStr: String): String? {
        return try {
            kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
                URL(urlStr).readText()
            }
        } catch (_: Exception) { null }
    }

    /** Weather Code → 한글 날씨 설명 (iOS 동일 매핑) */
    private fun weatherCodeToDesc(code: Int): String {
        return when (code) {
            0 -> "맑음 ☀️"
            1 -> "대체로 맑음 🌤️"
            2 -> "구름 조금 ⛅"
            3 -> "흐림 ☁️"
            4, 45, 48 -> "안개 🌫️"
            51, 53, 55 -> "이슬비 🌧️"
            61, 63, 65, 80 -> "비 ☔"
            95 -> "뇌우 ⚡"
            71, 73, 75, 77, 85, 86 -> "눈 🌨️"
            else -> "흐림 ☁️"
        }
    }

    // [Crisis Detection] SOS 다이얼로그 닫기
    fun dismissCrisisSOSDialog() {
        _uiState.update { it.copy(showCrisisSOSDialog = false) }
    }

    fun saveDiary(dateStr: String) {
        val state = _uiState.value
        if (!state.canSave) return

        // [Crisis Detection] 저장 전 위기 키워드 검사
        val allText = listOf(state.event, state.emotionDesc, state.emotionMeaning, state.selfTalk, state.sleepDesc)
            .joinToString(" ")
        val crisisLevel3 = listOf("죽고", "자살", "뛰어내", "목을", "손목", "유서", "마지막", "끝내고", "자해", "목숨")
        val crisisLevel2 = listOf("사라지고", "없어지고", "살기 싫", "의미 없", "끝내", "망했", "수면제", "칼", "약 먹", "다 끝")

        val hasLevel3 = crisisLevel3.any { allText.contains(it) }
        val hasLevel2 = crisisLevel2.any { allText.contains(it) }

        if (hasLevel3 || hasLevel2) {
            _uiState.update { it.copy(showCrisisSOSDialog = true) }
            return // 저장하지 않고 즉시 반환
        }

        _uiState.update { it.copy(isSaving = true, errorMessage = null) }

        val diary = Diary(
            date = dateStr,
            moodLevel = state.mood,
            event = state.event,
            content = state.event,
            emotionDesc = state.emotionDesc,
            emotionMeaning = state.emotionMeaning,
            selfTalk = state.selfTalk,
            sleepDesc = state.sleepDesc,
            sleepCondition = state.sleepDesc,
            weather = state.weather,
            temperature = state.temperature,
            medicationTaken = state.finalMedicationTaken,
            medication = state.finalMedicationTaken,
            medicationDesc = state.medicationDesc,
            aiPrediction = "분석 중..."
        )

        viewModelScope.launch {
            val result = if (state.isEditMode) {
                diaryRepo.updateDiary(state.editDiaryId!!, diary)
            } else {
                diaryRepo.saveDiary(diary)
            }
            result.onSuccess {
                _uiState.update { it.copy(isSaving = false, isSaved = true) }
            }.onFailure { e ->
                _uiState.update { it.copy(
                    isSaving = false,
                    errorMessage = "저장 실패: ${e.message}"
                ) }
            }
        }
    }
}
