package com.maumon.app.ui.share

import android.content.Context
import android.util.Log
import com.maumon.app.data.api.ApiClient
import com.google.gson.annotations.SerializedName
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext

/**
 * 공유 매니저 - iOS ShareManager.swift 대응
 * /api/share/ 엔드포인트 사용
 */
object ShareManager {
    private const val TAG = "ShareManager"

    // Models (iOS SharedUser, SharedStats 대응)
    data class SharedUser(
        val id: String,
        val name: String,
        val role: String? = null,
        @SerializedName("birth_date") val birthDate: String? = null,
        @SerializedName("connected_at") val connectedAt: String? = null
    )

    data class SharedStats(
        @SerializedName("user_name") val userName: String = "",
        @SerializedName("risk_level") val riskLevel: Int = 0,
        @SerializedName("latest_report") val latestReport: String = "",
        @SerializedName("recent_moods") val recentMoods: List<DailyMood> = emptyList(),
        @SerializedName("last_sync") val lastSync: String = ""
    )

    data class DailyMood(
        val date: String = "",
        val mood: Int = 3,
        val label: String = ""
    )

    // State
    private val _myCode = MutableStateFlow("")
    val myCode: StateFlow<String> = _myCode.asStateFlow()

    private val _connectedUsers = MutableStateFlow<List<SharedUser>>(emptyList())
    val connectedUsers: StateFlow<List<SharedUser>> = _connectedUsers.asStateFlow()

    private val _myGuardians = MutableStateFlow<List<SharedUser>>(emptyList())
    val myGuardians: StateFlow<List<SharedUser>> = _myGuardians.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _errorMessage = MutableStateFlow("")
    val errorMessage: StateFlow<String> = _errorMessage.asStateFlow()

    /** 1. 공유 코드 발급 (iOS generateCode 대응) */
    suspend fun generateCode(context: Context): String? {
        return withContext(Dispatchers.IO) {
            try {
                val prefs = context.getSharedPreferences("auth", Context.MODE_PRIVATE)
                val userId = prefs.getString("userId", "") ?: ""
                val username = prefs.getString("username", "") ?: ""
                val nickname = prefs.getString("nickname", "사용자") ?: "사용자"

                val body = mapOf(
                    "user_id" to userId,
                    "username" to username,
                    "user_name" to nickname
                )

                val response = ApiClient.flaskApi.generateShareCode(body)
                if (response.isSuccessful && response.body() != null) {
                    val code = response.body()!!["code"]?.toString() ?: ""
                    _myCode.value = code
                    Log.d(TAG, "✅ 코드 발급 성공: $code")
                    code
                } else {
                    Log.e(TAG, "❌ 코드 발급 실패: ${response.code()}")
                    null
                }
            } catch (e: Exception) {
                Log.e(TAG, "❌ 코드 발급 에러: ${e.message}")
                null
            }
        }
    }

    /** 2. 코드로 연결 (iOS connectWithCode 대응) */
    suspend fun connectWithCode(code: String): Pair<Boolean, String> {
        return withContext(Dispatchers.IO) {
            try {
                val body = mapOf("code" to code)
                val response = ApiClient.flaskApi.connectShare(body)
                if (response.isSuccessful) {
                    val msg = response.body()?.get("message")?.toString() ?: "연결 성공"
                    fetchList("viewer")
                    Pair(true, msg)
                } else {
                    Pair(false, "연결 실패 (${response.code()})")
                }
            } catch (e: Exception) {
                Pair(false, "네트워크 오류: ${e.message}")
            }
        }
    }

    /** 3. 연결 목록 조회 (iOS fetchList 대응) */
    suspend fun fetchList(role: String = "viewer") {
        withContext(Dispatchers.IO) {
            try {
                _isLoading.value = true
                _errorMessage.value = ""

                val response = ApiClient.flaskApi.getShareList(role)
                if (response.isSuccessful && response.body() != null) {
                    val data = response.body()!!
                    @Suppress("UNCHECKED_CAST")
                    val list = (data["data"] as? List<Map<String, Any>>)?.map { item ->
                        SharedUser(
                            id = item["id"]?.toString() ?: "",
                            name = item["name"]?.toString() ?: "",
                            role = item["role"]?.toString(),
                            birthDate = item["birth_date"]?.toString(),
                            connectedAt = item["connected_at"]?.toString()
                        )
                    } ?: emptyList()

                    if (role == "viewer") {
                        _connectedUsers.value = list
                    } else {
                        _myGuardians.value = list
                    }
                    Log.d(TAG, "✅ 목록 조회 성공: ${list.size}명 ($role)")
                } else {
                    _errorMessage.value = "목록 조회 실패"
                }
            } catch (e: Exception) {
                _errorMessage.value = "통신 오류: ${e.message}"
                Log.e(TAG, "❌ 목록 조회 에러: ${e.message}")
            } finally {
                _isLoading.value = false
            }
        }
    }

    /** 4. 연결 해제 (iOS disconnect 대응) */
    suspend fun disconnect(targetId: String, context: Context): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                val prefs = context.getSharedPreferences("auth", Context.MODE_PRIVATE)
                val userId = prefs.getString("userId", "") ?: ""
                val username = prefs.getString("username", "") ?: ""

                val body = mapOf(
                    "user_id" to userId,
                    "username" to username,
                    "target_id" to targetId
                )

                val response = ApiClient.flaskApi.disconnectShare(body)
                if (response.isSuccessful) {
                    fetchList("viewer")
                    fetchList("sharer")
                    true
                } else false
            } catch (e: Exception) {
                Log.e(TAG, "❌ 연결 해제 에러: ${e.message}")
                false
            }
        }
    }
}
