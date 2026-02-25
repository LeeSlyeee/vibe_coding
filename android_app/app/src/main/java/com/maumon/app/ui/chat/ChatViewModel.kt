package com.maumon.app.ui.chat

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.maumon.app.data.api.ApiClient
import com.maumon.app.data.llm.LLMService
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class ChatUiState(
    val messages: List<ChatMessage> = emptyList(),
    val isTyping: Boolean = false,
    val showCrisisBanner: Boolean = false,
    val useServerAI: Boolean = true, // iOS useServerAI 대응
    val isModelLoaded: Boolean = false,
)

class ChatViewModel(application: Application) : AndroidViewModel(application) {

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState

    private val llmService = LLMService.getInstance()

    private val crisisKeywords = listOf("죽고", "자살", "뛰어내", "사라지고", "수면제")

    init {
        // 로컬 LLM 모델 로드 상태 관찰
        viewModelScope.launch {
            llmService.isModelLoaded.collect { loaded ->
                _uiState.value = _uiState.value.copy(isModelLoaded = loaded)
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

    fun sendMessage(text: String) {
        val userMsg = ChatMessage(text = text, isUser = true)
        val currentMessages = _uiState.value.messages + userMsg

        // 위기 감지
        val crisis = crisisKeywords.any { text.contains(it) }

        _uiState.value = _uiState.value.copy(
            messages = currentMessages,
            isTyping = true,
            showCrisisBanner = _uiState.value.showCrisisBanner || crisis
        )

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

    /** 로컬 LLM 응답 (iOS generateAnalysis 로컬 모드 대응) */
    private suspend fun getLocalResponse(text: String, messages: List<ChatMessage>): String {
        // 모델이 로드되지 않았으면 자동 로드
        if (!llmService.isModelLoaded.value) {
            llmService.loadModel(getApplication())
        }

        return if (llmService.isModelLoaded.value) {
            try {
                llmService.generateAdvice(text)
            } catch (e: Exception) {
                llmService.getEmergencyEmpathy(text)
            }
        } else {
            // 모델 로드 실패 시 Fallback
            llmService.getEmergencyEmpathy(text)
        }
    }
}
