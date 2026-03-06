package com.maumon.app.ui.bridge

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.maumon.app.data.bridge.*

// 브랜드 컬러
private val BridgePurple = Color(0xFF6366F1)
private val BridgeViolet = Color(0xFF8B5CF6)
private val BridgeGreen = Color(0xFF10B981)

/**
 * Phase 3/4/5: 마음 브릿지 메인 화면
 * iOS MindBridgeMainView.swift와 동일
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MindBridgeMainScreen(onDismiss: () -> Unit) {
    val context = LocalContext.current
    val bridgeManager = remember { MindBridgeManager.getInstance(context) }
    val recipients by bridgeManager.recipients.collectAsState()

    var showAddRecipient by remember { mutableStateOf(false) }
    var selectedRecipient by remember { mutableStateOf<BridgeRecipient?>(null) }
    var showShareHistory by remember { mutableStateOf(false) }

    val familyRecipients = recipients.filter { it.type == RecipientType.FAMILY }
    val counselorRecipients = recipients.filter { it.type == RecipientType.COUNSELOR }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("🌉 마음 브릿지") },
                navigationIcon = {
                    IconButton(onClick = onDismiss) {
                        Icon(Icons.Default.Close, contentDescription = "닫기")
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
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            // 헤더
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    "내 마음을 소중한 사람에게",
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    "안전하게 전해보세요",
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold,
                    color = BridgePurple
                )
                Text(
                    "일기 원문은 절대 공유되지 않습니다",
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f)
                )
            }

            // 가족/보호자 섹션
            RecipientSection(
                title = "👨‍👩‍👧 가족 / 보호자",
                type = RecipientType.FAMILY,
                recipients = familyRecipients,
                onAdd = { showAddRecipient = true },
                onManage = { selectedRecipient = it }
            )

            // 상담사/의료진 섹션
            RecipientSection(
                title = "🩺 상담사 / 의료진",
                type = RecipientType.COUNSELOR,
                recipients = counselorRecipients,
                onAdd = { showAddRecipient = true },
                onManage = { selectedRecipient = it }
            )

            // 수신자 추가 버튼
            OutlinedCard(
                onClick = { showAddRecipient = true },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                border = CardDefaults.outlinedCardBorder()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        Icons.Default.AddCircle,
                        contentDescription = null,
                        tint = BridgePurple,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("새 수신자 추가", color = BridgePurple, fontWeight = FontWeight.Medium)
                }
            }

            // 공유 이력
            Card(
                onClick = { showShareHistory = true },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        Icons.Default.History,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        "공유 이력 보기",
                        fontSize = 14.sp,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
                    )
                    Spacer(modifier = Modifier.weight(1f))
                    Icon(
                        Icons.Default.ChevronRight,
                        contentDescription = null,
                        modifier = Modifier.size(16.dp),
                        tint = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.3f)
                    )
                }
            }

            // 프라이버시 배지
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                )
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Icon(
                        Icons.Default.Shield,
                        contentDescription = null,
                        tint = BridgeGreen
                    )
                    Column {
                        Text(
                            "프라이버시 보호",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            color = BridgeGreen
                        )
                        Text(
                            "모든 공유 항목은 기본 OFF입니다.\n사용자가 직접 켜야만 공유됩니다.\n일기 원문은 어떤 경로로도 절대 공유되지 않습니다.",
                            fontSize = 10.sp,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f)
                        )
                    }
                }
            }
        }
    }

    // 수신자 추가 다이얼로그
    if (showAddRecipient) {
        AddRecipientDialog(
            onDismiss = { showAddRecipient = false },
            onAdd = { name, type, schedule ->
                bridgeManager.addRecipient(name, type, schedule)
                showAddRecipient = false
            }
        )
    }

    // 수신자 설정 (Phase 4: 공유 깊이)
    selectedRecipient?.let { recipient ->
        RecipientDepthSettingsDialog(
            recipient = recipient,
            bridgeManager = bridgeManager,
            onDismiss = { selectedRecipient = null }
        )
    }

    // 공유 이력 (Phase 5)
    if (showShareHistory) {
        ShareHistoryDialog(
            bridgeManager = bridgeManager,
            onDismiss = { showShareHistory = false }
        )
    }
}

@Composable
private fun RecipientSection(
    title: String,
    type: RecipientType,
    recipients: List<BridgeRecipient>,
    onAdd: () -> Unit,
    onManage: (BridgeRecipient) -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(title, fontSize = 16.sp, fontWeight = FontWeight.Bold)

        if (recipients.isEmpty()) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Icon(
                        if (type == RecipientType.FAMILY) Icons.Default.People else Icons.Default.LocalHospital,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.4f)
                    )
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            if (type == RecipientType.FAMILY) "가족을 추가해보세요" else "상담사를 연결해보세요",
                            fontSize = 14.sp,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                        )
                        Text(
                            if (type == RecipientType.FAMILY) "감정 리포트를 안전하게 공유합니다"
                            else "AI 분석 결과를 대시보드로 전달합니다",
                            fontSize = 11.sp,
                            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.4f)
                        )
                    }
                    Button(
                        onClick = onAdd,
                        colors = ButtonDefaults.buttonColors(containerColor = BridgePurple),
                        contentPadding = PaddingValues(horizontal = 14.dp, vertical = 6.dp)
                    ) { Text("추가", fontSize = 12.sp) }
                }
            }
        } else {
            recipients.forEach { recipient ->
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        // 아바타
                        Box(
                            modifier = Modifier
                                .size(40.dp)
                                .clip(CircleShape)
                                .background(
                                    Brush.linearGradient(
                                        if (recipient.type == RecipientType.FAMILY)
                                            listOf(BridgePurple, BridgeViolet)
                                        else
                                            listOf(BridgeGreen, Color(0xFF059669))
                                    )
                                ),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                recipient.name.take(1),
                                fontSize = 16.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color.White
                            )
                        }

                        Column(modifier = Modifier.weight(1f)) {
                            Text(recipient.name, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(4.dp)
                            ) {
                                Box(
                                    modifier = Modifier
                                        .size(6.dp)
                                        .clip(CircleShape)
                                        .background(if (recipient.isActive) BridgeGreen else Color(0xFFF59E0B))
                                )
                                Text(
                                    if (recipient.isActive) "공유 중" else "일시 중지",
                                    fontSize = 11.sp,
                                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f)
                                )
                                recipient.shareSchedule?.let {
                                    Text(
                                        "· ${it.displayName}",
                                        fontSize = 11.sp,
                                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f)
                                    )
                                }
                            }
                        }

                        // 관리 버튼
                        TextButton(
                            onClick = { onManage(recipient) },
                            colors = ButtonDefaults.textButtonColors(contentColor = BridgePurple)
                        ) { Text("관리", fontSize = 12.sp) }
                    }
                }
            }
        }
    }
}

@Composable
private fun AddRecipientDialog(
    onDismiss: () -> Unit,
    onAdd: (String, RecipientType, ShareSchedule?) -> Unit
) {
    var name by remember { mutableStateOf("") }
    var type by remember { mutableStateOf(RecipientType.FAMILY) }
    var schedule by remember { mutableStateOf(ShareSchedule.WEEKLY) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("수신자 추가") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("이름 (예: 엄마, 김OO 상담사)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )

                // 유형 선택
                Text("유형", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilterChip(
                        selected = type == RecipientType.FAMILY,
                        onClick = { type = RecipientType.FAMILY },
                        label = { Text("👨‍👩‍👧 가족") }
                    )
                    FilterChip(
                        selected = type == RecipientType.COUNSELOR,
                        onClick = { type = RecipientType.COUNSELOR },
                        label = { Text("🩺 상담사") }
                    )
                }

                if (type == RecipientType.FAMILY) {
                    Text("공유 주기", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                    Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                        ShareSchedule.entries.forEach { s ->
                            FilterChip(
                                selected = schedule == s,
                                onClick = { schedule = s },
                                label = { Text(s.displayName, fontSize = 11.sp) }
                            )
                        }
                    }
                }

                // 안내
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Icon(Icons.Default.CheckCircle, contentDescription = null, tint = BridgeGreen, modifier = Modifier.size(16.dp))
                    Text("일기 원문은 절대 포함되지 않습니다", fontSize = 12.sp)
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = { onAdd(name, type, if (type == RecipientType.FAMILY) schedule else null) },
                enabled = name.isNotBlank()
            ) { Text("추가", fontWeight = FontWeight.Bold) }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("취소") }
        }
    )
}

// Phase 4: 공유 깊이 설정 다이얼로그
@Composable
private fun RecipientDepthSettingsDialog(
    recipient: BridgeRecipient,
    bridgeManager: MindBridgeManager,
    onDismiss: () -> Unit
) {
    val settings = remember { mutableStateOf(bridgeManager.getDepthSettings(recipient.id)) }
    var schedule by remember { mutableStateOf(recipient.shareSchedule ?: ShareSchedule.WEEKLY) }
    var isActive by remember { mutableStateOf(recipient.isActive) }
    var showDeleteConfirm by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Box(
                    modifier = Modifier
                        .size(32.dp)
                        .clip(CircleShape)
                        .background(
                            Brush.linearGradient(
                                if (recipient.type == RecipientType.FAMILY)
                                    listOf(BridgePurple, BridgeViolet)
                                else
                                    listOf(BridgeGreen, Color(0xFF059669))
                            )
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    Text(recipient.name.take(1), color = Color.White, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                }
                Column {
                    Text(recipient.name, fontSize = 16.sp)
                    Text(
                        if (recipient.type == RecipientType.FAMILY) "가족 / 보호자" else "상담사 / 의료진",
                        fontSize = 11.sp,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f)
                    )
                }
            }
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                // 활성/비활성
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("공유 활성화", modifier = Modifier.weight(1f))
                    Switch(checked = isActive, onCheckedChange = { isActive = it })
                }

                Divider()

                Text("${recipient.name}에게 공유할 정보", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                Text("기본 OFF — 직접 켜야 공유됩니다", fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f))

                DepthToggle("🟢", "주간 감정 상태", settings.value.moodStatus) {
                    settings.value = settings.value.copy(moodStatus = it)
                }
                DepthToggle("📊", "감정 변화 그래프", settings.value.moodGraph) {
                    settings.value = settings.value.copy(moodGraph = it)
                }
                DepthToggle("✨", "AI 분석 요약", settings.value.aiSummary) {
                    settings.value = settings.value.copy(aiSummary = it)
                }
                DepthToggle("📋", "7개 항목 상세 분석", settings.value.detailedAnalysis) {
                    settings.value = settings.value.copy(detailedAnalysis = it)
                }
                DepthToggle("🔑", "감정 트리거 키워드", settings.value.triggerKeywords) {
                    settings.value = settings.value.copy(triggerKeywords = it)
                }

                if (recipient.type == RecipientType.FAMILY) {
                    Divider()
                    Text("공유 주기", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                    Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                        ShareSchedule.entries.forEach { s ->
                            FilterChip(
                                selected = schedule == s,
                                onClick = { schedule = s },
                                label = { Text(s.displayName, fontSize = 11.sp) }
                            )
                        }
                    }
                }

                Divider()

                // 삭제 버튼
                TextButton(
                    onClick = { showDeleteConfirm = true },
                    colors = ButtonDefaults.textButtonColors(contentColor = Color.Red)
                ) {
                    Icon(Icons.Default.Delete, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("수신자 삭제")
                }
            }
        },
        confirmButton = {
            TextButton(onClick = {
                bridgeManager.updateDepthSettings(recipient.id, settings.value)
                bridgeManager.updateRecipient(recipient.id, isActive, schedule)
                onDismiss()
            }) { Text("저장", fontWeight = FontWeight.Bold, color = BridgePurple) }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("닫기") }
        }
    )

    if (showDeleteConfirm) {
        AlertDialog(
            onDismissRequest = { showDeleteConfirm = false },
            title = { Text("수신자를 삭제할까요?") },
            text = { Text("${recipient.name}에 대한 공유 설정이 모두 삭제됩니다.") },
            confirmButton = {
                TextButton(onClick = {
                    bridgeManager.removeRecipient(recipient.id)
                    showDeleteConfirm = false
                    onDismiss()
                }) { Text("삭제", color = Color.Red) }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteConfirm = false }) { Text("취소") }
            }
        )
    }
}

@Composable
private fun DepthToggle(icon: String, title: String, isOn: Boolean, onToggle: (Boolean) -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Text(icon, fontSize = 20.sp, modifier = Modifier.width(32.dp))
        Text(title, fontSize = 13.sp, modifier = Modifier.weight(1f))
        Switch(
            checked = isOn,
            onCheckedChange = onToggle,
            modifier = Modifier.height(24.dp)
        )
    }
}

// Phase 5: 공유 이력
@Composable
private fun ShareHistoryDialog(bridgeManager: MindBridgeManager, onDismiss: () -> Unit) {
    val history by bridgeManager.shareHistory.collectAsState()

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("공유 이력") },
        text = {
            if (history.isEmpty()) {
                Column(
                    modifier = Modifier.fillMaxWidth().padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Icon(
                        Icons.Default.History,
                        contentDescription = null,
                        modifier = Modifier.size(48.dp),
                        tint = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.3f)
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("공유 이력이 없습니다", color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f))
                }
            } else {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    history.take(20).forEach { entry ->
                        Row {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(entry.recipientName, fontSize = 13.sp, fontWeight = FontWeight.Medium)
                                Text(entry.sharedItems, fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f))
                            }
                            Column(horizontalAlignment = Alignment.End) {
                                Text(entry.formattedDate, fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.5f))
                                if (entry.wasViewed) {
                                    Text("열람됨", fontSize = 9.sp, color = Color.Blue)
                                }
                            }
                        }
                        Divider()
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) { Text("닫기") }
        }
    )
}
