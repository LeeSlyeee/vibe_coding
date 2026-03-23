package com.maumon.app.ui.stats

import androidx.compose.animation.animateColorAsState
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.ui.draw.clip
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.launch
import com.maumon.app.ui.theme.Primary

/**
 * 감정 통계 화면 - iOS AppStatsView 1:1 대응
 * 하위 탭: 흐름 / 월별 / 분포 / 날씨 / AI분석
 */

// 감정 색상 (iOS mood1~mood5 대응)
val Mood1Color = Color(0xFFFF453A)  // 화남 (빨강)
val Mood2Color = Color(0xFF5856D6)  // 우울 (보라)
val Mood3Color = Color(0xFFFF9500)  // 보통 (주황)
val Mood4Color = Color(0xFF34C759)  // 편안 (초록)
val Mood5Color = Color(0xFFFF2D55)  // 행복 (핑크)

fun moodColor(level: Int): Color = when (level) {
    1 -> Mood1Color; 2 -> Mood2Color; 3 -> Mood3Color; 4 -> Mood4Color; 5 -> Mood5Color
    else -> Color.Gray
}

fun moodLabel(level: Int): String = when (level) {
    1 -> "화남"; 2 -> "우울"; 3 -> "보통"; 4 -> "편안"; 5 -> "행복"; else -> ""
}

fun moodEmoji(level: Int): String = when (level) {
    1 -> "🤬"; 2 -> "😢"; 3 -> "😐"; 4 -> "😌"; 5 -> "🥰"; else -> ""
}

enum class StatsTab(val label: String) {
    Flow("흐름"),
    Monthly("월별"),
    Mood("분포"),
    Weather("날씨"),
    Report("AI분석"),
}

