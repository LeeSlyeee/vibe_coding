package com.maumon.app

import android.os.Bundle
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

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        // [Push Notification] FCM 초기화
        initFirebase()

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

    /**
     * Firebase 초기화 — google-services.json 없으면 건너뜀
     */
    private fun initFirebase() {
        try {
            MaumFirebaseService.createNotificationChannels(this)
            MaumFirebaseService.registerTokenToServer(this)
        } catch (e: Exception) {
            android.util.Log.w("MainActivity", "⚠️ Firebase 미설정 상태 (google-services.json 필요): ${e.message}")
        }
    }
}
