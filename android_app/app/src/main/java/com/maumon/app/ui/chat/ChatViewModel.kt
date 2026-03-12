package com.maumon.app.ui.chat

import android.app.Application
import android.util.Log
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.maumon.app.data.api.ApiClient
import com.maumon.app.data.model.Diary
import com.maumon.app.data.repository.AuthRepository
import com.maumon.app.data.repository.DiaryRepository
import com.maumon.app.data.llm.LLMService
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*

data class ChatUiState(
    val messages: List<ChatMessage> = emptyList(),
    val isTyping: Boolean = false,
    val showCrisisBanner: Boolean = false,
    val crisisLevel: Int = 0, // [Phase 4] 0=안전, 1=관심, 2=주의, 3=위험
    val showSOSDialog: Boolean = false, // [Phase 4] Level 3 즉시 모달
    val useServerAI: Boolean = true,
    val isModelLoaded: Boolean = false,
    // ─── 6단계 가이드형 일기 작성 플로우 (iOS AppChatView 대응) ───
    val currentStepIndex: Int = 0,
    val isFlowCompleted: Boolean = false,   // 6단계 모두 완료
    val isAnalyzing: Boolean = false,       // AI 분석 진행 중
    val loadingHint: String? = null,        // 분석 중 안내 메시지
    val isSaved: Boolean = false,           // 일기 저장 완료
    val isFreeChatMode: Boolean = false,    // 자유 대화 모드 (일기 완료 후 활성화)
)

class ChatViewModel(application: Application) : AndroidViewModel(application) {

    companion object {
        private const val TAG = "ChatVM"
    }

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState

    private val llmService = LLMService.getInstance()
    private val authRepo = AuthRepository(application.applicationContext)
    private val diaryRepo = DiaryRepository()

    // ═══════════════════════════════════════════════════════════════
    // 6단계 가이드형 대화 (iOS AppChatView.swift 완전 대응)
    // ═══════════════════════════════════════════════════════════════
    // Step 0: 투약 → Step 1: 수면 → Step 2: 사건 → Step 3: 감정
    // → Step 4: 의미 → Step 5: 자기위로(독백) → 분석 시작
    // ═══════════════════════════════════════════════════════════════

    /** 수집된 답변 (6칸: 투약/수면/사건/감정/의미/독백) */
    private val collectedAnswers = Array(6) { "" }

    /** 단계별 질문 (iOS stepQuestions 동일) */
    private val stepQuestions = listOf(
        "어젯밤 잠은 어떻게 주무셨나요?\n깊이 잤는지, 꿈을 꿨는지, 자주 깬 건 아닌지 편하게 말씀해주세요.",
        "그렇군요. 그럼 오늘 하루 어떤 일들이 있었는지 말해주세요.\n좋았던 일이든, 불편했던 일이든 자유롭게 말씀하셔도 괜찮아요.",
        "그 경험을 하면서 어떤 감정이 들었는지 자유롭게 표현해 주세요.\n여러 감정이 섞여 있어도 괜찮아요.",
        "왜 그런 감정이 들었는지 생각해보셨어요?\n상황이나 관계가 영향을 주었을 수도 있어요.",
        "오늘 하루도 정말 고생 많으셨어요.\n마지막으로, 오늘의 나에게 한마디 건네볼까요?\n'오늘 이만큼 버텨서 대견해' 같은 가벼운 말도 좋아요."
    )

    // [Phase 4] 3단계 위기 분류 시스템
    private val crisisLevel3 = listOf("죽고", "자살", "뛰어내", "목을", "손목", "유서", "마지막", "끝내고", "자해", "목숨")
    private val crisisLevel2 = listOf("사라지고", "없어지고", "살기 싫", "의미 없", "끝내", "망했", "수면제", "칼", "약 먹", "다 끝")
    private val crisisLevel1 = listOf("힘들", "지치", "우울", "불안", "두렵", "외로", "무서", "포기", "눈물")

