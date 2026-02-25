package com.maumon.app.ui.diary

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.maumon.app.data.model.Diary

/**
 * 일기 상세 보기 화면 - iOS AppDiaryDetailView 대응
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DiaryDetailScreen(
    diary: Diary,
    onBack: () -> Unit,
    onEdit: () -> Unit,
    onDelete: () -> Unit
) {
    val moodEmojis = listOf("", "😡", "😢", "😐", "🙂", "😊")
    val moodLabels = listOf("", "화가나", "우울해", "그저그래", "평온해", "행복해")
    val moodColors = listOf(
        Color.Gray,
        Color(0xFFFF453A), Color(0xFF5856D6), Color(0xFFFF9500),
        Color(0xFF34C759), Color(0xFFFF2D55)
    )
    val level = diary.effectiveMoodLevel.coerceIn(1, 5)

    var showDeleteDialog by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(diary.date ?: "일기") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "뒤로")
                    }
                },
                actions = {
                    IconButton(onClick = onEdit) {
                        Icon(Icons.Default.Edit, contentDescription = "수정")
                    }
                    IconButton(onClick = { showDeleteDialog = true }) {
                        Icon(Icons.Default.Delete, contentDescription = "삭제", tint = Color.Red)
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
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 기분 카드
            Card(
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(
                    containerColor = moodColors[level].copy(alpha = 0.1f)
                )
            ) {
                Column(
                    modifier = Modifier.fillMaxWidth().padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(moodEmojis[level], fontSize = 48.sp)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        moodLabels[level],
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold,
                        color = moodColors[level]
                    )
                    if (!diary.weather.isNullOrBlank()) {
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(diary.weather!!, fontSize = 14.sp, color = Color.Gray)
                    }
                }
            }

            // 내용 카드들
            val sleepText = diary.sleepDesc?.takeIf { it.isNotBlank() }
                ?: diary.sleepCondition?.takeIf { it.isNotBlank() }
            sleepText?.let {
                DetailCard(title = "😴 수면", content = it)
            }
            val eventText = diary.event?.takeIf { it.isNotBlank() }
                ?: diary.content?.takeIf { it.isNotBlank() }
            eventText?.let {
                DetailCard(title = "📝 오늘의 일", content = it)
            }
            diary.emotionDesc?.takeIf { it.isNotBlank() }?.let {
                DetailCard(title = "💭 감정", content = it)
            }
            diary.emotionMeaning?.takeIf { it.isNotBlank() }?.let {
                DetailCard(title = "🔍 감정의 의미", content = it)
            }
            diary.selfTalk?.takeIf { it.isNotBlank() }?.let {
                DetailCard(title = "💬 나에게 하는 말", content = it)
            }

            // 🤖 AI 심리 분석 (iOS AppDiaryDetailView 대응)
            val aiPredLabel = diary.aiPrediction?.takeIf {
                it.isNotBlank() && it != "분석 중..."
            }
            val aiAnalysisText = diary.aiAnalysis?.takeIf { it.isNotBlank() }

            if (aiPredLabel != null || aiAnalysisText != null) {
                Card(
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = Color(0xFFE3F2FD) // 파란색 계열 (iOS 동일)
                    )
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            "🤖 AI 심리 분석",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF1976D2)
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        aiPredLabel?.let {
                            Text(
                                "오늘의 주요 감정: $it",
                                style = MaterialTheme.typography.bodyMedium,
                                fontWeight = FontWeight.SemiBold
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                        }
                        aiAnalysisText?.let {
                            Text(it, style = MaterialTheme.typography.bodyMedium)
                        }
                    }
                }
            }

            // 💡 AI 조언 (iOS ai_advice/ai_comment 대응)
            val aiAdviceText = diary.aiAdvice?.takeIf { it.isNotBlank() }
                ?: diary.aiComment?.takeIf { it.isNotBlank() }
            if (aiAdviceText != null) {
                Card(
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = Color(0xFFE8F5E9) // 녹색 계열 (iOS 동일)
                    )
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            "💡 AI 조언",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF388E3C)
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(aiAdviceText, style = MaterialTheme.typography.bodyMedium)
                    }
                }
            }

            Spacer(modifier = Modifier.height(32.dp))
        }
    }

    // 삭제 확인 다이얼로그
    if (showDeleteDialog) {
        AlertDialog(
            onDismissRequest = { showDeleteDialog = false },
            title = { Text("일기 삭제") },
            text = { Text("이 일기를 삭제하시겠습니까?\n삭제된 일기는 복구할 수 없습니다.") },
            confirmButton = {
                TextButton(onClick = { showDeleteDialog = false; onDelete() }) {
                    Text("삭제", color = Color.Red)
                }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteDialog = false }) {
                    Text("취소")
                }
            }
        )
    }
}

@Composable
fun DetailCard(title: String, content: String) {
    Card(
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(title, style = MaterialTheme.typography.titleSmall, color = Color.Gray)
            Spacer(modifier = Modifier.height(8.dp))
            Text(content, style = MaterialTheme.typography.bodyLarge, lineHeight = 24.sp)
        }
    }
}
