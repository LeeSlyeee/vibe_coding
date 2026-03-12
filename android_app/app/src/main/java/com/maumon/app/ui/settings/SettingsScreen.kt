package com.maumon.app.ui.settings

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.maumon.app.ui.theme.Primary
import com.maumon.app.ui.share.ShareScreen
import com.maumon.app.data.billing.SubscriptionManager
import com.maumon.app.ui.subscription.MindBridgePaywallScreen
import com.maumon.app.ui.bridge.MindBridgeMainScreen

/**
 * 설정 화면 - iOS AppSettingsView 1:1 대응
 * 모든 항목이 실제 동작하도록 구현
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    onLogout: () -> Unit,
    settingsViewModel: SettingsViewModel = viewModel(),
) {
    val uiState by settingsViewModel.uiState.collectAsState()
    val context = LocalContext.current

    var showLogoutDialog by remember { mutableStateOf(false) }
    var showShareScreen by remember { mutableStateOf(false) }
    var showGuideScreen by remember { mutableStateOf(false) }
    var showEditNicknameDialog by remember { mutableStateOf(false) }
    var showBirthDatePicker by remember { mutableStateOf(false) }
    var showPrivacyDialog by remember { mutableStateOf(false) }
    var showTermsDialog by remember { mutableStateOf(false) }
    var showB2GCodeDialog by remember { mutableStateOf(false) }
    var showB2GDisconnectDialog by remember { mutableStateOf(false) }
    var showPaywallScreen by remember { mutableStateOf(false) }
    var showBridgeMainScreen by remember { mutableStateOf(false) }

    // 구독 상태 구독
    val subscriptionManager = remember { SubscriptionManager.getInstance(context) }
    val isSubscribed by subscriptionManager.instanceIsSubscribed.collectAsState()

    // 서버에서 최신 유저 정보 가져오기
    LaunchedEffect(Unit) {
        settingsViewModel.refreshUserInfo()
    }

    // 메시지 스낵바
    val snackbarHostState = remember { SnackbarHostState() }
    LaunchedEffect(uiState.message) {
        uiState.message?.let { msg ->
            snackbarHostState.showSnackbar(msg)
            settingsViewModel.clearMessage()
        }
    }

    // ShareScreen 전체 화면 표시
    if (showShareScreen) {
        ShareScreen(onBack = { showShareScreen = false })
        return
    }

    // GuideScreen 전체 화면 표시
    if (showGuideScreen) {
        GuideScreen(onBack = { showGuideScreen = false })
        return
    }

    // MindBridge 페이월 전체 화면 표시
    if (showPaywallScreen) {
        MindBridgePaywallScreen(onDismiss = { showPaywallScreen = false })
        return
    }

    // MindBridge 메인 화면 표시 (Phase 3: 구독 중일 때 접근)
    if (showBridgeMainScreen) {
        MindBridgeMainScreen(onDismiss = { showBridgeMainScreen = false })
        return
    }

    Box(modifier = Modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
        ) {
            // ═══════════════════════════════════════════
            // 프로필 헤더 — iOS Section 1 대응
            // ═══════════════════════════════════════════
            Surface(
                modifier = Modifier.fillMaxWidth(),
                color = Primary.copy(alpha = 0.05f)
            ) {
                Column(
                    modifier = Modifier.padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Surface(
                        modifier = Modifier.size(80.dp),
                        shape = CircleShape,
                        color = Primary.copy(alpha = 0.2f)
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Text("🧘", fontSize = 36.sp)
                        }
                    }
                    Spacer(modifier = Modifier.height(12.dp))

                    // 닉네임 또는 유저명 표시 (iOS authManager.username 대응)
                    val displayName = uiState.nickname
                        ?: uiState.realName
                        ?: uiState.username
                        ?: "마음온 사용자"
                    Text(
                        displayName,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold
                    )

                    // 로그인 상태 표시
                    if (uiState.isLoggedIn && uiState.username != null) {
                        Text(
                            "@${uiState.username}",
                            fontSize = 13.sp,
                            color = Color.Gray
                        )
                    }

                    Text(
                        "마음의 온도를 기록하세요",
                        fontSize = 14.sp,
                        color = Color.Gray
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // ═══════════════════════════════════════════
            // 계정 섹션 — iOS Section 1 "내 정보" 대응
            // ═══════════════════════════════════════════
            SettingsSection(title = "계정") {
                // 프로필 편집 (닉네임 변경)
                SettingsItem(
                    icon = Icons.Default.Person,
                    title = "닉네임 변경",
                    subtitle = uiState.nickname ?: "설정되지 않음",
                    onClick = { showEditNicknameDialog = true }
                )
                HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))

                // 생년월일 변경 — iOS BirthDatePickerView 대응
                SettingsItem(
                    icon = Icons.Default.Cake,
                    title = "생년월일",
                    subtitle = uiState.birthDate ?: "설정되지 않음",
                    onClick = { showBirthDatePicker = true }
                )
            }

            // ═══════════════════════════════════════════
            // 소셜 — iOS Section 1.5 보호자/친구 연결 대응
            // ═══════════════════════════════════════════
            SettingsSection(title = "소셜") {
                SettingsItem(
                    icon = Icons.Default.People,
                    title = "보호자/친구 연결",
                    subtitle = "가족과 감정 통계 공유하기",
                    onClick = { showShareScreen = true }
                )
            }

            // ═══════════════════════════════════════════
            // 건강 관리 — iOS Section 2 "B2G 연동" 대응
            // ═══════════════════════════════════════════
            SettingsSection(title = "건강 관리") {
                if (uiState.b2gIsLinked) {
                    // 연동된 상태 — 센터 정보 표시
                    SettingsItem(
                        icon = Icons.Default.CheckCircle,
                        title = "기관 연동됨",
                        subtitle = if (uiState.b2gCenterName.isNotEmpty())
                            "${uiState.b2gCenterName} (${uiState.b2gCenterCode})"
                        else
                            "코드: ${uiState.b2gCenterCode}",
                        onClick = { }
                    )
                    HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))

                    // 데이터 동기화 버튼 — iOS B2GManager.syncData() 대응
                    SettingsItem(
                        icon = Icons.Default.Sync,
                        title = "데이터 동기화",
                        subtitle = if (uiState.b2gLastSync > 0L)
                            "마지막: ${formatSyncTime(uiState.b2gLastSync)}"
                        else
                            "아직 동기화되지 않았습니다",
                        onClick = { settingsViewModel.syncB2G() }
                    )
                    HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))

                    // 연동 해제
                    SettingsItem(
                        icon = Icons.Default.LinkOff,
                        title = "연동 해제",
                        subtitle = "기관 연결을 해제합니다",
                        onClick = { showB2GDisconnectDialog = true }
                    )
                } else {
                    // 미연동 상태 — 코드 입력
                    SettingsItem(
                        icon = Icons.Default.Business,
                        title = "B2G 기관 연결",
                        subtitle = "기관 코드를 입력하여 연동하세요",
                        onClick = { showB2GCodeDialog = true }
                    )
                }
            }

            // ═══════════════════════════════════════════
            // 멤버십 — iOS Section 3 "멤버십" 대응
            // ═══════════════════════════════════════════
            SettingsSection(title = "멤버십") {
                if (uiState.b2gIsLinked) {
                    // Case A: B2G 연동 → 무료 프리미엄
                    SettingsItem(
                        icon = Icons.Default.Business,
                        title = "기관 연동 멤버십",
                        subtitle = "보건소 연동으로 프리미엄 혜택이 적용됩니다",
                        onClick = { }
                    )
                } else if (isSubscribed) {
                    // Case B: 마음 브릿지 구독 중
                    Column {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(horizontal = 16.dp, vertical = 14.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            // 그라데이션 아이콘
                            Box(
                                modifier = Modifier
                                    .size(40.dp)
                                    .background(
                                        Brush.linearGradient(
                                            listOf(Color(0xFF6366F1), Color(0xFF8B5CF6))
                                        ),
                                        shape = CircleShape
                                    ),
                                contentAlignment = Alignment.Center
                            ) {
                                Icon(
                                    Icons.Default.HealthAndSafety,
                                    contentDescription = null,
                                    tint = Color.White,
                                    modifier = Modifier.size(20.dp)
                                )
                            }
                            Spacer(modifier = Modifier.width(16.dp))
                            Column(modifier = Modifier.weight(1f)) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Text(
                                        "🌉 마음 브릿지",
                                        style = MaterialTheme.typography.bodyLarge,
                                        fontWeight = FontWeight.Bold,
                                        color = Color(0xFF6366F1)
                                    )
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Surface(
                                        shape = RoundedCornerShape(8.dp),
                                        color = Color(0xFF6366F1).copy(alpha = 0.1f)
                                    ) {
                                        Text(
                                            "구독 중",
                                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp),
                                            fontSize = 10.sp,
                                            fontWeight = FontWeight.Bold,
                                            color = Color(0xFF6366F1)
                                        )
                                    }
                                }
                            }
                            Icon(
                                Icons.Default.CheckCircle,
                                contentDescription = null,
                                tint = Color(0xFF22C55E)
                            )
                        }

                        // [Phase 3] 마음 브릿지 메인 진입 버튼 (iOS 동일)
                        Button(
                            onClick = { showBridgeMainScreen = true },
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(horizontal = 16.dp)
                                .padding(bottom = 12.dp),
                            shape = RoundedCornerShape(10.dp),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = Color.Transparent
                            ),
                            contentPadding = PaddingValues(0.dp)
                        ) {
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .background(
                                        Brush.horizontalGradient(
                                            listOf(Color(0xFF6366F1), Color(0xFF8B5CF6))
                                        ),
                                        shape = RoundedCornerShape(10.dp)
                                    )
                                    .padding(vertical = 10.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.Center
                                ) {
                                    Icon(
                                        Icons.Default.HealthAndSafety,
                                        contentDescription = null,
                                        tint = Color.White,
                                        modifier = Modifier.size(16.dp)
                                    )
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text(
                                        "마음 브릿지 열기",
                                        fontWeight = FontWeight.Bold,
                                        color = Color.White,
                                        fontSize = 14.sp
                                    )
                                }
                            }
                        }
                    }
                } else {
                    // Case C: 미구독 → 페이월 진입
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { showPaywallScreen = true }
                            .padding(horizontal = 16.dp, vertical = 14.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(
                            modifier = Modifier
                                .size(40.dp)
                                .background(
                                    Brush.linearGradient(
                                        listOf(Color(0xFF6366F1), Color(0xFF8B5CF6))
                                    ),
                                    shape = CircleShape
                                ),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                Icons.Default.HealthAndSafety,
                                contentDescription = null,
                                tint = Color.White,
                                modifier = Modifier.size(20.dp)
                            )
                        }
                        Spacer(modifier = Modifier.width(16.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                "🌉 마음 브릿지",
                                style = MaterialTheme.typography.bodyLarge,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFF6366F1)
                            )
                            Text(
                                "가족·상담사에게 내 마음을 안전하게 전해보세요",
                                style = MaterialTheme.typography.bodySmall,
                                color = Color.Gray
                            )
                        }
                        Icon(
                            Icons.Default.ChevronRight,
                            contentDescription = null,
                            tint = Color.Gray.copy(alpha = 0.5f)
                        )
                    }
                }
            }

            // ═══════════════════════════════════════════
            // 보안
            // ═══════════════════════════════════════════
            SettingsSection(title = "보안") {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 14.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(Icons.Default.Security, contentDescription = null, tint = Primary, modifier = Modifier.size(24.dp))
                    Spacer(modifier = Modifier.width(16.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text("화면 캡처 방지", style = MaterialTheme.typography.bodyLarge)
                        Text("앱 화면이 캡처되거나 녹화되는 것을 방지합니다", style = MaterialTheme.typography.bodySmall, color = Color.Gray)
                    }
                    Switch(
                        checked = uiState.isScreenshotPreventEnabled,
                        onCheckedChange = { settingsViewModel.toggleScreenshotPrevent(it) },
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = Color.White,
                            checkedTrackColor = Primary
                        )
                    )
                }
            }

            // ═══════════════════════════════════════════
            // 도움말 — iOS AppGuideView 대응
            // ═══════════════════════════════════════════
            SettingsSection(title = "도움말") {
                SettingsItem(
                    icon = Icons.Default.MenuBook,
                    title = "사용 설명서",
                    subtitle = "마음온을 100% 활용하는 방법",
                    onClick = { showGuideScreen = true }
                )
            }

            // ═══════════════════════════════════════════
            // 정보 — iOS Section 4 "앱 정보" 대응
            // ═══════════════════════════════════════════
            SettingsSection(title = "정보") {
                SettingsItem(
                    icon = Icons.Default.Info,
                    title = "앱 버전",
                    subtitle = getAppVersion(context),
                    onClick = { }
                )
                HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))

                // 개인정보 처리방침 — 앱 내 다이얼로그 표시
                SettingsItem(
                    icon = Icons.Default.Description,
                    title = "개인정보 처리방침",
                    onClick = { showPrivacyDialog = true }
                )
                HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))

                // 이용약관 — 앱 내 다이얼로그 표시
                SettingsItem(
                    icon = Icons.Default.Gavel,
                    title = "이용약관",
                    onClick = { showTermsDialog = true }
                )
                HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp))

                // 개발사 정보
                SettingsItem(
                    icon = Icons.Default.Groups,
                    title = "개발자",
                    subtitle = "마음온 팀",
                    onClick = { }
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            // ═══════════════════════════════════════════
            // 로그아웃 버튼
            // ═══════════════════════════════════════════
            Button(
                onClick = { showLogoutDialog = true },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp),
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color.Red.copy(alpha = 0.1f),
                    contentColor = Color.Red
                )
            ) {
                Icon(Icons.Default.Logout, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("로그아웃", fontWeight = FontWeight.Bold)
            }

            Spacer(modifier = Modifier.height(32.dp))
        }

        // 스낵바
        SnackbarHost(
            hostState = snackbarHostState,
            modifier = Modifier.align(Alignment.BottomCenter)
        )
    }

    // ═══════════════════════════════════════════
    // 다이얼로그들
    // ═══════════════════════════════════════════

    // 로그아웃 확인
    if (showLogoutDialog) {
        AlertDialog(
            onDismissRequest = { showLogoutDialog = false },
            title = { Text("로그아웃") },
            text = { Text("로그아웃하시겠습니까?") },
            confirmButton = {
                TextButton(onClick = { showLogoutDialog = false; onLogout() }) {
                    Text("로그아웃", color = Color.Red)
                }
            },
            dismissButton = {
                TextButton(onClick = { showLogoutDialog = false }) {
                    Text("취소")
                }
            }
        )
    }

    // 닉네임 편집 다이얼로그
    if (showEditNicknameDialog) {
        NicknameEditDialog(
            currentNickname = uiState.nickname ?: "",
            onDismiss = { showEditNicknameDialog = false },
            onConfirm = { newNickname ->
                settingsViewModel.updateNickname(newNickname)
                showEditNicknameDialog = false
            }
        )
    }

    // 생년월일 선택 다이얼로그
    if (showBirthDatePicker) {
        BirthDatePickerDialog(
            currentDate = uiState.birthDate,
            onDismiss = { showBirthDatePicker = false },
            onConfirm = { dateStr ->
                settingsViewModel.updateBirthDate(dateStr)
                showBirthDatePicker = false
            }
        )
    }

    // 개인정보 처리방침 다이얼로그
    if (showPrivacyDialog) {
        LegalTextDialog(
            title = "개인정보 처리방침",
            text = PRIVACY_POLICY_TEXT,
            onDismiss = { showPrivacyDialog = false }
        )
    }

    // 이용약관 다이얼로그
    if (showTermsDialog) {
        LegalTextDialog(
            title = "이용약관",
            text = TERMS_OF_SERVICE_TEXT,
            onDismiss = { showTermsDialog = false }
        )
    }

    // B2G 코드 입력 다이얼로그
    if (showB2GCodeDialog) {
        B2GCodeInputDialog(
            isLoading = uiState.isLoading,
            onDismiss = { showB2GCodeDialog = false },
            onConfirm = { code ->
                settingsViewModel.connectB2G(code)
                showB2GCodeDialog = false
            }
        )
    }

    // B2G 연동 해제 확인 다이얼로그
    if (showB2GDisconnectDialog) {
        AlertDialog(
            onDismissRequest = { showB2GDisconnectDialog = false },
            title = { Text("연동 해제", fontWeight = FontWeight.Bold) },
            text = {
                Text("기관 연동을 해제하시겠습니까?\n해제 후에는 기관에서 데이터를 확인할 수 없습니다.")
            },
            confirmButton = {
                TextButton(onClick = {
                    settingsViewModel.disconnectB2G()
                    showB2GDisconnectDialog = false
                }) {
                    Text("해제", color = Color.Red)
                }
            },
            dismissButton = {
                TextButton(onClick = { showB2GDisconnectDialog = false }) {
                    Text("취소")
                }
            }
        )
    }
}

// ═══════════════════════════════════════════
// 닉네임 편집 다이얼로그
// ═══════════════════════════════════════════
@Composable
fun NicknameEditDialog(
    currentNickname: String,
    onDismiss: () -> Unit,
    onConfirm: (String) -> Unit,
) {
    var text by remember { mutableStateOf(currentNickname) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text("닉네임 변경", fontWeight = FontWeight.Bold)
        },
        text = {
            Column {
                Text(
                    "새로운 닉네임을 입력하세요.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color.Gray
                )
                Spacer(modifier = Modifier.height(16.dp))
                OutlinedTextField(
                    value = text,
                    onValueChange = { text = it },
                    label = { Text("닉네임") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp)
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = { onConfirm(text) },
                enabled = text.isNotBlank() && text != currentNickname
            ) {
                Text("저장", color = Primary)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("취소")
            }
        }
    )
}

// ═══════════════════════════════════════════
// 생년월일 선택 다이얼로그
// 완전 커스텀 한국어 달력
// 일요일(빨간색), 토요일(파란색), 모든 텍스트 한국어
// ═══════════════════════════════════════════
@Composable
fun BirthDatePickerDialog(
    currentDate: String?,
    onDismiss: () -> Unit,
    onConfirm: (String) -> Unit,
) {
    // 초기 날짜 파싱
    val initialDate = remember {
        currentDate?.let { dateStr ->
            try {
                val parts = dateStr.split("-")
                if (parts.size == 3) Triple(parts[0].toInt(), parts[1].toInt(), parts[2].toInt())
                else null
            } catch (_: Exception) { null }
        }
    }

    val today = remember {
        val cal = java.util.Calendar.getInstance()
        Triple(
            cal.get(java.util.Calendar.YEAR),
            cal.get(java.util.Calendar.MONTH) + 1,
            cal.get(java.util.Calendar.DAY_OF_MONTH)
        )
    }

    var displayYear by remember { mutableIntStateOf(initialDate?.first ?: today.first) }
    var displayMonth by remember { mutableIntStateOf(initialDate?.second ?: today.second) }
    var selectedYear by remember { mutableIntStateOf(initialDate?.first ?: -1) }
    var selectedMonth by remember { mutableIntStateOf(initialDate?.second ?: -1) }
    var selectedDay by remember { mutableIntStateOf(initialDate?.third ?: -1) }

    val koreanDays = listOf("일", "월", "화", "수", "목", "금", "토")

    // 달력 데이터 계산
    val firstDayOfWeek = remember(displayYear, displayMonth) {
        val cal = java.util.Calendar.getInstance()
        cal.set(displayYear, displayMonth - 1, 1)
        cal.get(java.util.Calendar.DAY_OF_WEEK) - 1 // 0=일요일
    }
    val daysInMonth = remember(displayYear, displayMonth) {
        val cal = java.util.Calendar.getInstance()
        cal.set(displayYear, displayMonth - 1, 1)
        cal.getActualMaximum(java.util.Calendar.DAY_OF_MONTH)
    }

    val hasSelection = selectedYear > 0
    val headlineText = if (hasSelection) {
        "${selectedYear}년 ${selectedMonth}월 ${selectedDay}일"
    } else {
        "날짜를 선택하세요"
    }

    val sundayColor = Color(0xFFFF3B30)
    val saturdayColor = Color(0xFF007AFF)

    androidx.compose.ui.window.Dialog(onDismissRequest = onDismiss) {
        Card(
            shape = RoundedCornerShape(28.dp),
            colors = CardDefaults.cardColors(containerColor = Color.White),
            elevation = CardDefaults.cardElevation(defaultElevation = 8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(24.dp)) {
                // 제목
                Text(
                    "생년월일 선택",
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 13.sp,
                    color = Color.Gray
                )
                Spacer(Modifier.height(4.dp))

                // 선택된 날짜 헤드라인
                Text(
                    headlineText,
                    fontSize = 26.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF1D1D1F)
                )

                HorizontalDivider(
                    modifier = Modifier.padding(vertical = 16.dp),
                    color = Color(0xFFE5E5EA)
                )

                // ── 월 네비게이션 ──
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    IconButton(onClick = {
                        if (displayMonth == 1) { displayMonth = 12; displayYear-- }
                        else displayMonth--
                    }) {
                        Icon(
                            Icons.Default.ChevronLeft,
                            contentDescription = "이전 달",
                            tint = Primary
                        )
                    }
                    Text(
                        "${displayYear}년 ${displayMonth}월",
                        fontWeight = FontWeight.Bold,
                        fontSize = 17.sp,
                        color = Color(0xFF1D1D1F)
                    )
                    IconButton(onClick = {
                        if (displayMonth == 12) { displayMonth = 1; displayYear++ }
                        else displayMonth++
                    }) {
                        Icon(
                            Icons.Default.ChevronRight,
                            contentDescription = "다음 달",
                            tint = Primary
                        )
                    }
                }

                Spacer(Modifier.height(8.dp))

                // ── 요일 헤더 (일=빨강, 토=파랑) ──
                Row(modifier = Modifier.fillMaxWidth()) {
                    koreanDays.forEachIndexed { index, day ->
                        val color = when (index) {
                            0 -> sundayColor
                            6 -> saturdayColor
                            else -> Color(0xFF8E8E93)
                        }
                        Box(
                            modifier = Modifier.weight(1f),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                day,
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold,
                                color = color
                            )
                        }
                    }
                }

                Spacer(Modifier.height(6.dp))

                // ── 날짜 그리드 ──
                val totalCells = firstDayOfWeek + daysInMonth
                val rows = (totalCells + 6) / 7

                for (row in 0 until rows) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(42.dp)
                    ) {
                        for (col in 0..6) {
                            val cellIndex = row * 7 + col
                            val day = cellIndex - firstDayOfWeek + 1

                            Box(
                                modifier = Modifier
                                    .weight(1f)
                                    .fillMaxHeight(),
                                contentAlignment = Alignment.Center
                            ) {
                                if (day in 1..daysInMonth) {
                                    val isSelected = selectedYear == displayYear &&
                                            selectedMonth == displayMonth &&
                                            selectedDay == day
                                    val isToday = today.first == displayYear &&
                                            today.second == displayMonth &&
                                            today.third == day

                                    val textColor = when {
                                        isSelected -> Color.White
                                        col == 0 -> sundayColor
                                        col == 6 -> saturdayColor
                                        else -> Color(0xFF1D1D1F)
                                    }

                                    Surface(
                                        onClick = {
                                            selectedYear = displayYear
                                            selectedMonth = displayMonth
                                            selectedDay = day
                                        },
                                        shape = CircleShape,
                                        color = when {
                                            isSelected -> Primary
                                            isToday -> Primary.copy(alpha = 0.1f)
                                            else -> Color.Transparent
                                        },
                                        modifier = Modifier.size(36.dp)
                                    ) {
                                        Box(contentAlignment = Alignment.Center) {
                                            Text(
                                                "$day",
                                                fontSize = 15.sp,
                                                fontWeight = when {
                                                    isSelected -> FontWeight.Bold
                                                    isToday -> FontWeight.Bold
                                                    else -> FontWeight.Normal
                                                },
                                                color = textColor
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Spacer(Modifier.height(20.dp))

                // ── 버튼 ──
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End
                ) {
                    TextButton(onClick = onDismiss) {
                        Text("취소", color = Color.Gray, fontWeight = FontWeight.SemiBold)
                    }
                    Spacer(Modifier.width(8.dp))
                    TextButton(
                        onClick = {
                            if (hasSelection) {
                                val formatted = String.format(
                                    "%04d-%02d-%02d",
                                    selectedYear, selectedMonth, selectedDay
                                )
                                onConfirm(formatted)
                            }
                        },
                        enabled = hasSelection
                    ) {
                        Text(
                            "저장",
                            color = if (hasSelection) Primary else Color.Gray,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }
    }
}

// ═══════════════════════════════════════════
// 공통 컴포넌트
// ═══════════════════════════════════════════

@Composable
fun SettingsSection(title: String, content: @Composable ColumnScope.() -> Unit) {
    Column(modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp)) {
        Text(
            title,
            style = MaterialTheme.typography.labelLarge,
            color = Color.Gray,
            modifier = Modifier.padding(start = 8.dp, bottom = 8.dp, top = 12.dp)
        )
        Card(
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
        ) {
            Column { content() }
        }
    }
}

@Composable
fun SettingsItem(
    icon: ImageVector,
    title: String,
    subtitle: String? = null,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(icon, contentDescription = null, tint = Primary, modifier = Modifier.size(24.dp))
        Spacer(modifier = Modifier.width(16.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.bodyLarge)
            if (subtitle != null) {
                Text(subtitle, style = MaterialTheme.typography.bodySmall, color = Color.Gray)
            }
        }
        Icon(
            Icons.Default.ChevronRight,
            contentDescription = null,
            tint = Color.Gray.copy(alpha = 0.5f)
        )
    }
}

// ═══════════════════════════════════════════
// B2G 코드 입력 다이얼로그
// iOS AppSettingsView B2G Section 대응
// ═══════════════════════════════════════════

@Composable
fun B2GCodeInputDialog(
    isLoading: Boolean,
    onDismiss: () -> Unit,
    onConfirm: (String) -> Unit,
) {
    var code by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text("기관 코드 입력", fontWeight = FontWeight.Bold)
        },
        text = {
            Column {
                Text(
                    "보건소 또는 정신건강복지센터에서 받은 기관 코드를 입력하세요.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color.Gray
                )
                Spacer(modifier = Modifier.height(16.dp))
                OutlinedTextField(
                    value = code,
                    onValueChange = { code = it.uppercase() },
                    label = { Text("기관 코드") },
                    placeholder = { Text("예: MHCENTER01") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    enabled = !isLoading
                )
                if (isLoading) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(
                        horizontalArrangement = Arrangement.Center,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(20.dp),
                            strokeWidth = 2.dp
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("연동 중...", fontSize = 13.sp, color = Color.Gray)
                    }
                }

                Spacer(modifier = Modifier.height(12.dp))

                // 보건소 안내 박스 (iOS PremiumModalView 녹색 박스 대응)
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    color = Color(0xFFF0FDF4),
                    border = androidx.compose.foundation.BorderStroke(
                        1.dp, Color(0xFFDCFCE7)
                    )
                ) {
                    Row(modifier = Modifier.padding(15.dp)) {
                        Text("🏥", fontSize = 16.sp)
                        Spacer(modifier = Modifier.width(10.dp))
                        Column {
                            Text(
                                "보건소/정신건강복지센터 안내",
                                fontWeight = FontWeight.Bold,
                                fontSize = 14.sp,
                                color = Color(0xFF15803D)
                            )
                            Text(
                                "관할 보건소나 정신건강복지센터에서 발급받은 코드를 입력하세요.",
                                fontSize = 13.sp,
                                color = Color(0xFF15803D)
                            )
                        }
                    }
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = { onConfirm(code) },
                enabled = code.isNotBlank() && !isLoading
            ) {
                Text("연동하기", color = Primary, fontWeight = FontWeight.Bold)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("취소")
            }
        }
    )
}

// ═══════════════════════════════════════════
// 유틸리티
// ═══════════════════════════════════════════

/** 앱 버전 동적 추출 */
private fun getAppVersion(context: android.content.Context): String {
    return try {
        val pInfo = context.packageManager.getPackageInfo(context.packageName, 0)
        "${pInfo.versionName} (Android)"
    } catch (_: Exception) {
        "1.0.0 (Android)"
    }
}