    init {
        // 로컬 LLM 모델 로드 상태 관찰
        viewModelScope.launch {
            llmService.isModelLoaded.collect { loaded ->
                _uiState.value = _uiState.value.copy(isModelLoaded = loaded)
            }
        }

        // [선톡] 오늘 일기 존재 여부에 따라 분기
        viewModelScope.launch {
            // 서버에서 최신 유저 정보 동기화 (iOS syncUserInfo 대응)
            authRepo.syncUserInfo()

            // 실명 우선, 닉네임 대체, 없으면 "회원" (iOS 로직과 동일)
            val realName = authRepo.realName.first()
            val nickname = authRepo.nickname.first()
            var userName = realName ?: nickname ?: "회원"
            if (userName.startsWith("User ") || userName.startsWith("user_")) {
                userName = "회원"
            }

            // 오늘 날짜 계산 (yyyy-MM-dd)
            val sdf = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.getDefault())
            sdf.timeZone = java.util.TimeZone.getDefault()
            val todayStr = sdf.format(java.util.Date())

            // 서버에서 일기 목록 가져와서 오늘 일기 확인
            val todayDiary: Diary? = try {
                val result = diaryRepo.fetchDiaries()
                result.getOrNull()?.find { it.date == todayStr }
            } catch (e: Exception) {
                Log.e(TAG, "오늘 일기 확인 실패: ${e.message}")
                null
            }

            // 약간의 딜레이 후 메시지 추가
            kotlinx.coroutines.delay(500)

            if (_uiState.value.messages.isEmpty()) {
                if (todayDiary != null) {
                    // ━━━ 오늘 일기가 이미 존재 → 자유 대화 모드로 시작 ━━━
                    Log.d(TAG, "📋 오늘 일기 발견 (${todayDiary.date}) → 자유 대화 모드")

                    val diaryEvent = todayDiary.event ?: todayDiary.content ?: ""
                    val diaryEmotion = todayDiary.emotionDesc ?: ""
                    val diaryAnalysis = todayDiary.aiAnalysis ?: todayDiary.aiComment ?: ""

                    val diaryContextMsg = buildString {
                        append("안녕하세요, ${userName}님! 👋\n\n")
                        append("오늘 이미 일기를 작성해주셨네요 ✨\n")
                        if (diaryEvent.isNotBlank()) {
                            append("오늘 있었던 일: ${diaryEvent.take(80)}\n")
                        }
                        if (diaryEmotion.isNotBlank()) {
                            append("느낀 감정: ${diaryEmotion.take(80)}\n")
                        }
                        append("\n더 이야기하고 싶은 게 있으시면 편하게 말씀해주세요. 💬")
                    }

                    _uiState.value = _uiState.value.copy(
                        messages = listOf(ChatMessage(text = diaryContextMsg, isUser = false)),
                        currentStepIndex = 6,
                        isFlowCompleted = true,
                        isFreeChatMode = true
                    )
                } else {
                    // ━━━ 오늘 일기 없음 → 기존 6단계 가이드 플로우 시작 ━━━
                    val welcomeText = "안녕하세요, ${userName}님! 👋\n\n" +
                        "저는 AI 감정 케어 도우미 '마음온'이에요.\n" +
                        "지금부터 오늘 하루에 대해 몇 가지 여쭤볼게요.\n\n" +
                        "가장 먼저, 혹시 챙겨 드시는 약이 있다면\n오늘 잘 복용하셨나요? 💊"

                    _uiState.value = _uiState.value.copy(
                        messages = listOf(ChatMessage(text = welcomeText, isUser = false))
                    )
                }
            }
        }
    }

    /** 서버 AI ↔ 로컬 AI 전환 (iOS toggleAIMode 대응) */
    fun toggleAIMode() {
        val newMode = !_uiState.value.useServerAI
        _uiState.value = _uiState.value.copy(useServerAI = newMode)

        // 로컬 모드로 전환 시 모델 로드
        if (!newMode && !llmService.isModelLoaded.value) {
            viewModelScope.launch {
                llmService.loadModel(getApplication())
            }
        }
    }

    /** [Phase 4] SOS 다이얼로그 닫기 */
    fun dismissSOSDialog() {
        _uiState.value = _uiState.value.copy(showSOSDialog = false)
    }

    /**
     * 메시지 전송 — iOS sendMessage() 대응
     * 6단계 가이드형 플로우를 따름
     */
    fun sendMessage(text: String) {
        val state = _uiState.value

        // 자유 대화 모드이면 별도 처리 (AI 응답 중에도 메시지 전송 가능)
        if (state.isFreeChatMode) {
            sendFreeChat(text)
            return
        }

        // 가이드 플로우에서는 AI 응답 중 입력 차단
        if (state.isTyping) return

        if (state.isFlowCompleted) return
        if (state.currentStepIndex >= 6) return // 6단계 초과 방지

        val userMsg = ChatMessage(text = text, isUser = true)
        val currentMessages = _uiState.value.messages + userMsg

        // [Phase 4] 3단계 위기 감지
        val detectedLevel = when {
            crisisLevel3.any { text.contains(it) } -> 3
            crisisLevel2.any { text.contains(it) } -> 2
            crisisLevel1.any { text.contains(it) } -> 1
            else -> 0
        }

        val maxLevel = maxOf(_uiState.value.crisisLevel, detectedLevel)

        // 답변 저장
        val stepIdx = state.currentStepIndex
        collectedAnswers[stepIdx] = text
        val nextStepIndex = stepIdx + 1

        _uiState.value = _uiState.value.copy(
            messages = currentMessages,
            isTyping = true,
            currentStepIndex = nextStepIndex,
            crisisLevel = maxLevel,
            showCrisisBanner = maxLevel >= 2,
            showSOSDialog = detectedLevel >= 3
        )

        if (detectedLevel >= 3) {
            Log.w(TAG, "🚨 [Crisis] LEVEL 3 detected!")
        } else if (detectedLevel >= 2) {
            Log.w(TAG, "⚠️ [Crisis] LEVEL 2 detected!")
        }

        viewModelScope.launch {
            // 타이핑 딜레이 (iOS 1.2초 대응)
            kotlinx.coroutines.delay(1200)

            if (nextStepIndex < 6) {
                // 다음 질문 표시 (stepQuestions[nextStepIndex - 1])
                val questionText = stepQuestions[nextStepIndex - 1]
                val aiMsg = ChatMessage(text = questionText, isUser = false)
                _uiState.value = _uiState.value.copy(
                    messages = _uiState.value.messages + aiMsg,
                    isTyping = false
                )
            } else if (nextStepIndex == 6) {
                // 6단계 완료 → 분석 시작
                val closingMsg = ChatMessage(
                    text = "소중한 이야기들을 나눠주셔서 감사해요.\n다이어리를 기록하고 감정을 분석해 드릴게요. 잠시만 기다려주세요.",
                    isUser = false
                )
                _uiState.value = _uiState.value.copy(
                    messages = _uiState.value.messages + closingMsg,
                    isTyping = false,
                    isFlowCompleted = true
                )
                // 분석 시작
                startFinalAnalysis()
            }
        }
    }

    /**
     * 최종 분석 — iOS startFinalAnalysis() 대응
     * 수집된 답변으로 Diary 생성 → 서버 저장 → AI 분석 → 결과 채팅 표시
     */
    private fun startFinalAnalysis() {
        val qMed = collectedAnswers[0]   // 투약
        val qSleep = collectedAnswers[1] // 수면
        val qEvent = collectedAnswers[2] // 사건
        val qEmotion = collectedAnswers[3] // 감정
        val qMeaning = collectedAnswers[4] // 의미
        val qSelfTalk = collectedAnswers[5] // 독백

        // 투약 여부 유추 (iOS medPositiveWords 대응)
        val medPositiveWords = listOf("명", "모", "머", "머겄", "먹", "네", "응", "ㅇ", "Y", "y", "약", "타", "챙", "복용")
        val hasTakenMed = medPositiveWords.any { qMed.contains(it) }

        // 날짜 (iOS dateString 대응)
        val sdf = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
        sdf.timeZone = TimeZone.getDefault()
        val dateString = sdf.format(Date())

        _uiState.value = _uiState.value.copy(
            isAnalyzing = true,
            loadingHint = "📝 일기장에 기록을 옮기는 중..."
        )

        viewModelScope.launch {
            // ── 1단계: Diary 생성 및 서버 저장 ──
            val diary = Diary(
                date = dateString,
                moodLevel = 3, // 기본값 (AI가 나중에 분석)
                event = qEvent,
                content = qEvent,
                emotionDesc = qEmotion,
                emotionMeaning = qMeaning,
                selfTalk = qSelfTalk,
                sleepDesc = qSleep,
                sleepCondition = qSleep,
                weather = "맑음",
                temperature = 20.0,
                medicationTaken = hasTakenMed,
                medication = hasTakenMed,
                medicationDesc = qMed,
                aiPrediction = "분석 대기 중..."
            )

            // 서버 저장
            val saveResult = diaryRepo.saveDiary(diary)
            val savedDiaryId = saveResult.getOrNull()?.realId

            saveResult.onSuccess {
                Log.d(TAG, "✅ 일기 서버 저장 성공 (ID: $savedDiaryId)")
            }.onFailure { e ->
                Log.e(TAG, "❌ 일기 저장 실패: ${e.message}")
            }

            // ── 2단계: AI 분석 ──
            _uiState.value = _uiState.value.copy(
                loadingHint = if (_uiState.value.useServerAI) "🛡️ 마음 가이드 생성 중..." else "🔒 AI 마음 가이드 생성 중... (데이터는 보호됩니다)"
            )

            // 빈 AI 메시지 추가 (스트리밍 효과용)
            val placeholderMsg = ChatMessage(text = "", isUser = false)
            _uiState.value = _uiState.value.copy(
                messages = _uiState.value.messages + placeholderMsg,
                isTyping = true
            )

            val combinedText = "투약여부: $qMed\n사건: $qEvent\n감정: $qEmotion\n의미: $qMeaning\n혼잣말: $qSelfTalk\n수면: $qSleep"
            val analyzeInstruction = "[일기 전체를 요약하고, 사용자의 감정에 공감하며 한 문단의 따뜻한 조언을 제공하세요. 반드시 한국어를 사용하세요.]\n\n$combinedText"

            val aiAnalysisText: String = if (_uiState.value.useServerAI) {
                // ☁️ 서버 AI 분석
                getServerAnalysis(analyzeInstruction)
            } else {
                // 📱 로컬 LLM 분석
                getLocalAnalysis(combinedText)
            }

            // AI 분석 결과로 placeholder 교체
            val currentMsgs = _uiState.value.messages.toMutableList()
            if (currentMsgs.isNotEmpty()) {
                currentMsgs[currentMsgs.lastIndex] = ChatMessage(text = aiAnalysisText, isUser = false)
            }

            _uiState.value = _uiState.value.copy(
                messages = currentMsgs,
                isTyping = false,
                isAnalyzing = false,
                loadingHint = null
            )

            // ── 3단계: 서버에 AI 분석 결과 업데이트 ──
            if (savedDiaryId != null) {
                val updatedDiary = diary.copy(aiAnalysis = aiAnalysisText)
                diaryRepo.updateDiary(savedDiaryId, updatedDiary).onSuccess {
                    Log.d(TAG, "✅ AI 분석 결과 서버 업데이트 완료")
                }.onFailure { e ->
                    Log.e(TAG, "⚠️ AI 분석 결과 업데이트 실패: ${e.message}")
                }
            }

            // ── 4단계: 종료 멘트 + 자유 대화 전환 ──
            kotlinx.coroutines.delay(1000)

            val closingMsg = ChatMessage(
                text = "분석을 마치고 일기장에 보관해두었어요.\n오늘 하루도 수고 많으셨습니다. 😊",
                isUser = false
            )
            _uiState.value = _uiState.value.copy(
                messages = _uiState.value.messages + closingMsg,
                isSaved = true
            )

            // 자유 대화 전환 안내
            kotlinx.coroutines.delay(1500)

            val freeChatMsg = ChatMessage(
                text = "더 이야기하고 싶은 게 있으시면 편하게 말씀해주세요.\n오늘 있었던 일, 지금 느끼는 감정 등 자유롭게 대화할 수 있어요. 💬",
                isUser = false
            )
            _uiState.value = _uiState.value.copy(
                messages = _uiState.value.messages + freeChatMsg,
                isFreeChatMode = true
            )
        }
    }

    /**
     * 자유 대화 모드 — 6단계 일기 작성 완료 후 활성화
     * 이전 대화 기록을 history에 포함시켜 서버 AI에 전달
     */
    private fun sendFreeChat(text: String) {
        val userMsg = ChatMessage(text = text, isUser = true)

        // [Phase 4] 위기 감지 (자유 대화 중에도 동작)
        val detectedLevel = when {
            crisisLevel3.any { text.contains(it) } -> 3
            crisisLevel2.any { text.contains(it) } -> 2
            crisisLevel1.any { text.contains(it) } -> 1
            else -> 0
        }
        val maxLevel = maxOf(_uiState.value.crisisLevel, detectedLevel)

        _uiState.value = _uiState.value.copy(
            messages = _uiState.value.messages + userMsg,
            isTyping = true,
            crisisLevel = maxLevel,
            showCrisisBanner = maxLevel >= 2,
            showSOSDialog = detectedLevel >= 3
        )

        viewModelScope.launch {
            // 이전 대화 기록을 history 문자열로 조합 (최근 10턴 = 20개 메시지)
            val recentMessages = _uiState.value.messages.takeLast(20)
            val historyStr = recentMessages
                .dropLast(1) // 방금 추가한 userMsg 제외
                .joinToString("\n") { msg ->
                    if (msg.isUser) "User: ${msg.text.take(100)}"
                    else "AI: ${msg.text.take(100)}"
                }

            val aiResponseText: String = try {
                Log.d(TAG, "💬 [자유 대화] 서버 AI 요청")

                val response = ApiClient.chatApi.sendChat(
                    mapOf(
                        "text" to text,
                        "mode" to "reaction",
                        "history" to historyStr
                    )
                )

                if (response.isSuccessful && response.body() != null) {
                    val result = response.body()!!.displayText
                    Log.d(TAG, "✅ [자유 대화] 응답: ${result.take(50)}...")
                    if (result.isNotBlank()) result
                    else llmService.getEmergencyEmpathy(text)
                } else {
                    Log.e(TAG, "❌ [자유 대화] HTTP ${response.code()}")
                    llmService.getEmergencyEmpathy(text)
                }
            } catch (e: Exception) {
                Log.e(TAG, "❌ [자유 대화] 오류: ${e.message}")
                llmService.getEmergencyEmpathy(text)
            }

            val aiMsg = ChatMessage(text = aiResponseText, isUser = false)
            _uiState.value = _uiState.value.copy(
                messages = _uiState.value.messages + aiMsg,
                isTyping = false
            )
        }
    }

    /** 서버 AI 분석 — iOS chat/reaction endpoint 사용 */
    private suspend fun getServerAnalysis(analyzeText: String): String {
        return try {
            Log.d(TAG, "🚀 [서버 AI] 일기 분석 요청 시작")

            val response = ApiClient.chatApi.sendChat(
                mapOf(
                    "text" to analyzeText,
                    "mode" to "reaction",
                    "history" to "사용자가 방금 남긴 일기 기록입니다."
                )
            )

            if (response.isSuccessful && response.body() != null) {
                val result = response.body()!!.displayText
                Log.d(TAG, "✅ [서버 AI] 분석 완료: ${result.take(50)}...")
                if (result.isNotBlank()) result
                else llmService.getEmergencyEmpathy(analyzeText)
            } else {
                Log.e(TAG, "❌ [서버 AI] 분석 실패: HTTP ${response.code()}")
                llmService.getEmergencyEmpathy(analyzeText)
            }
        } catch (e: Exception) {
            Log.e(TAG, "❌ [서버 AI] 분석 오류: ${e.message}")
            llmService.getEmergencyEmpathy(analyzeText)
        }
    }

    /** 로컬 LLM 분석 — iOS generateUnifiedAnalysis 대응 */
    private suspend fun getLocalAnalysis(combinedText: String): String {
        if (!llmService.isModelLoaded.value) {
            llmService.loadModel(getApplication())
        }

        return if (llmService.isModelLoaded.value) {
            try {
                val (_, comment, _) = llmService.generateUnifiedAnalysis(combinedText)
                comment
            } catch (e: Exception) {
                llmService.getEmergencyEmpathy(combinedText)
            }
        } else {
            llmService.getEmergencyEmpathy(combinedText)
        }
    }
}
