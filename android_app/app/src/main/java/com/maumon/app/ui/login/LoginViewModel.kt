package com.maumon.app.ui.login

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.maumon.app.data.repository.AuthRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class LoginUiState(
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val isSuccess: Boolean = false,
)

class LoginViewModel(app: Application) : AndroidViewModel(app) {

    private val authRepo = AuthRepository(app.applicationContext)

    private val _uiState = MutableStateFlow(LoginUiState())
    val uiState: StateFlow<LoginUiState> = _uiState

    fun login(username: String, password: String) {
        _uiState.value = LoginUiState(isLoading = true)
        viewModelScope.launch {
            val result = authRepo.login(username, password)
            result.onSuccess {
                // 유저 정보 동기화
                authRepo.syncUserInfo()
                _uiState.value = LoginUiState(isSuccess = true)
            }.onFailure { e ->
                _uiState.value = LoginUiState(
                    errorMessage = parseError(e.message)
                )
            }
        }
    }

    fun register(username: String, password: String, name: String) {
        _uiState.value = LoginUiState(isLoading = true)
        viewModelScope.launch {
            val result = authRepo.register(username, password, name)
            result.onSuccess {
                _uiState.value = LoginUiState(isSuccess = true)
            }.onFailure { e ->
                _uiState.value = LoginUiState(
                    errorMessage = parseError(e.message)
                )
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(errorMessage = null)
    }

    private fun parseError(msg: String?): String {
        if (msg == null) return "알 수 없는 오류"
        return when {
            msg.contains("401") -> "아이디 또는 비밀번호가 틀렸습니다."
            msg.contains("409") -> "이미 존재하는 아이디입니다."
            msg.contains("Unable to resolve host") -> "서버에 연결할 수 없습니다."
            msg.contains("timeout") -> "서버 응답 시간이 초과되었습니다."
            else -> msg
        }
    }
}
