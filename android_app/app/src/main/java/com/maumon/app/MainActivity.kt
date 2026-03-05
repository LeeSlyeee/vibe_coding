package com.maumon.app

import android.content.Intent
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.maumon.app.data.push.MaumFirebaseService
import com.maumon.app.ui.MaumOnApp
import com.maumon.app.ui.theme.MaumOnTheme
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        // [Push Notification] FCM 초기화
        initFirebase()

        // 딥링크 체크 (푸시 터치로 앱이 열린 경우)
        handleDeepLink(intent)

        setContent {
            MaumOnTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    MaumOnApp()
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        // 앱이 이미 떠있는 상태에서 푸시 터치
        handleDeepLink(intent)
    }

    private fun handleDeepLink(intent: Intent?) {
        if (intent == null) return

        // 로그: 인텐트에 들어있는 모든 extras 확인
        intent.extras?.let { extras ->
            Log.d("MainActivity", "📮 Intent extras: ${extras.keySet().map { "$it=${extras.get(it)}" }}")
        }

        // 방법 1: 우리가 직접 만든 알림 (포그라운드) → deep_link 키
        val deepLink = intent.getStringExtra("deep_link")
        // 방법 2: FCM 시스템 알림 (백그라운드) → data payload의 type 키가 직접 들어옴
        val fcmType = intent.getStringExtra("type")

        val route = when {
            deepLink == "weekly_letter" -> "weekly_letter"
            fcmType == "weekly_letter" -> "weekly_letter"
            else -> null
        }

        if (route != null) {
            Log.d("MainActivity", "📮 딥링크 감지: $route (deepLink=$deepLink, fcmType=$fcmType)")
            DeepLinkRouter.navigate(route)
        }
    }

    /**
     * Firebase 초기화 — google-services.json 없으면 건너뜀
     */
    private fun initFirebase() {
        try {
            MaumFirebaseService.createNotificationChannels(this)
            MaumFirebaseService.registerTokenToServer(this)
        } catch (e: Exception) {
            Log.w("MainActivity", "⚠️ Firebase 미설정 상태: ${e.message}")
        }
    }
}

/**
 * 전역 딥링크 라우터 - StateFlow로 Compose에서 관찰 가능
 */
object DeepLinkRouter {
    private val _pendingRoute = MutableStateFlow<String?>(null)
    val pendingRoute: StateFlow<String?> = _pendingRoute

    fun navigate(route: String) {
        _pendingRoute.value = route
    }

    fun consume() {
        _pendingRoute.value = null
    }
}
