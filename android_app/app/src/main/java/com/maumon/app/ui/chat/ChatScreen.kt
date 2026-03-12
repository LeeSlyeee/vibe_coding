package com.maumon.app.ui.chat

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.platform.LocalContext
import androidx.core.content.ContextCompat
import androidx.lifecycle.viewmodel.compose.viewModel
import com.maumon.app.ui.theme.Primary
import kotlinx.coroutines.launch

data class ChatMessage(
    val id: String = java.util.UUID.randomUUID().toString(),
    val text: String,
    val isUser: Boolean,
)

/**
 * 채팅 화면 - iOS AppChatView 대응
 * 서버 AI / 로컬 AI 전환 가능 (iOS useServerAI Toggle 대응)
 */
@Composable
fun ChatScreen(chatViewModel: ChatViewModel = viewModel()) {
    var inputText by remember { mutableStateOf("") }
    val uiState by chatViewModel.uiState.collectAsState()
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()

    // === 음성 인식 (STT) ===
    val context = LocalContext.current
    val voiceRecorder = remember { VoiceRecorder(context) }
    val isVoiceRecording by voiceRecorder.isRecording.collectAsState()
    val transcribedText by voiceRecorder.transcribedText.collectAsState()
    val voiceError by voiceRecorder.error.collectAsState()

    // 음성 인식 결과 → 입력창에 반영
    LaunchedEffect(transcribedText) {
        if (transcribedText.isNotBlank()) {
            inputText = transcribedText
        }
    }

    // 마이크 권한 요청 런처
    val micPermissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            voiceRecorder.startRecording()
        }
    }

    // VoiceRecorder 리소스 해제
    DisposableEffect(Unit) {
        onDispose {
            voiceRecorder.destroy()
        }
    }

    // 새 메시지 시 스크롤
    LaunchedEffect(uiState.messages.size) {
        if (uiState.messages.isNotEmpty()) {
            listState.animateScrollToItem(uiState.messages.size - 1)
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
    ) {
        // 헤더
        Surface(shadowElevation = 2.dp) {
            Column {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        "한마디",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.weight(1f))
                    // 서버/로컬 전환 버튼 (iOS Toggle 대응)
                    Surface(
                        onClick = { chatViewModel.toggleAIMode() },
                        shape = RoundedCornerShape(12.dp),
                        color = if (uiState.useServerAI) Primary.copy(alpha = 0.15f)
                                else Color(0xFF34C759).copy(alpha = 0.15f)
                    ) {
                        Text(
                            if (uiState.useServerAI) "☁️ 서버 AI" else "📱 로컬 AI",
                            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (uiState.useServerAI) Primary else Color(0xFF34C759)
                        )
                    }
                }
                // On-Device 보안 배지
                if (!uiState.useServerAI) {
                    Surface(
                        modifier = Modifier
                            .padding(start = 16.dp, bottom = 8.dp),
                        shape = RoundedCornerShape(12.dp),
                        color = Color(0xFF34C759).copy(alpha = 0.08f)
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text("🔒", fontSize = 10.sp)
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(
                                "이 대화는 폰 안에서만 처리됩니다",
                                fontSize = 11.sp,
                                color = Color.Gray
                            )
                        }
                    }
                }
            }
        }

        // 위기 배너
        AnimatedVisibility(visible = uiState.showCrisisBanner) {
            val context = LocalContext.current
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp)
                    .clickable {
                        val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:1393"))
                        context.startActivity(intent)
                    },
                shape = RoundedCornerShape(12.dp),
                color = Color.Red.copy(alpha = 0.9f)
            ) {
                Row(
                    modifier = Modifier.padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("⚠️", fontSize = 20.sp)
                    Spacer(modifier = Modifier.width(8.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            "전문가의 도움이 필요하신가요?",
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 13.sp
                        )
                        Text(
                            "자살예방 상담전화: 1393 (터치하여 연결)",
                            color = Color.White.copy(alpha = 0.9f),
                            fontWeight = FontWeight.Bold,
                            fontSize = 13.sp
                        )
                    }
                    Text("📞", fontSize = 22.sp)
                }
            }
        }

        // 메시지 목록
        LazyColumn(
            modifier = Modifier.weight(1f).padding(horizontal = 16.dp),
            state = listState,
            verticalArrangement = Arrangement.spacedBy(8.dp),
            contentPadding = PaddingValues(vertical = 16.dp)
        ) {

            items(uiState.messages) { msg ->
                ChatBubble(message = msg)
            }

            // 타이핑 인디케이터 (loadingHint 반영)
            if (uiState.isTyping) {
                item {
                    Row(
                        modifier = Modifier.padding(start = 4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Surface(
                            shape = RoundedCornerShape(20.dp),
                            color = Color.Gray.copy(alpha = 0.1f)
                        ) {
                            Text(
                                uiState.loadingHint ?: "답변을 생각하는 중...",
                                modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp),
                                color = Color.Gray,
                                fontSize = 14.sp
                            )
                        }
                    }
                }
            }
        }

        // 음성 인식 에러 스낵바
        voiceError?.let { errMsg ->
            Snackbar(
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
                action = {
                    TextButton(onClick = { /* 에러 자동 소멸 */ }) {
                        Text("확인", color = Color.White)
                    }
                }
            ) {
                Text(errMsg, fontSize = 13.sp)
            }
        }

        // 입력 영역
        val inputEnabled = when {
            uiState.isFreeChatMode -> true  // 자유 대화: AI 응답 중에도 항상 입력 가능
            uiState.isTyping -> false       // 가이드 플로우: AI 응답 중 차단
            uiState.isFlowCompleted -> false
            else -> true
        }
        val placeholderText = when {
            isVoiceRecording -> "🎤 듣고 있어요..."
            uiState.isFreeChatMode -> "마음온에게 자유롭게 이야기해보세요..."
            uiState.isFlowCompleted -> "오늘의 기록이 완료되었어요 ✨"
            uiState.currentStepIndex == 0 -> "약 복용 여부를 알려주세요..."
            uiState.currentStepIndex == 1 -> "수면 상태를 알려주세요..."
            uiState.currentStepIndex == 2 -> "오늘 있었던 일을 알려주세요..."
            uiState.currentStepIndex == 3 -> "느낀 감정을 표현해주세요..."
            uiState.currentStepIndex == 4 -> "그 감정의 이유를 생각해보세요..."
            uiState.currentStepIndex == 5 -> "오늘의 나에게 한마디..."
            else -> "메시지 보내기..."
        }

        Surface(shadowElevation = 4.dp) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // 🎙️ 마이크 버튼
                IconButton(
                    onClick = {
                        if (isVoiceRecording) {
                            voiceRecorder.stopRecording()
                        } else {
                            // 권한 확인 후 녹음 시작
                            val hasPermission = ContextCompat.checkSelfPermission(
                                context, Manifest.permission.RECORD_AUDIO
                            ) == PackageManager.PERMISSION_GRANTED
                            if (hasPermission) {
                                voiceRecorder.startRecording()
                            } else {
                                micPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                            }
                        }
                    },
                    enabled = inputEnabled,
                    modifier = Modifier
                        .size(40.dp)
                        .clip(CircleShape)
                        .background(
                            if (isVoiceRecording) Color.Red.copy(alpha = 0.8f)
                            else Color.Gray.copy(alpha = 0.15f)
                        )
                ) {
                    Icon(
                        Icons.Default.Mic,
                        contentDescription = if (isVoiceRecording) "녹음 중지" else "음성 입력",
                        tint = if (isVoiceRecording) Color.White else Color.Gray
                    )
                }

                OutlinedTextField(
                    value = inputText,
                    onValueChange = { inputText = it },
                    modifier = Modifier.weight(1f),
                    placeholder = { Text(placeholderText) },
                    shape = RoundedCornerShape(24.dp),
                    singleLine = true,
                    enabled = inputEnabled
                )

                // 보내기 버튼
                IconButton(
                    onClick = {
                        if (inputText.isNotBlank()) {
                            chatViewModel.sendMessage(inputText)
                            inputText = ""
                        }
                    },
                    enabled = inputText.isNotBlank() && inputEnabled,
                    modifier = Modifier
                        .size(48.dp)
                        .clip(CircleShape)
                        .background(
                            if (inputText.isNotBlank() && inputEnabled) Primary
                            else Color.Gray.copy(alpha = 0.3f)
                        )
                ) {
                    Icon(
                        Icons.Default.Send,
                        contentDescription = "보내기",
                        tint = Color.White
                    )
                }
            }
        }
    }
    
    // [Phase 4] Level 3 위기 감지 시 즉시 SOS 다이얼로그
    if (uiState.showSOSDialog) {
        val context = LocalContext.current
        AlertDialog(
            onDismissRequest = { /* 의도적으로 쉽게 닫히지 않음 */ },
            icon = { Text("🆘", fontSize = 36.sp) },
            title = { 
                Text(
                    "당신은 혼자가 아닙니다",
                    fontWeight = FontWeight.Bold,
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center
                )
            },
            text = {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        "지금 힘든 순간도 반드시 지나갑니다.\n전문가의 도움을 받아보세요.",
                        textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                        color = Color.Gray
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    // 긴급 연락처 버튼들
                    Button(
                        onClick = {
                            val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:1393"))
                            context.startActivity(intent)
                        },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = Color.Red)
                    ) {
                        Text("📞 자살예방 상담전화 1393", fontWeight = FontWeight.Bold)
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedButton(
                        onClick = {
                            val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:15770199"))
                            context.startActivity(intent)
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("🏥 정신건강 상담전화 1577-0199")
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedButton(
                        onClick = {
                            val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:112"))
                            context.startActivity(intent)
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("👮 경찰청 긴급신고 112")
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    chatViewModel.dismissSOSDialog()
                }) {
                    Text("닫기", color = Color.Gray)
                }
            }
        )
    }
}

@Composable
fun ChatBubble(message: ChatMessage) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (message.isUser) Arrangement.End else Arrangement.Start
    ) {
        if (!message.isUser) {
            // AI 아바타
            Surface(
                modifier = Modifier.size(32.dp),
                shape = CircleShape,
                color = Color(0xFFF3E5F5)
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Text("🧘", fontSize = 16.sp)
                }
            }
            Spacer(modifier = Modifier.width(8.dp))
        }

        Surface(
            shape = RoundedCornerShape(
                topStart = 20.dp, topEnd = 20.dp,
                bottomStart = if (message.isUser) 20.dp else 4.dp,
                bottomEnd = if (message.isUser) 4.dp else 20.dp
            ),
            color = if (message.isUser) Primary else Color.Gray.copy(alpha = 0.1f),
            modifier = Modifier.widthIn(max = 280.dp)
        ) {
            Text(
                text = message.text,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp),
                color = if (message.isUser) Color.White else MaterialTheme.colorScheme.onSurface,
                fontSize = 15.sp,
                lineHeight = 22.sp
            )
        }
    }
}
