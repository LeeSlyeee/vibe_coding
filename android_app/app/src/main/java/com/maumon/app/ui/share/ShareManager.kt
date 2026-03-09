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
        @SerializedName("connected_at") val connectedAt: String? = null,
        @SerializedName("share_mood") val shareMood: Boolean? = true,
        @SerializedName("share_report") val shareReport: Boolean? = false,
        @SerializedName("share_crisis") val shareCrisis: Boolean? = true
    )

    data class SharedStats(
        @SerializedName("sharer_name") val sharerName: String = "",
        @SerializedName("avg_mood") val avgMood: Double? = null,
        @SerializedName("has_safety_concern") val hasSafetyConcern: Boolean? = null,
        @SerializedName("mood_trend") val moodTrend: List<DailyMood> = emptyList(),
        @SerializedName("recent_status") val recentStatus: String = "",
        @SerializedName("total_entries") val totalEntries: Int = 0,
        @SerializedName("writing_streak") val writingStreak: Int = 0,
        @SerializedName("mood_restricted") val moodRestricted: Boolean? = null,
        @SerializedName("narrative_summary") val narrativeSummary: List<String>? = null
    )

    data class DailyMood(
        val date: String = "",
        val mood: Int = 3
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

    // MARK: - Guardian Alert Model
    data class GuardianAlert(
        val type: String = "",
        @SerializedName("sharer_id") val sharerId: Int = 0,
        @SerializedName("sharer_name") val sharerName: String = "",
        val message: String = "",
        val severity: String = "", // "high", "medium", "low"
        val icon: String = "",
        @SerializedName("action_guide") val actionGuide: List<String>? = null,
        @SerializedName("avg_mood") val avgMood: Double? = null
    ) {
        val id: String get() = "${type}_$sharerId"
    }

    private val _guardianAlerts = MutableStateFlow<List<GuardianAlert>>(emptyList())
    val guardianAlerts: StateFlow<List<GuardianAlert>> = _guardianAlerts.asStateFlow()

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
                val responseBody = response.body()
                if (response.isSuccessful && responseBody != null) {
                    val code = responseBody["code"]?.toString() ?: ""
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
                val responseBody = response.body()
                if (response.isSuccessful && responseBody != null) {
                    @Suppress("UNCHECKED_CAST")
                    val list = (responseBody["data"] as? List<Map<String, Any>>)?.map { item ->
                        SharedUser(
                            id = item["id"]?.toString() ?: "",
                            name = item["name"]?.toString() ?: "",
                            role = item["role"]?.toString(),
                            birthDate = item["birth_date"]?.toString(),
                            connectedAt = item["connected_at"]?.toString(),
                            shareMood = item["share_mood"] as? Boolean ?: true,
                            shareReport = item["share_report"] as? Boolean ?: false,
                            shareCrisis = item["share_crisis"] as? Boolean ?: true
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

    /** 4. 보호자 알림 이력 조회 (iOS fetchGuardianAlerts 대응) */
    suspend fun fetchGuardianAlerts() {
        withContext(Dispatchers.IO) {
            try {
                val response = ApiClient.flaskApi.getGuardianAlerts()
                val responseBody = response.body()
                if (response.isSuccessful && responseBody != null) {
                    @Suppress("UNCHECKED_CAST")
                    val alertsArray = responseBody["alerts"] as? List<Map<String, Any>>
                    if (alertsArray != null) {
                        val gson = com.google.gson.Gson()
                        val jsonElement = gson.toJsonTree(alertsArray)
                        val alerts = gson.fromJson(jsonElement, Array<GuardianAlert>::class.java).toList()
                        _guardianAlerts.value = alerts
                        Log.d(TAG, "✅ 알림 이력 조회 성공: ${alerts.size}건")
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "❌ 알림 이력 조회 실패: ${e.message}")
            }
        }
    }

    /** 5. 연결 해제 (iOS disconnect 대응) */
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

    /** 6. 공유 범위 설정 (Phase 6) */
    suspend fun updateShareScope(viewerId: String, shareMood: Boolean, shareReport: Boolean, shareCrisis: Boolean): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                val body = mapOf(
                    "viewer_id" to viewerId.toInt(),
                    "share_mood" to shareMood,
                    "share_report" to shareReport,
                    "share_crisis" to shareCrisis
                )
                val response = ApiClient.flaskApi.updateShareScope(body)
                if (response.isSuccessful) {
                    fetchList("sharer") // 갱신
                    true
                } else {
                    false
                }
            } catch (e: Exception) {
                Log.e(TAG, "❌ 공유 범위 설정 에러: ${e.message}")
                false
            }
        }
    }

    /** 7. 알림 설정 (Phase 5) */
    suspend fun updateAlertSettings(sharerId: String, alertMoodDrop: Boolean, alertCrisis: Boolean, alertInactivity: Boolean): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                val body = mapOf(
                    "sharer_id" to sharerId.toInt(),
                    "alert_mood_drop" to alertMoodDrop,
                    "alert_crisis" to alertCrisis,
                    "alert_inactivity" to alertInactivity
                )
                val response = ApiClient.flaskApi.updateAlertSettings(body)
                if (response.isSuccessful) {
                    fetchList("viewer")
                    true
                } else {
                    false
                }
            } catch (e: Exception) {
                Log.e(TAG, "❌ 알림 설정 에러: ${e.message}")
                false
            }
        }
    }

    /** 8. 역할 변경 */
    suspend fun updateRole(sharerId: String, role: String): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                val body = mapOf(
                    "sharer_id" to sharerId.toInt(),
                    "role" to role
                )
                val response = ApiClient.flaskApi.updateRole(body)
                if (response.isSuccessful) {
                    fetchList("viewer")
                    true
                } else {
                    false
                }
            } catch (e: Exception) {
                Log.e(TAG, "❌ 역할 변경 에러: ${e.message}")
                false
            }
        }
    }
}
