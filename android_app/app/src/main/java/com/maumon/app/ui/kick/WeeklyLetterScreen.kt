package com.maumon.app.ui.kick

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.maumon.app.data.api.ApiClient
import com.maumon.app.data.model.WeeklyLetter
import kotlinx.coroutines.launch

// ━━━━━━━━━━━━━━━━━━━━━━━━━
// 데모 데이터
// ━━━━━━━━━━━━━━━━━━━━━━━━━
private val demoLetters = listOf(
    WeeklyLetter(
        id = 9001,
        title = "2월 24일 ~ 3월 2일 마음 편지",
        content = "안녕하세요, 마음온 AI에요 💌\n\n이번 한 주, 정말 수고 많으셨어요.\n\n일기를 읽다 보니 요즘 좀 바쁘고 지치신 것 같아요. 평소보다 문장이 짧아지고, 감정 표현도 조금 단조로워진 걸 느꼈어요. 아마 몸과 마음이 모두 쉼을 원하고 있는 것 같아요.\n\n그래도 매일 일기를 꾸준히 쓰고 계신 모습이 정말 대단해요. 이렇게 자신의 마음을 들여다보는 시간 자체가 치유의 시작이니까요.\n\n이번 주말에는 좋아하는 음악 한 곡과 따뜻한 차 한 잔으로 자신에게 작은 선물을 해보는 건 어떨까요? ☕🎵\n\n다음 주에도 함께할게요.\n\n마음온 AI 드림 ✉️",
        startDate = "2026-02-24",
        endDate = "2026-03-02",
        isRead = false,
        createdAt = "2026-03-02T23:00:00"
    ),
    WeeklyLetter(
        id = 9002,
        title = "2월 17일 ~ 2월 23일 마음 편지",
        content = "안녕하세요, 마음온 AI에요 💌\n\n지난 한 주 동안 일기를 보니, 직장에서의 이야기가 많았어요. 특히 팀장님과 동료분들 이야기가 자주 등장했는데, 그 속에서 보이는 당신의 노력이 참 멋졌어요.\n\n어휘도 풍부하고 문장도 길었어요. 할 말이 많았던 한 주였나 봐요. 충분히 표현하고, 충분히 기록한 당신에게 박수를 보내요 👏\n\n가까운 사람에게 안부 한 마디 전해보는 건 어때요?\n\n마음온 AI 드림 ✉️",
        startDate = "2026-02-17",
        endDate = "2026-02-23",
        isRead = true,
        createdAt = "2026-02-23T23:00:00"
    ),
    WeeklyLetter(
        id = 9003,
        title = "2월 10일 ~ 2월 16일 마음 편지",
        content = "안녕하세요, 마음온 AI에요 💌\n\n이번 주는 마음이 참 편안했던 한 주 같아요. 일기 속 감정이 다채롭고, 좋아하는 것들에 대한 이야기가 많았거든요.\n\n특히 주말에 산책하며 느꼈던 봄 기운 이야기가 인상적이었어요. 자연 속에서 에너지를 충전하는 당신만의 방법이 참 좋아요 🌿\n\n마음온 AI 드림 ✉️",
        startDate = "2026-02-10",
        endDate = "2026-02-16",
        isRead = true,
        createdAt = "2026-02-16T23:00:00"
    )
)

