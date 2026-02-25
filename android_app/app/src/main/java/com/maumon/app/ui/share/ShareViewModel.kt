package com.maumon.app.ui.share

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.maumon.app.data.repository.ShareRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class ShareUiState(
    val isLoading: Boolean = false,
    val generatedCode: String? = null,
    val connectedUsers: List<Map<String, Any>> = emptyList(),
    val errorMessage: String? = null,
    val successMessage: String? = null,
)

class ShareViewModel : ViewModel() {
    private val shareRepo = ShareRepository()
    private val _uiState = MutableStateFlow(ShareUiState())
    val uiState: StateFlow<ShareUiState> = _uiState

    init { loadConnectedUsers() }

    fun generateCode() {
        _uiState.value = _uiState.value.copy(isLoading = true, errorMessage = null)
        viewModelScope.launch {
            shareRepo.generateCode(emptyMap())
                .onSuccess { resp ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        generatedCode = resp["code"]?.toString()
                    )
                }
                .onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        errorMessage = "코드 생성 실패: ${e.message}"
                    )
                }
        }
    }

    fun connectWithCode(code: String) {
        _uiState.value = _uiState.value.copy(isLoading = true, errorMessage = null, successMessage = null)
        viewModelScope.launch {
            shareRepo.connectWithCode(code)
                .onSuccess { msg ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        successMessage = msg
                    )
                    loadConnectedUsers()
                }
                .onFailure { e ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        errorMessage = "연결 실패: ${e.message}"
                    )
                }
        }
    }

    fun disconnect(targetId: String) {
        viewModelScope.launch {
            shareRepo.disconnect(mapOf("target_id" to targetId))
                .onSuccess { loadConnectedUsers() }
                .onFailure { e ->
                    _uiState.value = _uiState.value.copy(errorMessage = "해제 실패: ${e.message}")
                }
        }
    }

    @Suppress("UNCHECKED_CAST")
    private fun loadConnectedUsers() {
        viewModelScope.launch {
            shareRepo.getConnectedList("viewer")
                .onSuccess { result ->
                    val data = result["data"] as? List<Map<String, Any>> ?: emptyList()
                    _uiState.value = _uiState.value.copy(connectedUsers = data)
                }
        }
    }
}