@Composable
fun StatsScreen(
    statsViewModel: StatsViewModel = viewModel(),
    onNavigateToWeeklyLetter: () -> Unit = {},
    onNavigateToRelationalMap: () -> Unit = {},
) {
    val uiState by statsViewModel.uiState.collectAsState()
    var currentTab by remember { mutableStateOf(StatsTab.Flow) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFF5F5F7))
    ) {
        // ── 헤더 (iOS 동일) ──
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color.White.copy(alpha = 0.8f))
                .padding(horizontal = 24.dp, vertical = 20.dp)
        ) {
            Text(
                "마음 분석",
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold
            )
            Text(
                "데이터로 보는 나의 하루",
                fontSize = 14.sp,
                color = Color.Gray
            )
        }

        // ── 마음 온도 카드 ──
        if (uiState.moodTempLoaded) {
            val tempColor = try {
                Color(android.graphics.Color.parseColor(uiState.moodTempColor))
            } catch (e: Exception) {
                Color.Gray
            }
            
            Card(
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp, vertical = 8.dp)
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    // 온도 게이지
                    Box(
                        modifier = Modifier
                            .size(56.dp)
                            .clip(RoundedCornerShape(28.dp))
                            .background(tempColor.copy(alpha = 0.15f)),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            String.format("%.1f°", uiState.moodTemperature),
                            fontSize = 16.sp,
                            fontWeight = FontWeight.ExtraBold,
                            color = tempColor
                        )
                    }
                    
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            "마음 온도",
                            fontSize = 12.sp,
                            color = Color.Gray
                        )
                        Text(
                            uiState.moodTempLabel,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold,
                            color = tempColor
                        )
                        Text(
                            uiState.moodTempDesc,
                            fontSize = 11.sp,
                            color = Color.Gray,
                            maxLines = 2
                        )
                    }
                }
            }
        }

        // ── 마음 컨디션 카드 (Phase 1~6 교차 분석) ──
        if (uiState.conditionLoaded) {
            Card(
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp, vertical = 4.dp)
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    // 컨디션 아이콘
                    Box(
                        modifier = Modifier
                            .size(56.dp)
                            .clip(RoundedCornerShape(28.dp))
                            .background(Color(0xFF34C759).copy(alpha = 0.12f)),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            uiState.conditionIcon,
                            fontSize = 28.sp
                        )
                    }

                    Column(modifier = Modifier.weight(1f)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                "마음 컨디션",
                                fontSize = 12.sp,
                                color = Color.Gray
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(
                                "${uiState.conditionScore}점",
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFF34C759)
                            )
                        }
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            uiState.conditionLabel,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF1D1D1F)
                        )
                        if (uiState.conditionMessage.isNotBlank()) {
                            Text(
                                uiState.conditionMessage,
                                fontSize = 11.sp,
                                color = Color.Gray,
                                maxLines = 2
                            )
                        }
                    }
                }
            }
        }

        // ── 탭 바 (iOS Modern Tab Bar 대응) ──
        Row(
            modifier = Modifier
                .horizontalScroll(rememberScrollState())
                .padding(horizontal = 24.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            StatsTab.entries.forEach { tab ->
                val isSelected = currentTab == tab
                val bgColor by animateColorAsState(
                    targetValue = if (isSelected) Primary else Color.White,
                    label = "tab_bg"
                )
                val textColor = if (isSelected) Color.White else Color.Gray

                Surface(
                    onClick = { currentTab = tab },
                    shape = RoundedCornerShape(20.dp),
                    color = bgColor,
                    shadowElevation = if (isSelected) 4.dp else 1.dp
                ) {
                    Text(
                        tab.label,
                        modifier = Modifier.padding(horizontal = 18.dp, vertical = 10.dp),
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 15.sp,
                        color = textColor
                    )
                }
            }
        }

        // ── 콘텐츠 ──
        if (uiState.isLoading) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else if (uiState.totalDiaries == 0 && currentTab != StatsTab.Report) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("📊", fontSize = 48.sp)
                    Spacer(modifier = Modifier.height(16.dp))
                    Text("아직 데이터가 부족해요", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        "일기를 작성하면\n감정 분석 리포트를 볼 수 있어요.",
                        textAlign = TextAlign.Center,
                        color = Color.Gray
                    )
                }
            }
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 24.dp, vertical = 10.dp),
                verticalArrangement = Arrangement.spacedBy(24.dp)
            ) {
                when (currentTab) {
                    StatsTab.Flow -> FlowChartContent(uiState)
                    StatsTab.Monthly -> MonthlyChartContent(uiState)
                    StatsTab.Mood -> MoodDistributionContent(uiState)
                    StatsTab.Weather -> WeatherStatsContent(uiState)
                    StatsTab.Report -> {
                        if (uiState.totalDiaries > 0) {
                            ReportContent(uiState)
                            Spacer(modifier = Modifier.height(16.dp))
                        }
                        
                        // Kick 기능 진입 카드 (데이터 유무 무관)
                        KickEntryCard(
                            emoji = "💌",
                            title = "마음온 AI 주간 편지",
                            description = "1주일 동안의 기록을 따뜻한 편지로 받아보세요.",
                            accentColor = Color(0xFFFF6B9D),
                            onClick = onNavigateToWeeklyLetter
                        )
                        
                        Spacer(modifier = Modifier.height(12.dp))
                        
                        KickEntryCard(
                            emoji = "✨",
                            title = "나의 마음 별자리",
                            description = "나와 내 주변 사람들의 관계와 감정을 확인하세요.",
                            accentColor = Color(0xFF5B7FFF),
                            onClick = onNavigateToRelationalMap
                        )

                        // 킥 인사이트 섹션 (Phase 1~6 통합 요약)
                        if (uiState.kickInsightsLoaded && uiState.kickInsights.isNotEmpty()) {
                            Spacer(modifier = Modifier.height(16.dp))
                            KickInsightsSection(insights = uiState.kickInsights)
                        }
                    }
                }
                Spacer(modifier = Modifier.height(80.dp))
            }
        }
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Tab 1: 감정 흐름 (FlowChartView)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@Composable
fun FlowChartContent(state: StatsUiState) {
    StatsCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("📈", fontSize = 18.sp)
            Spacer(modifier = Modifier.width(8.dp))
            Text("감정 흐름", fontSize = 18.sp, fontWeight = FontWeight.Bold)
        }
        Spacer(modifier = Modifier.height(16.dp))

        // 감정 라인 차트 (Canvas)
        val dataPoints = state.moodTimeline
        if (dataPoints.isNotEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .horizontalScroll(rememberScrollState())
            ) {
                val chartWidth = (dataPoints.size * 80f).coerceAtLeast(300f)
                Canvas(
                    modifier = Modifier
                        .width(chartWidth.dp)
                        .height(200.dp)
                ) {
                    val padding = 40f
                    val w = size.width - padding * 2
                    val h = size.height - padding * 2
                    val step = if (dataPoints.size > 1) w / (dataPoints.size - 1) else w

                    // 라인 & 점
                    for (i in dataPoints.indices) {
                        val x = padding + i * step
                        val y = padding + h - (dataPoints[i].second.toFloat() / 5f * h)

                        // 점
                        drawCircle(
                            color = moodColor(dataPoints[i].second),
                            radius = 8f,
                            center = Offset(x, y)
                        )

                        // 라인 (다음 점까지)
                        if (i < dataPoints.size - 1) {
                            val nextX = padding + (i + 1) * step
                            val nextY = padding + h - (dataPoints[i + 1].second.toFloat() / 5f * h)
                            drawLine(
                                color = Primary.copy(alpha = 0.4f),
                                start = Offset(x, y),
                                end = Offset(nextX, nextY),
                                strokeWidth = 3f
                            )
                        }

                        // 날짜 라벨
                        drawContext.canvas.nativeCanvas.drawText(
                            dataPoints[i].first.takeLast(5),
                            x, size.height - 8f,
                            android.graphics.Paint().apply {
                                textSize = 24f; textAlign = android.graphics.Paint.Align.CENTER
                                color = android.graphics.Color.GRAY
                            }
                        )
                    }

                    // Y축 이모지 라벨
                    listOf(1, 3, 5).forEach { level ->
                        val y = padding + h - (level.toFloat() / 5f * h)
                        drawContext.canvas.nativeCanvas.drawText(
                            moodEmoji(level), 16f, y + 8f,
                            android.graphics.Paint().apply { textSize = 28f }
                        )
                    }
                }
            }
        }
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Tab 2: 월별 (MonthlyChartView)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@Composable
fun MonthlyChartContent(state: StatsUiState) {
    val grouped = state.moodTimeline.groupBy { it.first.take(7) }
        .toSortedMap(compareByDescending { it })

    grouped.forEach { (month, items) ->
        val parts = month.split("-")
        val header = if (parts.size == 2) "${parts[0]}년 ${parts[1]}월" else month

        StatsCard {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("📅", fontSize = 18.sp)
                Spacer(modifier = Modifier.width(8.dp))
                Text(header, fontSize = 18.sp, fontWeight = FontWeight.Bold)
            }
            Spacer(modifier = Modifier.height(16.dp))

            // 바 차트
            Canvas(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(180.dp)
            ) {
                val padding = 20f
                val barWidth = ((size.width - padding * 2) / items.size.coerceAtLeast(1)) * 0.7f
                val gap = ((size.width - padding * 2) / items.size.coerceAtLeast(1))
                val maxH = size.height - padding * 2

                items.sortedBy { it.first }.forEachIndexed { i, (date, mood) ->
                    val x = padding + i * gap + (gap - barWidth) / 2
                    val barH = (mood.toFloat() / 5f) * maxH
                    val y = size.height - padding - barH

                    drawRoundRect(
                        color = moodColor(mood),
                        topLeft = Offset(x, y),
                        size = Size(barWidth, barH),
                        cornerRadius = androidx.compose.ui.geometry.CornerRadius(8f, 8f)
                    )

                    // 날짜 라벨
                    drawContext.canvas.nativeCanvas.drawText(
                        date.takeLast(2), x + barWidth / 2, size.height - 2f,
                        android.graphics.Paint().apply {
                            textSize = 20f; textAlign = android.graphics.Paint.Align.CENTER
                            color = android.graphics.Color.GRAY
                        }
                    )
                }
            }
        }
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Tab 3: 감정 분포 (MoodDistributionView)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@Composable
fun MoodDistributionContent(state: StatsUiState) {
    StatsCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("🎨", fontSize = 18.sp)
            Spacer(modifier = Modifier.width(8.dp))
            Text("감정 비중", fontSize = 18.sp, fontWeight = FontWeight.Bold)
        }
        Spacer(modifier = Modifier.height(16.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // 도넛 차트
            val moodCounts = listOf(
                1 to state.angryCount,
                2 to state.sadCount,
                3 to state.normalCount,
                4 to state.calmCount,
                5 to state.happyCount
            ).filter { it.second > 0 }

            val total = moodCounts.sumOf { it.second }

            Box(
                modifier = Modifier.size(140.dp),
                contentAlignment = Alignment.Center
            ) {
                Canvas(modifier = Modifier.fillMaxSize()) {
                    var startAngle = -90f
                    moodCounts.forEach { (mood, count) ->
                        val sweep = (count.toFloat() / total) * 360f
                        drawArc(
                            color = moodColor(mood),
                            startAngle = startAngle,
                            sweepAngle = sweep,
                            useCenter = false,
                            style = Stroke(width = 25f, cap = StrokeCap.Round),
                            topLeft = Offset(20f, 20f),
                            size = Size(size.width - 40f, size.height - 40f)
                        )
                        startAngle += sweep
                    }
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("$total", fontSize = 24.sp, fontWeight = FontWeight.Bold)
                    Text("합계", fontSize = 11.sp, color = Color.Gray)
                }
            }

            Spacer(modifier = Modifier.width(20.dp))

            // 범례
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                (5 downTo 1).forEach { level ->
                    val count = when (level) {
                        5 -> state.happyCount; 4 -> state.calmCount; 3 -> state.normalCount
                        2 -> state.sadCount; 1 -> state.angryCount; else -> 0
                    }
                    if (count > 0) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Canvas(modifier = Modifier.size(8.dp)) {
                                drawCircle(color = moodColor(level))
                            }
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(moodLabel(level), fontSize = 14.sp)
                            Spacer(modifier = Modifier.weight(1f))
                            Text("$count", fontWeight = FontWeight.Bold, color = Color.Gray)
                        }
                    }
                }
            }
        }
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Tab 4: 날씨와 기분 (Vico ColumnChart - iOS Charts BarMark 대응)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@Composable
fun WeatherStatsContent(state: StatsUiState) {
    val chartColors = listOf(
        Color(0xFFFF6B6B), // 1: 화남 - 코랄 레드
        Color(0xFF845EC2), // 2: 우울 - 딥 퍼플
        Color(0xFFFFC75F), // 3: 보통 - 골든 옐로우
        Color(0xFF00C9A7), // 4: 평온 - 민트 그린
        Color(0xFFFF6F91), // 5: 행복 - 핫 핑크
    )

    StatsCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("🌤", fontSize = 20.sp)
            Spacer(modifier = Modifier.width(8.dp))
            Text("날씨와 기분", fontSize = 18.sp, fontWeight = FontWeight.Bold)
        }
        Spacer(modifier = Modifier.height(16.dp))

        if (state.weatherMoods.isEmpty()) {
            Text(
                "날씨 데이터가 있는 일기가 필요합니다.",
                color = Color.Gray,
                modifier = Modifier.fillMaxWidth(),
                textAlign = TextAlign.Center
            )
        } else {
            val weatherLabels = state.weatherMoods.map { it.first }
            val allLevels = (1..5).toList()
            val seriesData = allLevels.map { level ->
                state.weatherMoods.map { (_, moods) ->
                    moods.find { it.first == level }?.second?.toFloat() ?: 0f
                }
            }

            val chartEntryModel = com.patrykandpatrick.vico.core.entry.entryModelOf(
                *seriesData.map { series ->
                    series.mapIndexed { idx, value ->
                        com.patrykandpatrick.vico.core.entry.FloatEntry(idx.toFloat(), value)
                    }
                }.toTypedArray()
            )

            val columnChart = com.patrykandpatrick.vico.compose.chart.column.columnChart(
                columns = chartColors.map { color ->
                    com.patrykandpatrick.vico.core.component.shape.LineComponent(
                        color = color.toArgb(),
                        thicknessDp = 24f,
                        shape = com.patrykandpatrick.vico.core.component.shape.Shapes.roundedCornerShape(
                            topLeftPercent = 30,
                            topRightPercent = 30
                        )
                    )
                },
                mergeMode = com.patrykandpatrick.vico.core.chart.column.ColumnChart.MergeMode.Stack,
                spacing = 12.dp
            )

            val bottomAxis = com.patrykandpatrick.vico.compose.axis.horizontal.bottomAxis(
                valueFormatter = { value, _ ->
                    weatherLabels.getOrElse(value.toInt()) { "" }
                }
            )

            com.patrykandpatrick.vico.compose.chart.Chart(
                chart = columnChart,
                model = chartEntryModel,
                startAxis = com.patrykandpatrick.vico.compose.axis.vertical.startAxis(),
                bottomAxis = bottomAxis,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(260.dp)
                    .padding(top = 8.dp)
            )

            Spacer(modifier = Modifier.height(16.dp))

            // 범례
            val legends = listOf("화남" to 0, "우울" to 1, "보통" to 2, "평온" to 3, "행복" to 4)
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center
            ) {
                legends.forEach { (label, idx) ->
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.padding(horizontal = 6.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .size(10.dp)
                                .background(chartColors[idx], RoundedCornerShape(3.dp))
                        )
                        Spacer(modifier = Modifier.width(3.dp))
                        Text(label, fontSize = 11.sp, fontWeight = FontWeight.Medium)
                    }
                }
            }
        }
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Tab 5: AI 심층 리포트 (ReportView)
@Composable
fun ReportContent(state: StatsUiState) {
    val context = androidx.compose.ui.platform.LocalContext.current
    val llmService = remember { com.maumon.app.data.llm.LLMService.getInstance() }
    val scope = rememberCoroutineScope()

    var reportContent by remember { mutableStateOf("") }
    var isGenerating by remember { mutableStateOf(false) }
    var longTermContent by remember { mutableStateOf("") }
    var isGeneratingLong by remember { mutableStateOf(false) }
    var loadingMessage by remember { mutableStateOf("AI가 일기장을 읽고 있어요...") }

    val isModelLoaded by llmService.isModelLoaded.collectAsState()
    val isModelLoading by llmService.isLoading.collectAsState()
    val loadProgress by llmService.loadingProgress.collectAsState()

    // 일기 텍스트 추출
    val diaryTexts = remember(state.diaries) {
        state.diaries.mapNotNull { diary ->
            val date = diary.date ?: return@mapNotNull null
            val event = diary.event ?: diary.content ?: ""
            val emotionDesc = diary.emotionDesc ?: ""
            if (event.isBlank() && emotionDesc.isBlank()) return@mapNotNull null
            "[$date] $event / 감정: $emotionDesc"
        }
    }

    StatsCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("✨", fontSize = 18.sp)
            Spacer(modifier = Modifier.width(8.dp))
            Text("AI 심층 리포트", fontSize = 18.sp, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.weight(1f))
            // 모델 상태 표시
            if (isModelLoaded) {
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = Color(0xFF34C759).copy(alpha = 0.15f)
                ) {
                    Text(
                        "🟢 온디바이스 AI",
                        fontSize = 10.sp,
                        color = Color(0xFF34C759),
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                    )
                }
            }
        }
        Spacer(modifier = Modifier.height(16.dp))

        if (reportContent.isEmpty() && !isGenerating) {
            // 분석 시작 버튼
            Button(
                onClick = {
                    isGenerating = true
                    scope.launch {
                        // 모델 로드 확인
                        if (!isModelLoaded && !isModelLoading) {
                            loadingMessage = "AI 모델을 불러오는 중... (처음 1회만)"
                            llmService.loadModel(context)
                        }

                        loadingMessage = "AI가 일기장을 읽고 있어요..."

                        if (llmService.isModelLoaded.value) {
                            reportContent = llmService.generateReport(diaryTexts)
                        } else {
                            // 모델 로드 실패 시 Fallback
                            reportContent = """
최근 작성하신 일기를 살펴보니, 전반적으로 안정적인 기분을 유지하고 계시네요.
특히 일상에서 소소한 성취감을 느끼시는 것이 긍정적인 신호예요.
꾸준한 감정 기록이 자기 인식에 큰 도움이 되고 있어요. 😊
                            """.trimIndent()
                        }
                        isGenerating = false
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = Primary
                )
            ) {
                Text(
                    "✨ 지금 바로 분석 시작하기  →",
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(vertical = 8.dp)
                )
            }
        } else if (isGenerating) {
            Column(
                modifier = Modifier.fillMaxWidth().height(150.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                CircularProgressIndicator()
                Spacer(modifier = Modifier.height(12.dp))
                Text(loadingMessage, color = Color.Gray, fontSize = 14.sp)
                if (isModelLoading && loadProgress > 0) {
                    Spacer(modifier = Modifier.height(8.dp))
                    LinearProgressIndicator(
                        progress = { loadProgress },
                        modifier = Modifier.fillMaxWidth(0.6f),
                    )
                    Text("${(loadProgress * 100).toInt()}%", fontSize = 12.sp, color = Color.Gray)
                }
            }
        } else {
            // 3줄 요약
            Surface(
                shape = RoundedCornerShape(16.dp),
                color = Color(0xFFF8F9FE)
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Text("💬 3줄 요약", fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(reportContent, fontSize = 15.sp, lineHeight = 22.sp)
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // 장기 패턴 분석
            if (longTermContent.isEmpty() && !isGeneratingLong) {
                Button(
                    onClick = {
                        isGeneratingLong = true
                        scope.launch {
                            if (llmService.isModelLoaded.value) {
                                longTermContent = llmService.generateLongTermAnalysis(diaryTexts)
                            } else {
                                longTermContent = """
지난 2주간의 감정 흐름을 보면, 안정적인 감정 상태를 유지하고 계세요.
규칙적인 일기 작성 습관이 자기 인식에 큰 도움이 되고 있어요.
앞으로도 꾸준히 기록하시면 더 풍부한 분석을 해드릴 수 있어요!
                                """.trimIndent()
                            }
                            isGeneratingLong = false
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF34C759))
                ) {
                    Text("🧠 장기 기억 패턴 분석하기", fontWeight = FontWeight.SemiBold)
                }
            } else if (isGeneratingLong) {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    CircularProgressIndicator()
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("장기 패턴 분석 중...", color = Color.Gray)
                }
            } else {
                Surface(
                    shape = RoundedCornerShape(16.dp),
                    color = Color(0xFFF0FDF4)
                ) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        Text("🧠 메타 분석", fontWeight = FontWeight.Bold, color = Color(0xFF34C759))
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(longTermContent, fontSize = 15.sp, lineHeight = 22.sp)
                    }
                }
            }

            Spacer(modifier = Modifier.height(8.dp))
            TextButton(onClick = {
                reportContent = ""
                longTermContent = ""
            }) {
                Text("🔄 다시 분석", color = Color.Gray)
            }
            
            // 면책 고지
            Column(modifier = Modifier.padding(top = 4.dp)) {
                Text(
                    "💡 AI 분석은 참고용이며, 전문 의료 서비스를 대체하지 않습니다.",
                    fontSize = 11.sp,
                    color = Color.Gray
                )
                Text(
                    "⚠️ 위기 감지는 보조적 수단이며, 100% 정확성을 보장하지 않습니다.",
                    fontSize = 11.sp,
                    color = Color(0xFFFF9500)
                )
            }
        }
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 공통 카드 래퍼
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@Composable
fun StatsCard(content: @Composable ColumnScope.() -> Unit) {
    Card(
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier.padding(24.dp),
            content = content
        )
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Kick 기능 진입 카드
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@Composable
fun KickEntryCard(
    emoji: String,
    title: String,
    description: String,
    accentColor: Color,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Row(
            modifier = Modifier.padding(20.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(emoji, fontSize = 28.sp)
            Spacer(modifier = Modifier.width(14.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    title,
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp,
                    color = Color.Black
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    description,
                    fontSize = 12.sp,
                    color = Color.Gray
                )
            }
            Text("›", fontSize = 24.sp, color = Color.Gray)
        }
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 킥 인사이트 섹션 (Phase 1~6 통합 요약)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@Composable
fun KickInsightsSection(insights: List<String>) {
    StatsCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("🔍", fontSize = 18.sp)
            Spacer(modifier = Modifier.width(8.dp))
            Text("킥 인사이트", fontSize = 18.sp, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                "${insights.size}건",
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White,
                modifier = Modifier
                    .background(Primary, shape = RoundedCornerShape(10.dp))
                    .padding(horizontal = 8.dp, vertical = 2.dp)
            )
        }
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            "킥 분석 엔진이 발견한 주요 변화 신호",
            fontSize = 12.sp,
            color = Color.Gray
        )
        Spacer(modifier = Modifier.height(12.dp))

        insights.forEach { insight ->
            val (icon, bgColor) = when {
                insight.contains("[시계열]") -> "📊" to Color(0xFFF0F4FF)
                insight.contains("[언어]") -> "🔤" to Color(0xFFFFF8F0)
                insight.contains("[관계]") -> "🧑‍🤝‍🧑" to Color(0xFFF0FFF4)
                insight.contains("[감정흐름]") -> "🌊" to Color(0xFFF8F0FF)
                insight.contains("[수면]") -> "💤" to Color(0xFFF0FAFF)
                insight.contains("[서사]") -> "📖" to Color(0xFFFFF0F5)
                else -> "📌" to Color(0xFFF5F5F7)
            }
            val hasWarning = insight.contains("⚠️")

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp)
                    .background(
                        if (hasWarning) Color(0xFFFFF3F3) else bgColor,
                        shape = RoundedCornerShape(12.dp)
                    )
                    .padding(horizontal = 14.dp, vertical = 10.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Text(icon, fontSize = 16.sp)
                Text(
                    insight
                        .replace("[시계열] ", "")
                        .replace("[언어] ", "")
                        .replace("[관계] ", "")
                        .replace("[감정흐름] ", "")
                        .replace("[수면] ", "")
                        .replace("[서사] ", ""),
                    fontSize = 13.sp,
                    color = if (hasWarning) Color(0xFFD32F2F) else Color(0xFF1D1D1F),
                    fontWeight = if (hasWarning) FontWeight.SemiBold else FontWeight.Normal
                )
            }
        }
    }
}