/**
 * 주간 편지함 화면
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WeeklyLetterScreen(
    targetLetterId: Int? = null,
    onBack: () -> Unit
) {
    var letters by remember { mutableStateOf(demoLetters) }
    var selectedLetter by remember { mutableStateOf<WeeklyLetter?>(null) }
    val scope = rememberCoroutineScope()

    // API 시도 (성공 시 실 데이터로 교체)
    LaunchedEffect(Unit) {
        try {
            val response = ApiClient.flaskApi.getMyWeeklyLetters()
            if (response.isSuccessful) {
                val data = response.body()
                if (!data.isNullOrEmpty()) {
                    letters = data
                    
                    // [DeepLink] Auto-open the specific letter if provided
                    if (targetLetterId != null) {
                        selectedLetter = data.find { it.id == targetLetterId }
                    }
                }
            } else if (targetLetterId != null) {
                // API 실패 시 이미 호딩된 데이터에서 시도 (데모용)
                selectedLetter = letters.find { it.id == targetLetterId }
            }
        } catch (_: Exception) { 
            // 데모 유지
            if (targetLetterId != null) {
                selectedLetter = letters.find { it.id == targetLetterId }
            }
        }
    }

    // 상세 보기 다이얼로그
    selectedLetter?.let { letter ->
        LetterDetailDialog(
            letter = letter,
            onDismiss = { selectedLetter = null }
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("주간 편지함", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, "뒤로")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color.White
                )
            )
        },
        containerColor = Color(0xFFF8F9FE)
    ) { padding ->
        if (letters.isEmpty()) {
            // 빈 상태
            Box(
                modifier = Modifier.fillMaxSize().padding(padding),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("📭", fontSize = 48.sp)
                    Spacer(modifier = Modifier.height(16.dp))
                    Text("아직 도착한 주간 편지가 없어요.", color = Color.Gray)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        "일기를 꾸준히 쓰면 1주일마다\n마음온 AI가 편지를 보내드려요!",
                        fontSize = 13.sp, color = Color.Gray,
                        lineHeight = 18.sp
                    )
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize().padding(padding),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(letters, key = { it.id }) { letter ->
                    LetterRow(
                        letter = letter,
                        onClick = { selectedLetter = letter }
                    )
                }
            }
        }
    }
}

@Composable
private fun LetterRow(letter: WeeklyLetter, onClick: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // 봉투 아이콘
            Box(
                modifier = Modifier
                    .size(50.dp)
                    .clip(CircleShape)
                    .background(
                        if (letter.isRead) Color.Gray.copy(alpha = 0.1f)
                        else Color(0xFF5B7FFF).copy(alpha = 0.1f)
                    ),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    if (letter.isRead) "📭" else "💌",
                    fontSize = 24.sp
                )
            }

            Spacer(modifier = Modifier.width(12.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    letter.title,
                    fontWeight = FontWeight.Bold,
                    fontSize = 15.sp,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "${letter.startDate ?: ""} ~ ${letter.endDate ?: ""}",
                    fontSize = 12.sp,
                    color = Color.Gray
                )
            }

            // 읽지 않음 표시
            if (!letter.isRead) {
                Box(
                    modifier = Modifier
                        .size(10.dp)
                        .clip(CircleShape)
                        .background(Color.Red)
                )
            }
        }
    }
}

@Composable
private fun LetterDetailDialog(letter: WeeklyLetter, onDismiss: () -> Unit) {
    var fullLetter by remember { mutableStateOf<WeeklyLetter?>(null) }
    var isLoading by remember { mutableStateOf(true) }
    var isOpened by remember { mutableStateOf(false) }

    // 편지 상세 로드
    LaunchedEffect(letter.id) {
        if (letter.id >= 9000) {
            // 데모 데이터 → 바로 표시
            kotlinx.coroutines.delay(600)
            fullLetter = letter
            isLoading = false
            isOpened = true
        } else {
            try {
                val response = ApiClient.flaskApi.getWeeklyLetterDetail(letter.id)
                if (response.isSuccessful) {
                    fullLetter = response.body()
                }
            } catch (_: Exception) {
                fullLetter = letter
            }
            isLoading = false
            isOpened = true
        }
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("닫기")
            }
        },
        title = null,
        text = {
            Column(
                modifier = Modifier.fillMaxWidth()
            ) {
                if (isLoading) {
                    Box(
                        modifier = Modifier.fillMaxWidth().height(200.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("💌", fontSize = 48.sp)
                            Spacer(modifier = Modifier.height(12.dp))
                            CircularProgressIndicator(
                                modifier = Modifier.size(24.dp),
                                strokeWidth = 2.dp
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text("편지를 뜯는 중...", color = Color.Gray, fontSize = 13.sp)
                        }
                    }
                } else {
                    fullLetter?.let { fl ->
                        AnimatedVisibility(
                            visible = isOpened,
                            enter = fadeIn() + slideInVertically(initialOffsetY = { it / 4 })
                        ) {
                            Column {
                                Text(
                                    fl.title,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 18.sp
                                )
                                Spacer(modifier = Modifier.height(8.dp))
                                Text(
                                    "${fl.startDate ?: ""} ~ ${fl.endDate ?: ""}",
                                    fontSize = 12.sp,
                                    color = Color.Gray
                                )
                                Spacer(modifier = Modifier.height(4.dp))
                                Divider()
                                Spacer(modifier = Modifier.height(12.dp))
                                Text(
                                    fl.content ?: "내용이 없습니다.",
                                    fontSize = 15.sp,
                                    lineHeight = 24.sp,
                                    color = Color(0xFF2C3E50)
                                )
                            }
                        }
                    }
                }
            }
        }
    )
}
