package com.maumon.app.ui.calendar

import java.time.DayOfWeek

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ChevronLeft
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.maumon.app.data.model.Diary
import com.maumon.app.data.billing.SubscriptionManager
import com.maumon.app.ui.subscription.MindBridgePaywallScreen
import com.maumon.app.ui.theme.*
import java.time.LocalDate
import java.time.YearMonth
import java.time.format.DateTimeFormatter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CalendarScreen(
    calendarViewModel: CalendarViewModel = viewModel(),
    onWriteDiary: (dateStr: String) -> Unit = {},
    onViewDiary: (Diary) -> Unit = {},
    onLogout: () -> Unit = {},
) {
    var currentMonth by remember { mutableStateOf(YearMonth.now()) }
    val uiState by calendarViewModel.uiState.collectAsState()
    val today = LocalDate.now()
    var showSettingsSheet by remember { mutableStateOf(false) }
    var showFutureDateAlert by remember { mutableStateOf(false) }
    
    // [Step 4] Soft Nudge State
    var showNudgeBanner by remember { mutableStateOf(true) }
    var showPaywallFromNudge by remember { mutableStateOf(false) }
    val context = LocalContext.current
    val isSubscribed by SubscriptionManager.isSubscribed.collectAsState()
    val isB2GLinked by SubscriptionManager.isB2GLinked.collectAsState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
    ) {
        // 월 네비게이션 + 새로고침 + 설정
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // 좌측: < > 월 이동
            IconButton(onClick = { currentMonth = currentMonth.minusMonths(1) }) {
                Icon(Icons.Default.ChevronLeft, contentDescription = "이전 달")
            }

            // 중앙: 년/월
            Text(
                text = "${currentMonth.year}년 ${currentMonth.monthValue}월",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.weight(1f),
                textAlign = TextAlign.Center
            )

            // 우측: 새로고침 + > + 설정
            if (uiState.isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(24.dp),
                    strokeWidth = 2.dp
                )
            } else {
                IconButton(onClick = { calendarViewModel.fetchDiaries() }) {
                    Icon(Icons.Default.Refresh, contentDescription = "새로고침")
                }
            }
            IconButton(onClick = { currentMonth = currentMonth.plusMonths(1) }) {
                Icon(Icons.Default.ChevronRight, contentDescription = "다음 달")
            }
            // iOS 햄버거 메뉴 대응
            IconButton(onClick = { showSettingsSheet = true }) {
                Icon(Icons.Default.Menu, contentDescription = "설정")
            }
        }

        // 요일 헤더
        WeekdayHeader()

        // 캘린더 그리드
        CalendarGrid(
            yearMonth = currentMonth,
            diaries = uiState.diaries,
            calendarViewModel = calendarViewModel,
            onDayClick = { dateStr ->
                val diary = calendarViewModel.getDiaryForDate(dateStr)
                if (diary != null) {
                    onViewDiary(diary)
                } else {
                    // 미래 날짜 체크
                    val selectedDate = try {
                        LocalDate.parse(dateStr)
                    } catch (_: Exception) { null }

                    if (selectedDate != null && selectedDate.isAfter(today)) {
                        // 미래 날짜 → 안내 다이얼로그 표시
                        showFutureDateAlert = true
                    } else {
                        onWriteDiary(dateStr)
                    }
                }
            }
        )

        Spacer(modifier = Modifier.weight(1f))

        // [Step 4] Soft Nudge Banner (마음 브릿지 자연스러운 유도)
        val diaryCount = uiState.diaries.size
        val nudgeDismissedDate = remember {
            val prefs = context.getSharedPreferences("maum_on_prefs", android.content.Context.MODE_PRIVATE)
            prefs.getString("nudge_dismissed_date", "") ?: ""
        }
        val todayStr = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE)
        val shouldShowNudge = !isSubscribed && !isB2GLinked && diaryCount >= 7 && nudgeDismissedDate != todayStr

        if (shouldShowNudge && showNudgeBanner) {
            androidx.compose.animation.AnimatedVisibility(
                visible = showNudgeBanner,
                exit = androidx.compose.animation.fadeOut()
            ) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 8.dp)
                        .clickable { showPaywallFromNudge = true },
                    shape = RoundedCornerShape(14.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                    border = androidx.compose.foundation.BorderStroke(
                        1.dp,
                        androidx.compose.ui.graphics.Brush.linearGradient(
                            colors = listOf(
                                Color(0xFF6366f1).copy(alpha = 0.3f),
                                Color(0xFF8b5cf6).copy(alpha = 0.15f)
                            )
                        )
                    )
                ) {
                    Row(
                        modifier = Modifier.padding(14.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        // 아이콘
                        Box(
                            modifier = Modifier
                                .size(40.dp)
                                .clip(androidx.compose.foundation.shape.CircleShape)
                                .background(
                                    androidx.compose.ui.graphics.Brush.linearGradient(
                                        colors = listOf(
                                            Color(0xFF6366f1).copy(alpha = 0.15f),
                                            Color(0xFF8b5cf6).copy(alpha = 0.15f)
                                        )
                                    )
                                ),
                            contentAlignment = Alignment.Center
                        ) {
                            Text("\uD83C\uDF09", fontSize = 20.sp) // 🌉
                        }

                        // 텍스트
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                "가족에게 내 마음을 전해보세요",
                                fontSize = 14.sp,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                            Text(
                                "마음 브릿지로 감정 리포트를 안전하게 공유",
                                fontSize = 11.sp,
                                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                            )
                        }

                        // 닫기 버튼
                        IconButton(
                            onClick = {
                                showNudgeBanner = false
                                // 오늘 하루 다시 표시하지 않음
                                context.getSharedPreferences("maum_on_prefs", android.content.Context.MODE_PRIVATE)
                                    .edit()
                                    .putString("nudge_dismissed_date", todayStr)
                                    .apply()
                            },
                            modifier = Modifier.size(28.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Close,
                                contentDescription = "닫기",
                                modifier = Modifier.size(14.dp),
                                tint = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f)
                            )
                        }
                    }
                }
            }
        }

        // 오늘 일기 쓰기 버튼
        Button(
            onClick = { onWriteDiary(today.toString()) },
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp, vertical = 16.dp)
                .height(56.dp),
            shape = RoundedCornerShape(16.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Primary)
        ) {
            Icon(Icons.Default.Add, contentDescription = null)
            Spacer(modifier = Modifier.width(8.dp))
            Text("오늘의 일기 쓰기", fontSize = 16.sp, fontWeight = FontWeight.Bold)
        }
    }

    // 미래 날짜 안내 다이얼로그
    if (showFutureDateAlert) {
        AlertDialog(
            onDismissRequest = { showFutureDateAlert = false },
            icon = { Text("📅", fontSize = 32.sp) },
            title = {
                Text("미래의 일기는 쓸 수 없어요", fontWeight = FontWeight.Bold)
            },
            text = {
                Text(
                    "일기는 오늘 또는 과거 날짜에만 작성할 수 있습니다.\n오늘의 감정을 기록해보세요!"
                )
            },
            confirmButton = {
                TextButton(onClick = { showFutureDateAlert = false }) {
                    Text("확인")
                }
            }
        )
    }

    // 설정 BottomSheet (iOS 햄버거 메뉴 대응)
    if (showSettingsSheet) {
        ModalBottomSheet(
            onDismissRequest = { showSettingsSheet = false }
        ) {
            com.maumon.app.ui.settings.SettingsScreen(
                onLogout = {
                    showSettingsSheet = false
                    onLogout()
                }
            )
        }
    }

    // [Step 4] Paywall from Nudge → Full Paywall Screen
    if (showPaywallFromNudge) {
        MindBridgePaywallScreen(onDismiss = { showPaywallFromNudge = false })
    }
}