/** 동기화 시간 포맷 — iOS lastSyncDate 표시 대응 */
private fun formatSyncTime(timestampMs: Long): String {
    if (timestampMs <= 0L) return "없음"
    val sdf = java.text.SimpleDateFormat("yyyy-MM-dd HH:mm", java.util.Locale.KOREA)
    return sdf.format(java.util.Date(timestampMs))
}

// ═══════════════════════════════════════════
// 법적 고지 다이얼로그
// ═══════════════════════════════════════════

@Composable
fun LegalTextDialog(
    title: String,
    text: String,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(title, fontWeight = FontWeight.Bold)
        },
        text = {
            Column(
                modifier = Modifier
                    .heightIn(max = 400.dp)
                    .verticalScroll(rememberScrollState())
            ) {
                Text(
                    text,
                    style = MaterialTheme.typography.bodySmall,
                    lineHeight = 20.sp
                )
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("확인", color = Primary)
            }
        }
    )
}

// ═══════════════════════════════════════════
// 법적 텍스트 상수
// ═══════════════════════════════════════════

private const val PRIVACY_POLICY_TEXT = """
마음온(maumON) 개인정보 처리방침

제1조 (목적)
본 방침은 마음온 앱(이하 '서비스')이 수집하는 개인정보의 항목, 수집 목적, 보유 기간 등을 안내합니다.

제2조 (수집하는 개인정보)
1. 필수 항목: 아이디, 비밀번호
2. 선택 항목: 닉네임, 생년월일
3. 자동 수집 항목: 기기 정보, 앱 사용 기록
4. 서비스 이용 과정에서 생성되는 정보: 감정 일기, 감정 분석 결과

제3조 (개인정보의 수집 및 이용 목적)
1. 서비스 제공 및 운영
2. 감정 분석 및 통계 제공
3. 보호자/친구 연결 기능 제공
4. B2G 기관 연동 서비스 제공
5. 서비스 개선 및 신규 서비스 개발

제4조 (개인정보의 보유 및 이용 기간)
회원 탈퇴 시까지 보유하며, 탈퇴 후 즉시 파기합니다.
단, 관련 법령에 의해 보존할 의무가 있는 경우 해당 기간 동안 보존합니다.

제5조 (개인정보의 제3자 제공)
이용자의 동의 없이 제3자에게 개인정보를 제공하지 않습니다.
단, B2G 기관 연동 시 해당 기관에 감정 통계 데이터가 공유될 수 있으며, 이 경우 사전 동의를 받습니다.

제6조 (이용자의 권리)
이용자는 언제든지 자신의 개인정보를 조회, 수정, 삭제할 수 있으며, 서비스 탈퇴를 요청할 수 있습니다.

제7조 (문의처)
개인정보 관련 문의: maumon.team@gmail.com

시행일: 2026년 1월 1일
"""

