package com.maumon.app.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.maumon.app.data.model.Diary
import com.maumon.app.data.repository.AuthRepository
import com.maumon.app.ui.diary.DiaryDetailScreen
import com.maumon.app.ui.diary.DiaryWriteScreen
import com.maumon.app.ui.kick.WeeklyLetterScreen
import com.maumon.app.ui.kick.RelationalMapScreen
import com.maumon.app.ui.login.LoginScreen
import com.maumon.app.ui.main.MainScreen
import kotlinx.coroutines.launch

/**
 * 앱 전체 네비게이션 - 로그인/메인/일기작성/일기상세 라우팅
 */
@Composable
fun MaumOnApp() {
    val navController = rememberNavController()
    val context = LocalContext.current
    val authRepo = remember { AuthRepository(context) }
    var isCheckingAuth by remember { mutableStateOf(true) }
    var startDestination by remember { mutableStateOf("login") }
    var isLoggedIn by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    // 선택된 일기 (상세 화면용)
    var selectedDiary by remember { mutableStateOf<Diary?>(null) }
    // 수정할 일기 (작성 화면용)
    var editDiary by remember { mutableStateOf<Diary?>(null) }

    // 앱 시작 시 저장된 토큰 확인
    LaunchedEffect(Unit) {
        isLoggedIn = authRepo.restoreToken()
        startDestination = if (isLoggedIn) "main" else "login"
        isCheckingAuth = false
    }

    val pendingRoute by com.maumon.app.DeepLinkRouter.pendingRoute.collectAsState()
    LaunchedEffect(pendingRoute, isCheckingAuth, isLoggedIn) {
        val route = pendingRoute ?: return@LaunchedEffect
        if (!isCheckingAuth && isLoggedIn) {
            var success = false
            var retryCount = 0
            while (!success && retryCount < 10) {
                try {
                    // StartDestination 또는 현재 뷰가 존재할 때만 안전하게 이동
                    if (navController.currentBackStackEntry != null) {
                        navController.navigate(route) {
                            launchSingleTop = true
                        }
                        success = true
                        com.maumon.app.DeepLinkRouter.consume()
                        android.util.Log.d("MaumOnApp", "✅ 딥링크 네비게이션 성공: $route")
                    } else {
                        throw IllegalStateException("NavHost is not fully initialized yet")
                    }
                } catch (e: Exception) {
                    retryCount++
                    android.util.Log.w("MaumOnApp", "⏳ 딥링크 네비게이션 대기 중 (${retryCount}/10): ${e.message}")
                    kotlinx.coroutines.delay(300)
                }
            }
            if (!success) {
                android.util.Log.e("MaumOnApp", "❌ 딥링크 네비게이션 최종 실패")
                com.maumon.app.DeepLinkRouter.consume() // 너무 오래 실패하면 어쩔 수 없이 버림
            }
        }
    }

    if (isCheckingAuth) {
        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            CircularProgressIndicator(color = MaterialTheme.colorScheme.primary)
        }
    } else {
        NavHost(
            navController = navController,
            startDestination = startDestination
        ) {
            // 로그인
            composable("login") {
                LoginScreen(
                    onLoginSuccess = {
                        isLoggedIn = true
                        navController.navigate("main") {
                            popUpTo("login") { inclusive = true }
                        }
                    }
                )
            }

            // 메인 (탭 네비게이션)
            composable("main") {
                MainScreen(
                    onLogout = {
                        scope.launch {
                            authRepo.logout()
                            isLoggedIn = false
                            navController.navigate("login") {
                                popUpTo("main") { inclusive = true }
                            }
                        }
                    },
                    onWriteDiary = { dateStr ->
                        navController.navigate("diary_write/$dateStr")
                    },
                    onViewDiary = { diary ->
                        selectedDiary = diary
                        navController.navigate("diary_detail")
                    },
                    onNavigateToWeeklyLetter = {
                        navController.navigate("weekly_letter")
                    },
                    onNavigateToRelationalMap = {
                        navController.navigate("relational_map")
                    }
                )
            }

            // 일기 작성
            composable(
                route = "diary_write/{dateStr}",
                arguments = listOf(navArgument("dateStr") { type = NavType.StringType })
            ) { backStackEntry ->
                val dateStr = backStackEntry.arguments?.getString("dateStr") ?: ""
                DiaryWriteScreen(
                    dateStr = dateStr,
                    diaryToEdit = editDiary,
                    onDismiss = {
                        editDiary = null
                        navController.popBackStack()
                    },
                    onSaved = { editDiary = null }
                )
            }

            // 일기 상세
            composable("diary_detail") {
                selectedDiary?.let { diary ->
                    DiaryDetailScreen(
                        diary = diary,
                        onBack = { navController.popBackStack() },
                        onEdit = {
                            editDiary = diary
                            diary.date?.let { date ->
                                navController.navigate("diary_write/$date")
                            }
                        },
                        onDelete = {
                            navController.popBackStack()
                        }
                    )
                }
            }

            // Kick: 주간 편지
            composable(
                route = "weekly_letter?letterId={letterId}",
                arguments = listOf(navArgument("letterId") { 
                    type = NavType.StringType
                    nullable = true
                })
            ) { backStackEntry ->
                val letterIdStr = backStackEntry.arguments?.getString("letterId")
                val targetLetterId = letterIdStr?.toIntOrNull()
                
                WeeklyLetterScreen(
                    targetLetterId = targetLetterId,
                    onBack = { navController.popBackStack() }
                )
            }

            // Kick: 마음 별자리
            composable("relational_map") {
                RelationalMapScreen(
                    onBack = { navController.popBackStack() }
                )
            }

            // 보호자 연동 (Deep Link 용)
            composable("share") {
                com.maumon.app.ui.share.ShareScreen(
                    onBack = { navController.popBackStack() }
                )
            }

            // 공유 통계 보기 (Deep Link 용)
            composable(
                route = "shared_stats/{targetId}",
                arguments = listOf(navArgument("targetId") { type = NavType.StringType })
            ) { backStackEntry ->
                val targetId = backStackEntry.arguments?.getString("targetId") ?: ""
                com.maumon.app.ui.share.SharedStatsScreen(
                    targetId = targetId,
                    targetName = "내담자", // 기본값 (API에서 가져오거나 목록에서 추출 권장)
                    onBack = { navController.popBackStack() }
                )
            }
        }
    }
}