@Composable
fun WeekdayHeader() {
    val days = listOf("일", "월", "화", "수", "목", "금", "토")
    Row(modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp)) {
        days.forEach { day ->
            Text(
                text = day,
                modifier = Modifier.weight(1f),
                textAlign = TextAlign.Center,
                style = MaterialTheme.typography.bodySmall,
                color = when (day) {
                    "일" -> Color(0xFFFF3B30)
                    "토" -> Primary
                    else -> MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f)
                },
                fontWeight = FontWeight.Medium
            )
        }
    }
}

@Composable
fun CalendarGrid(
    yearMonth: YearMonth,
    diaries: List<Diary>,
    calendarViewModel: CalendarViewModel,
    onDayClick: (String) -> Unit
) {
    val firstDay = yearMonth.atDay(1)
    val daysInMonth = yearMonth.lengthOfMonth()
    val startDayOfWeek = firstDay.dayOfWeek.value % 7
    val today = LocalDate.now()

    // 날짜→일기 맵 생성 (recomposition에서 효율적)
    val diaryMap = remember(diaries) {
        diaries.associateBy { it.date }
    }

    val cells = mutableListOf<Int?>()
    repeat(startDayOfWeek) { cells.add(null) }
    for (day in 1..daysInMonth) { cells.add(day) }

    LazyVerticalGrid(
        columns = GridCells.Fixed(7),
        modifier = Modifier.padding(horizontal = 12.dp),
        contentPadding = PaddingValues(vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(4.dp),
        horizontalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        items(cells) { day ->
            if (day != null) {
                val date = yearMonth.atDay(day)
                val isToday = date == today
                val dateStr = date.toString()
                val diary = diaryMap[dateStr]

                DayCell(
                    day = day,
                    date = date,
                    isToday = isToday,
                    diary = diary,
                    onClick = { onDayClick(dateStr) }
                )
            } else {
                Box(modifier = Modifier.aspectRatio(1f))
            }
        }
    }
}

/** AI 감정 키워드 → 배경색 매핑 (iOS MoodAssets 대응) */
fun emotionColor(diary: Diary?): Color? {
    if (diary == null) return null
    val emotion = (diary.aiPrediction ?: diary.aiComment ?: "").lowercase()
    return when {
        emotion.contains("행복") || emotion.contains("기쁨") || emotion.contains("즐거") -> Color(0xFFFFE0E6) // 핑크
        emotion.contains("평온") || emotion.contains("편안") || emotion.contains("안정") -> Color(0xFFE0F5E9) // 연초록
        emotion.contains("보통") || emotion.contains("무난") || emotion.contains("그저") -> Color(0xFFFFF3E0) // 연오렌지
        emotion.contains("우울") || emotion.contains("슬") || emotion.contains("외로") -> Color(0xFFE8E0F5) // 연보라
        emotion.contains("화") || emotion.contains("짜증") || emotion.contains("분노") -> Color(0xFFFFE0E0) // 연빨강
        emotion.contains("불안") || emotion.contains("걱정") || emotion.contains("긴장") -> Color(0xFFE0ECF5) // 연파랑
        emotion.contains("감사") || emotion.contains("뿌듯") || emotion.contains("성취") -> Color(0xFFFFF9E0) // 연노랑
        else -> {
            // AI 감정 없으면 mood_level 기반
            when (diary.effectiveMoodLevel) {
                5 -> Color(0xFFFFE0E6)
                4 -> Color(0xFFE0F5E9)
                3 -> Color(0xFFFFF3E0)
                2 -> Color(0xFFE8E0F5)
                1 -> Color(0xFFFFE0E0)
                else -> Color(0xFFF0F0F0)
            }
        }
    }
}

/** 감정 이모지 (mood_level 기반) */
fun moodEmojiFor(diary: Diary): String {
    return when (diary.effectiveMoodLevel) {
        5 -> "😊"
        4 -> "🙂"
        3 -> "😐"
        2 -> "😢"
        1 -> "😡"
        else -> "📝"
    }
}

@Composable
fun DayCell(day: Int, date: LocalDate, isToday: Boolean, diary: Diary?, onClick: () -> Unit) {
    val bgColor = emotionColor(diary)
    val hasDiary = diary != null
    // AI 감정 라벨 추출 (iOS parseAI 대응)
    val aiLabel = diary?.let {
        val raw = it.aiPrediction?.takeIf { p -> p.isNotBlank() && p != "분석 중..." }
        raw?.let { text ->
            // "Happy (80%)" → "Happy" 추출
            val label = if (text.contains("(")) text.substringBefore("(").trim() else text.trim()
            // 영→한 번역
            val translations = mapOf(
                "Happy" to "행복", "Sad" to "슬픔", "Angry" to "분노",
                "Fear" to "두려움", "Surprise" to "놀람", "Neutral" to "평온",
                "Disgust" to "혐오", "Anxiety" to "불안", "Depression" to "우울",
                "Stress" to "스트레스", "Joy" to "기쁨", "Love" to "사랑",
                "Confusion" to "혼란", "Excitement" to "흥분", "Tired" to "지침"
            )
            translations[label] ?: label
        }
    }

    // 토요일=파란, 일요일=빨간 색상
    val isSunday = date.dayOfWeek == DayOfWeek.SUNDAY
    val isSaturday = date.dayOfWeek == DayOfWeek.SATURDAY

    Box(
        modifier = Modifier
            .height(75.dp)
            .clip(RoundedCornerShape(10.dp))
            .background(
                when {
                    isToday && hasDiary -> bgColor!!.copy(alpha = 0.85f)
                    isToday -> Primary.copy(alpha = 0.12f)
                    hasDiary -> bgColor!!.copy(alpha = 0.7f)
                    else -> Color.Transparent
                }
            )
            .then(
                if (isToday) Modifier.border(2.dp, Primary, RoundedCornerShape(10.dp))
                else Modifier
            )
            .clickable(onClick = onClick),
        contentAlignment = Alignment.TopCenter
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(top = 4.dp)
        ) {
            // 1. 날짜 (토요일=파란, 일요일=빨간)
            Text(
                text = "$day",
                fontSize = if (hasDiary) 10.sp else 13.sp,
                fontWeight = if (isToday || hasDiary) FontWeight.Bold else FontWeight.Normal,
                color = when {
                    isSunday -> Color(0xFFFF3B30)  // 빨간색
                    isSaturday -> Primary          // 파란색
                    isToday -> Primary
                    hasDiary -> MaterialTheme.colorScheme.onSurface.copy(alpha = 0.8f)
                    else -> MaterialTheme.colorScheme.onSurface
                }
            )
            if (hasDiary) {
                // 2. 감정 이모지
                Text(text = moodEmojiFor(diary!!), fontSize = 16.sp)
                // 3. AI 감정 라벨
                aiLabel?.let {
                    Text(
                        text = it,
                        fontSize = 8.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
                        maxLines = 1
                    )
                }
            }
        }
    }
}