private const val TERMS_OF_SERVICE_TEXT = """
마음온(maumON) 이용약관

제1조 (목적)
본 약관은 마음온 앱(이하 '서비스')의 이용과 관련하여 서비스 제공자와 이용자 간의 권리, 의무 및 책임사항을 규정함을 목적으로 합니다.

제2조 (서비스의 내용)
1. 감정 일기 작성 및 관리
2. AI 기반 감정 분석 및 통계
3. 보호자/친구와의 감정 공유
4. B2G 기관 연동 서비스
5. AI 감정 케어 서비스

제3조 (이용자의 의무)
1. 이용자는 본인의 계정 정보를 안전하게 관리할 책임이 있습니다.
2. 타인의 계정을 부정하게 사용하거나, 서비스의 안정적 운영을 방해하는 행위를 해서는 안 됩니다.
3. 허위 정보를 등록하거나, 타인의 정보를 도용해서는 안 됩니다.

제4조 (서비스 제공의 제한)
서비스 제공자는 다음 경우 서비스 제공을 제한할 수 있습니다.
1. 시스템 점검 및 유지보수
2. 천재지변 등 불가항력적 사유
3. 이용자의 약관 위반

제5조 (면책조항)
1. 서비스에서 제공하는 AI 분석 및 감정 케어는 참고용이며, 의료적 판단을 대체하지 않습니다.
2. 긴급한 정신건강 위기 상황에서는 반드시 전문 의료기관이나 긴급 상담전화(1393, 1577-0199)를 이용해 주세요.
3. AI가 제공하는 감정 분석 결과 및 코멘트의 정확성을 보장하지 않으며, 이를 근거로 한 의사결정에 대해 서비스 제공자는 책임을 지지 않습니다.
4. 기본적으로 모든 데이터는 사용자 기기에만 저장됩니다. 기관 연동 시에만 사용자가 동의한 정보가 암호화되어 전송됩니다.
5. 보호자 알림 기능은 사용자 본인의 명시적 동의 하에서만 작동합니다.
6. AI의 위기 감지 기능은 보조적 수단이며, 100% 정확성을 보장하지 않습니다. AI가 감지하지 못하는 위기 상황이 발생할 수 있으므로, 긴급한 상황에서는 즉시 1393 또는 119에 직접 연락해 주세요.

제6조 (약관의 변경)
서비스 제공자는 필요한 경우 약관을 변경할 수 있으며, 변경된 약관은 앱 내 공지를 통해 안내합니다.

제7조 (문의처)
서비스 관련 문의: maumon.team@gmail.com

시행일: 2026년 1월 1일
"""
