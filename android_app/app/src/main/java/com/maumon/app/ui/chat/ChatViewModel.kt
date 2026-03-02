package com.maumon.app.ui.chat

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.maumon.app.data.api.ApiClient
import com.maumon.app.data.repository.AuthRepository
import com.maumon.app.data.llm.LLMService
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

data class ChatUiState(
    val messages: List<ChatMessage> = emptyList(),
    val isTyping: Boolean = false,
    val showCrisisBanner: Boolean = false,
    val crisisLevel: Int = 0, // [Phase 4] 0=안전, 1=관심, 2=주의, 3=위험
    val showSOSDialog: Boolean = false, // [Phase 4] Level 3 즉시 모달
    val useServerAI: Boolean = true,
    val isModelLoaded: Boolean = false,
)

class ChatViewModel(application: Application) : AndroidViewModel(application) {

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState

    private val llmService = LLMService.getInstance()
    private val authRepo = AuthRepository(application.applicationContext)

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

        // [선톡] iOS AppChatView.swift의 welcomeText 대응 — AI가 먼저 인사
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

            val welcomeText = "안녕하세요, ${userName}님! 👋\n\n" +
                "저는 AI 감정 케어 도우미 '마음온'이에요.\n" +
                "전문 상담사는 아니지만, 당신의 이야기를 조용히 들을 준비가 되어 있어요.\n\n" +
                "오늘 하루 중 기억에 남는 순간이 있었나요? 🌡️"

            // 약간의 딜레이 후 메시지 추가 (iOS 0.5초 딜레이 대응)
            kotlinx.coroutines.delay(500)

            if (_uiState.value.messages.isEmpty()) {
                val welcomeMsg = ChatMessage(text = welcomeText, isUser = false)
                _uiState.value = _uiState.value.copy(
                    messages = listOf(welcomeMsg)
                )
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

    fun sendMessage(text: String) {
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

        _uiState.value = _uiState.value.copy(
            messages = currentMessages,
            isTyping = true,
            crisisLevel = maxLevel,
            showCrisisBanner = maxLevel >= 2,
            showSOSDialog = detectedLevel >= 3 // Level 3: 즉시 SOS 다이얼로그
        )
        
        if (detectedLevel >= 3) {
            android.util.Log.w("ChatVM", "🚨 [Crisis] LEVEL 3 detected!")
        } else if (detectedLevel >= 2) {
            android.util.Log.w("ChatVM", "⚠️ [Crisis] LEVEL 2 detected!")
        }

        viewModelScope.launch {
            val aiText = if (_uiState.value.useServerAI) {
                // ☁️ 서버 AI 모드
                getServerResponse(text, currentMessages)
            } else {
                // 📱 로컬 LLM 모드
                getLocalResponse(text, currentMessages)
            }

            val aiMsg = ChatMessage(text = aiText, isUser = false)
            _uiState.value = _uiState.value.copy(
                messages = _uiState.value.messages + aiMsg,
                isTyping = false
            )
        }
    }

    /** 서버 AI 응답 — iOS APIService.sendChatMessage() 대응 */
    private suspend fun getServerResponse(text: String, messages: List<ChatMessage>): String {
        return try {
            // iOS와 동일한 history 포맷
            val history = messages.takeLast(4).joinToString("\n") { msg ->
                val role = if (msg.isUser) "User" else "Model"
                "$role: ${msg.text.take(300)}"
            }

            android.util.Log.d("ChatVM", "🚀 [서버 AI] chat/reaction 요청 시작 (timeout: 300s)")

            // ✅ chatApi 사용 — 300초 타임아웃 (iOS timeoutInterval: 300.0 대응)
            val response = ApiClient.chatApi.sendChat(
                mapOf(
                    "text" to text,
                    "mode" to "reaction",
                    "history" to history
                )
            )

            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                val result = body.displayText
                android.util.Log.d("ChatVM", "✅ [서버 AI] 응답 수신 완료: ${result.take(50)}...")
                if (result.isNotBlank()) result
                else "서버에서 빈 응답이 돌아왔습니다. 잠시 후 다시 시도해주세요."
            } else {
                val code = response.code()
                val errBody = response.errorBody()?.string()?.take(200) ?: ""
                android.util.Log.e("ChatVM", "❌ [서버 AI] HTTP $code: $errBody")
                "서버 응답을 처리할 수 없습니다 (HTTP $code).\n잠시 후 다시 시도해주세요."
            }
        } catch (e: java.net.SocketTimeoutException) {
            android.util.Log.e("ChatVM", "⏱️ [서버 AI] 타임아웃: ${e.message}")
            "서버 응답 대기 시간을 초과했습니다.\nAI가 생각 중이니 잠시 후 다시 시도해주세요."
        } catch (e: java.net.ConnectException) {
            android.util.Log.e("ChatVM", "🔌 [서버 AI] 연결 실패: ${e.message}")
            "서버에 연결할 수 없습니다.\n네트워크 상태를 확인해주세요."
        } catch (e: Exception) {
            android.util.Log.e("ChatVM", "❌ [서버 AI] 오류: ${e.javaClass.simpleName} - ${e.message}")
            "네트워크 오류가 발생했습니다.\n${e.message}"
        }
    }

    /** 로컬 LLM 응답 (iOS generateAnalysis 로컬 채팅 모드 대응) */
    private suspend fun getLocalResponse(text: String, messages: List<ChatMessage>): String {
        // 모델이 로드되지 않았으면 자동 로드
        if (!llmService.isModelLoaded.value) {
            llmService.loadModel(getApplication())
        }

        return if (llmService.isModelLoaded.value) {
            try {
                // 대화 히스토리 구성
                val history = messages.map { Pair(it.isUser, it.text) }
                llmService.generateChatResponse(text, history)
            } catch (e: Exception) {
                llmService.getEmergencyEmpathy(text)
            }
        } else {
            // 모델 로드 실패 시 Fallback
            llmService.getEmergencyEmpathy(text)
        }
    }
}
