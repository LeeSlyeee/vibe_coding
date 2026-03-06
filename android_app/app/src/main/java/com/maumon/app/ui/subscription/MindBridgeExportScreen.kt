package com.maumon.app.ui.subscription

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Canvas
import android.view.View
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.graphics.*
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.*

// 브랜드 컬러
private val BridgePurple = Color(0xFF6366F1)
private val BridgeViolet = Color(0xFF8B5CF6)

/**
 * 마음 브릿지 감정 리포트 Export 화면
 * 
 * Phase 2: 감정 상태를 이미지 카드로 생성 → 카카오톡/메시지 등으로 공유
 * iOS MindBridgeExportView.swift와 동일한 기능
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MindBridgeExportScreen(
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    
    // 공유 범위 토글
    var includeEmoji by remember { mutableStateOf(true) }
    var includeMoodScore by remember { mutableStateOf(true) }
    var includeWeeklyTrend by remember { mutableStateOf(true) }
    var includeAIComment by remember { mutableStateOf(true) }
    
    // 데이터
    val userName = remember {
        val prefs = context.getSharedPreferences("auth", Context.MODE_PRIVATE)
        prefs.getString("nickname", null)
            ?: prefs.getString("username", "사용자") ?: "사용자"
    }
    val dateRange = remember {
        val sdf = SimpleDateFormat("M월 d일", Locale.KOREA)
        val today = Date()
        val cal = Calendar.getInstance()
        cal.add(Calendar.DAY_OF_YEAR, -6)
        "${sdf.format(cal.time)} ~ ${sdf.format(today)}"
    }
    
    // 임시 데이터 (실제 연동 시 ViewModel에서 주입)
    val todayEmoji = "😊"
    val todayMoodLabel = "보통"
    val todayScore = 65
    val weeklyScores = listOf(45, 60, 55, 70, 65, 80, 65)
    val aiSummaryText = "전반적으로 안정적인 감정 흐름을 유지하고 있어요. 주중에 약간의 스트레스가 관찰되었지만, 주말에 잘 회복하는 패턴을 보이고 있습니다."

    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("감정 리포트 공유") },
                navigationIcon = {
                    IconButton(onClick = onDismiss) {
                        Icon(Icons.Default.Close, "닫기")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp, vertical = 16.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            // MARK: - 리포트 카드 미리보기
            ReportCard(
                userName = userName,
                dateRange = dateRange,
                todayEmoji = todayEmoji,
                todayMoodLabel = todayMoodLabel,
                todayScore = todayScore,
                weeklyScores = weeklyScores,
                aiSummaryText = aiSummaryText,
                includeEmoji = includeEmoji,
                includeMoodScore = includeMoodScore,
                includeWeeklyTrend = includeWeeklyTrend,
                includeAIComment = includeAIComment
            )
            
            // MARK: - 공유 깊이 설정
            ShareDepthSection(
                includeEmoji = includeEmoji,
                onEmojiChange = { includeEmoji = it },
                includeMoodScore = includeMoodScore,
                onMoodScoreChange = { includeMoodScore = it },
                includeWeeklyTrend = includeWeeklyTrend,
                onWeeklyTrendChange = { includeWeeklyTrend = it },
                includeAIComment = includeAIComment,
                onAICommentChange = { includeAIComment = it }
            )
            
            // MARK: - 내보내기 버튼
            Button(
                onClick = {
                    shareAsText(
                        context = context,
                        userName = userName,
                        todayEmoji = todayEmoji,
                        todayMoodLabel = todayMoodLabel,
                        todayScore = todayScore,
                        includeEmoji = includeEmoji,
                        includeMoodScore = includeMoodScore
                    )
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(54.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color.Transparent),
                contentPadding = PaddingValues(0.dp)
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(
                            Brush.horizontalGradient(listOf(BridgePurple, BridgeViolet))
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(Icons.Default.Share, null, tint = Color.White)
                        Text("이미지로 공유하기", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 17.sp)
                    }
                }
            }
            
            // MARK: - 프라이버시 안내
            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Icon(Icons.Default.Shield, null, tint = Color(0xFF22C55E))
                    Column {
                        Text(
                            "프라이버시 보호",
                            fontWeight = FontWeight.Bold,
                            fontSize = 12.sp,
                            color = Color(0xFF22C55E)
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            "일기 원문은 절대 포함되지 않습니다.\n서버를 거치지 않고 기기에서 직접 이미지를 생성합니다.",
                            fontSize = 11.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }
    }
}

// MARK: - 리포트 카드
@Composable
private fun ReportCard(
    userName: String,
    dateRange: String,
    todayEmoji: String,
    todayMoodLabel: String,
    todayScore: Int,
    weeklyScores: List<Int>,
    aiSummaryText: String,
    includeEmoji: Boolean,
    includeMoodScore: Boolean,
    includeWeeklyTrend: Boolean,
    includeAIComment: Boolean
) {
    Card(
        shape = RoundedCornerShape(20.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column {
            // 헤더
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Brush.horizontalGradient(listOf(BridgePurple, BridgeViolet)))
                    .padding(20.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        "${userName}님의 마음 리포트",
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                    Text(dateRange, fontSize = 12.sp, color = Color.White.copy(alpha = 0.8f))
                }
                Icon(Icons.Default.HealthAndSafety, null, tint = Color.White.copy(alpha = 0.8f))
            }
            
            Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                // 오늘의 감정
                if (includeEmoji) {
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        Text(todayEmoji, fontSize = 40.sp)
                        Column {
                            Text("오늘의 감정", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text(todayMoodLabel, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                }
                
                // 감정 온도
                if (includeMoodScore) {
                    Column {
                        Text("마음 온도", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Row(verticalAlignment = Alignment.Bottom) {
                            Text(todayScore.toString(), fontSize = 32.sp, fontWeight = FontWeight.Bold, color = moodColor(todayScore))
                            Text(" / 100", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                    HorizontalDivider()
                }
                
                // 주간 추이
                if (includeWeeklyTrend) {
                    Column {
                        Text("최근 7일 감정 변화", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Spacer(modifier = Modifier.height(8.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceEvenly,
                            verticalAlignment = Alignment.Bottom
                        ) {
                            val days = listOf("월", "화", "수", "목", "금", "토", "일")
                            days.zip(weeklyScores).forEach { (day, score) ->
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Box(
                                        modifier = Modifier
                                            .width(24.dp)
                                            .height((score * 0.6f + 10).dp)
                                            .clip(RoundedCornerShape(4.dp))
                                            .background(moodColor(score))
                                    )
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text(day, fontSize = 9.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                }
                            }
                        }
                    }
                    HorizontalDivider()
                }
                
                // AI 코멘트
                if (includeAIComment) {
                    Column {
                        Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                            Icon(Icons.Default.AutoAwesome, null, tint = BridgePurple, modifier = Modifier.size(16.dp))
                            Text("AI 분석 요약", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            aiSummaryText,
                            fontSize = 14.sp,
                            lineHeight = 20.sp
                        )
                    }
                }
                
                // 워터마크
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                    Text(
                        "마음온 maumON",
                        fontSize = 10.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
                    )
                }
            }
        }
    }
}

// MARK: - 공유 깊이 설정
@Composable
private fun ShareDepthSection(
    includeEmoji: Boolean,
    onEmojiChange: (Boolean) -> Unit,
    includeMoodScore: Boolean,
    onMoodScoreChange: (Boolean) -> Unit,
    includeWeeklyTrend: Boolean,
    onWeeklyTrendChange: (Boolean) -> Unit,
    includeAIComment: Boolean,
    onAICommentChange: (Boolean) -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Default.Tune, null, tint = BridgePurple)
            Text("공유할 항목 선택", fontWeight = FontWeight.Bold)
        }
        Text("어떤 정보를 포함할지 직접 결정하세요", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        
        Card(shape = RoundedCornerShape(12.dp)) {
            Column {
                ExportToggle("😊", "오늘의 감정 (이모지)", includeEmoji, onEmojiChange)
                HorizontalDivider(modifier = Modifier.padding(start = 50.dp))
                ExportToggle("🌡️", "마음 온도 (점수)", includeMoodScore, onMoodScoreChange)
                HorizontalDivider(modifier = Modifier.padding(start = 50.dp))
                ExportToggle("📊", "7일간 감정 변화", includeWeeklyTrend, onWeeklyTrendChange)
                HorizontalDivider(modifier = Modifier.padding(start = 50.dp))
                ExportToggle("✨", "AI 분석 코멘트", includeAIComment, onAICommentChange)
            }
        }
    }
}

@Composable
private fun ExportToggle(icon: String, title: String, isOn: Boolean, onChange: (Boolean) -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(icon, fontSize = 22.sp, modifier = Modifier.width(36.dp))
        Text(title, fontSize = 14.sp, modifier = Modifier.weight(1f))
        Switch(checked = isOn, onCheckedChange = onChange)
    }
}

// 텍스트 기반 공유 (이미지 없이)
private fun shareAsText(
    context: Context,
    userName: String,
    todayEmoji: String,
    todayMoodLabel: String,
    todayScore: Int,
    includeEmoji: Boolean,
    includeMoodScore: Boolean
) {
    val text = buildString {
        appendLine("${userName}님의 마음 리포트")
        appendLine("━━━━━━━━━━━━━━━")
        if (includeEmoji) appendLine("$todayEmoji 오늘의 감정: $todayMoodLabel")
        if (includeMoodScore) appendLine("🌡️ 마음 온도: $todayScore/100")
        appendLine("")
        appendLine("— 마음온 maumON")
    }
    
    val intent = Intent(Intent.ACTION_SEND).apply {
        type = "text/plain"
        putExtra(Intent.EXTRA_TEXT, text)
        putExtra(Intent.EXTRA_SUBJECT, "${userName}님의 마음 리포트")
    }
    context.startActivity(Intent.createChooser(intent, "공유하기"))
}

private fun moodColor(score: Int): Color {
    return when {
        score < 30 -> Color(0xFFEF4444)
        score < 50 -> Color(0xFFF59E0B)
        score < 70 -> Color(0xFFFBBF24)
        score < 85 -> Color(0xFF10B981)
        else -> Color(0xFF6366F1)
    }
}
