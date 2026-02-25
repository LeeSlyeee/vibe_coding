package com.maumon.app.ui.settings

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.maumon.app.data.repository.AuthRepository
import com.maumon.app.data.repository.B2GRepository
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

data class SettingsUiState(
    val username: String? = null,
    val nickname: String? = null,
    val realName: String? = null,
    val birthDate: String? = null,
    val isLoggedIn: Boolean = false,
    val isLoading: Boolean = false,
    val message: String? = null,
    // B2G 상태
    val b2gCenterCode: String = "",
    val b2gIsLinked: Boolean = false,
    val b2gCenterName: String = "",
    val b2gLastSync: Long = 0L,
)

class SettingsViewModel(app: Application) : AndroidViewModel(app) {

    private val authRepo = AuthRepository(app.applicationContext)
    private val b2gRepo = B2GRepository(app.applicationContext)

    private val _uiState = MutableStateFlow(SettingsUiState())
    val uiState: StateFlow<SettingsUiState> = _uiState

    init {
        // Collect user data flows
        viewModelScope.launch {
            combine(
                authRepo.isLoggedIn,
                authRepo.username,
                authRepo.nickname,
                authRepo.realName,
                authRepo.birthDate
            ) { loggedIn, username, nickname, realName, birthDate ->
                SettingsUiState(
                    isLoggedIn = loggedIn,
                    username = username,
                    nickname = nickname,
                    realName = realName,
                    birthDate = birthDate,
                )
            }.collect { state ->
                _uiState.update { current ->
                    current.copy(
                        isLoggedIn = state.isLoggedIn,
                        username = state.username,
                        nickname = state.nickname,
                        realName = state.realName,
                        birthDate = state.birthDate,
                    )
                }
            }
        }

        // Collect B2G state flows
        viewModelScope.launch {
            combine(
                b2gRepo.isLinked,
                b2gRepo.centerCode,
                b2gRepo.centerName,
                b2gRepo.lastSyncDate
            ) { linked, code, name, sync ->
                Triple(linked, code, Pair(name, sync))
            }.collect { (linked, code, pair) ->
                _uiState.update { current ->
                    current.copy(
                        b2gIsLinked = linked,
                        b2gCenterCode = code,
                        b2gCenterName = pair.first,
                        b2gLastSync = pair.second,
                    )
                }
            }
        }
    }

    /** 서버에서 유저 정보 다시 가져오기 */
    fun refreshUserInfo() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            authRepo.syncUserInfo()
            _uiState.update { it.copy(isLoading = false) }
        }
    }

    /** 닉네임 변경 */
    fun updateNickname(newNickname: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            val result = authRepo.updateProfile(newNickname)
            result.onSuccess {
                _uiState.update { it.copy(isLoading = false, message = "닉네임이 변경되었습니다.") }
            }.onFailure { e ->
                _uiState.update { it.copy(isLoading = false, message = "닉네임 변경 실패: ${e.message}") }
            }
        }
    }

    /** 생년월일 변경 */
    fun updateBirthDate(dateStr: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            val result = authRepo.updateBirthDate(dateStr)
            result.onSuccess {
                _uiState.update { it.copy(isLoading = false, message = "생년월일이 변경되었습니다.") }
            }.onFailure { e ->
                _uiState.update { it.copy(isLoading = false, message = "생년월일 변경 실패: ${e.message}") }
            }
        }
    }

    /** B2G 기관 코드 연결 */
    fun connectB2G(code: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            val (success, message) = b2gRepo.connect(code)
            _uiState.update { it.copy(isLoading = false, message = message) }
        }
    }

    /** B2G 기관 연동 해제 */
    fun disconnectB2G() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            b2gRepo.disconnect()
            _uiState.update { it.copy(isLoading = false, message = "기관 연동이 해제되었습니다.") }
        }
    }

    /** B2G 데이터 동기화 — iOS B2GManager.syncData() 대응 */
    fun syncB2G() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            val (success, message) = b2gRepo.syncData(force = true)
            _uiState.update { it.copy(isLoading = false, message = message) }
        }
    }

    /** 메시지 표시 */
    fun showMessage(msg: String) {
        _uiState.update { it.copy(message = msg) }
    }

    /** 메시지 소비 */
    fun clearMessage() {
        _uiState.update { it.copy(message = null) }
    }
}
