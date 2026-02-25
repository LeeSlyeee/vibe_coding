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
    val scope = rememberCoroutineScope()

    // 선택된 일기 (상세 화면용)
    var selectedDiary by remember { mutableStateOf<Diary?>(null) }
    // 수정할 일기 (작성 화면용)
    var editDiary by remember { mutableStateOf<Diary?>(null) }

    // 앱 시작 시 저장된 토큰 확인
    LaunchedEffect(Unit) {
        val hasToken = authRepo.restoreToken()
        startDestination = if (hasToken) "main" else "login"
        isCheckingAuth = false
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
                            // TODO: 삭제 후 뒤로가기
                            navController.popBackStack()
                        }
                    )
                }
            }
        }
    }
}
