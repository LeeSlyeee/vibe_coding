package com.maumon.app.ui.diary

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
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.maumon.app.ui.theme.*

/**
 * 일기 작성 화면 - iOS AppDiaryWriteView 대응
 * Phase 1: 마음 가이드 (날씨 + 격려 메시지)
 * Phase 2: 질문 카드 방식 폼 (기분 → 수면 → 사건 → 감정 → 의미 → 자기 독백)
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DiaryWriteScreen(
    dateStr: String,
    diaryToEdit: com.maumon.app.data.model.Diary? = null,
    onDismiss: () -> Unit,
    onSaved: () -> Unit,
    diaryWriteViewModel: DiaryWriteViewModel = viewModel()
) {
    val uiState by diaryWriteViewModel.uiState.collectAsState()

    // 수정 모드: 기존 데이터로 폼 채우기 (iOS onAppear diaryToEdit 대응)
    LaunchedEffect(diaryToEdit) {
        diaryToEdit?.let { edit ->
            diaryWriteViewModel.loadFromDiary(edit)
        }
    }

    // 새 글 작성: 날씨 가져오기 + 마음 가이드 생성 (iOS fetchWeather() → fetchInsight() 대응)
    LaunchedEffect(Unit) {
        if (diaryToEdit == null) {
            diaryWriteViewModel.fetchWeatherAndGuide()
        }
    }

    // 저장 성공 시 화면 닫기
    LaunchedEffect(uiState.isSaved) {
        if (uiState.isSaved) {
            onSaved()
            onDismiss()
        }
    }

    // Phase 분기: 마음 가이드 vs 폼
    AnimatedContent(
        targetState = uiState.showMindGuide,
        transitionSpec = {
            fadeIn() togetherWith fadeOut()
        },
        label = "guide_form_transition"
    ) { showGuide ->
        if (showGuide && !uiState.isEditMode) {
            // ═════════════════════════════════════
            // Phase 1: 마음 가이드 (iOS Insight View)
            // ═════════════════════════════════════
            MindGuideView(
                dateStr = dateStr,
                weather = uiState.weather,
                temperature = uiState.temperature,
                isLoading = uiState.isLoadingGuide,
                message = uiState.guideMessage,
                onDismiss = onDismiss,
                onStartWriting = { diaryWriteViewModel.skipToForm() }
            )
        } else {
            // ═════════════════════════════════════
            // Phase 2: 일기 작성 폼
            // ═════════════════════════════════════
            DiaryFormView(
                dateStr = dateStr,
                uiState = uiState,
                viewModel = diaryWriteViewModel,
                onDismiss = onDismiss
            )
        }
    }
}

// ═══════════════════════════════════════════
// 마음 가이드 뷰 — iOS Insight View 1:1 대응
// ═══════════════════════════════════════════

@Composable
private fun MindGuideView(
    dateStr: String,
    weather: String,
    temperature: Double,
    isLoading: Boolean,
    message: String,
    onDismiss: () -> Unit,
    onStartWriting: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.White)
    ) {
        // 헤더 바
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            TextButton(onClick = onDismiss) {
                Text("닫기", color = Color.Gray)
            }
            Spacer(modifier = Modifier.weight(1f))
            Text(dateStr, fontWeight = FontWeight.Bold, color = Color.Gray)
            Spacer(modifier = Modifier.weight(1f))
            Spacer(modifier = Modifier.width(48.dp)) // 좌우 균형
        }

        // 날씨 정보
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 20.dp),
            horizontalArrangement = Arrangement.Center
        ) {
            Text(weather, color = Color(0xFF007AFF), fontSize = 15.sp)
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                String.format("%.1f°C", temperature),
                color = Color(0xFF007AFF),
                fontSize = 15.sp
            )
        }

        // 메인 콘텐츠
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            if (isLoading) {
                // 로딩 상태 (iOS 대응)
                Box(
                    modifier = Modifier
                        .size(120.dp)
                        .clip(CircleShape)
                        .background(Color(0xFF9C27B0).copy(alpha = 0.1f)),
                    contentAlignment = Alignment.Center
                ) {
                    Text("✨", fontSize = 50.sp)
                }

                Spacer(modifier = Modifier.height(40.dp))

                Text(
                    "마음 가이드를 준비하고 있어요",
                    fontSize = 22.sp,
                    fontWeight = FontWeight.Bold,
                    textAlign = TextAlign.Center
                )

                Spacer(modifier = Modifier.height(20.dp))

                Text(
                    "오늘의 날씨와 지난 감정 흐름을 연결하여\n당신만을 위한 특별한 조언을 만들고 있습니다.",
                    fontSize = 15.sp,
                    color = Color.Gray,
                    textAlign = TextAlign.Center,
                    lineHeight = 24.sp
                )

                Spacer(modifier = Modifier.height(16.dp))

                Text(
                    "잠시만 기다려주세요...",
                    fontSize = 14.sp,
                    color = Color(0xFF9C27B0)
                )

                Spacer(modifier = Modifier.height(24.dp))

                CircularProgressIndicator(
                    modifier = Modifier.size(40.dp),
                    color = Color(0xFF9C27B0),
                    strokeWidth = 3.dp
                )
            } else {
                // 가이드 완료 (iOS 대응)
                Box(
                    modifier = Modifier
                        .size(80.dp)
                        .clip(CircleShape)
                        .background(Color(0xFF9C27B0).copy(alpha = 0.1f)),
                    contentAlignment = Alignment.Center
                ) {
                    Text("🧘‍♀️", fontSize = 36.sp)
                }

                Spacer(modifier = Modifier.height(30.dp))

                Text(
                    "오늘의 마음 가이드",
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF9C27B0)
                )

                Spacer(modifier = Modifier.height(20.dp))

                // 가이드 메시지 박스
                Text(
                    text = message.ifEmpty { "오늘 하루도 수고 많으셨어요." },
                    fontSize = 16.sp,
                    textAlign = TextAlign.Center,
                    lineHeight = 26.sp,
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(
                            Color(0xFF9C27B0).copy(alpha = 0.05f),
                            RoundedCornerShape(15.dp)
                        )
                        .padding(24.dp)
                )

                Spacer(modifier = Modifier.height(40.dp))

                // "오늘의 감정 기록하기" 버튼 (iOS 대응)
                Button(
                    onClick = onStartWriting,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp)
                        .padding(horizontal = 40.dp),
                    shape = RoundedCornerShape(15.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF1D1D1F)
                    )
                ) {
                    Text(
                        "오늘의 감정 기록하기",
                        fontWeight = FontWeight.Bold,
                        color = Color.White,
                        fontSize = 16.sp
                    )
                }
            }
        }
    }
}

// ═══════════════════════════════════════════
// 일기 작성 폼 — iOS showForm = true 상태
// ═══════════════════════════════════════════

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun DiaryFormView(
    dateStr: String,
    uiState: DiaryWriteUiState,
    viewModel: DiaryWriteViewModel,
    onDismiss: () -> Unit
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(dateStr, fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onDismiss) {
                        Icon(Icons.Default.Close, contentDescription = "닫기")
                    }
                },
                actions = {
                    if (uiState.isSaving) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(24.dp).padding(end = 16.dp),
                            strokeWidth = 2.dp
                        )
                    } else {
                        IconButton(
                            onClick = { viewModel.saveDiary(dateStr) },
                            enabled = uiState.canSave
                        ) {
                            Icon(
                                Icons.Default.Save,
                                contentDescription = "저장",
                                tint = if (uiState.canSave) Primary else Color.Gray
                            )
                        }
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
            // 1. 기분 선택
            MoodSelector(
                selectedMood = uiState.mood,
                onMoodSelected = { viewModel.updateMood(it) }
            )

            // 2. 날씨 & 약물
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                // 날씨 (자동 로드된 값 표시)
                Card(
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("오늘의 날씨", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
                        Spacer(modifier = Modifier.height(4.dp))
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            OutlinedTextField(
                                value = uiState.weather,
                                onValueChange = { viewModel.updateWeather(it) },
                                modifier = Modifier.weight(1f),
                                singleLine = true,
                                shape = RoundedCornerShape(8.dp)
                            )
                            if (uiState.isWeatherLoaded) {
                                Text(
                                    String.format("%.0f°", uiState.temperature),
                                    fontSize = 14.sp,
                                    color = Color.Gray,
                                    modifier = Modifier.padding(start = 8.dp)
                                )
                            }
                        }
                    }
                }

                // 약물 (iOS 동적 약물 리스트 대응)
                Card(
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        // 헤더 + 설정 아이콘 (iOS gear icon 대응)
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                "약물 복용",
                                style = MaterialTheme.typography.labelSmall,
                                color = Color.Gray,
                                fontWeight = FontWeight.SemiBold
                            )
                            Spacer(modifier = Modifier.weight(1f))
                            IconButton(
                                onClick = { viewModel.showMedSettings() },
                                modifier = Modifier.size(24.dp)
                            ) {
                                Icon(
                                    Icons.Default.Settings,
                                    contentDescription = "약물 설정",
                                    tint = Color.Gray,
                                    modifier = Modifier.size(18.dp)
                                )
                            }
                        }
                        Spacer(modifier = Modifier.height(8.dp))

                        if (uiState.savedMedications.isEmpty()) {
                            // 등록된 약이 없을 때: 단순 토글 (iOS 대응)
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Checkbox(
                                    checked = uiState.medicationTaken,
                                    onCheckedChange = { viewModel.updateMedication(it) }
                                )
                                Text("복용 완료", style = MaterialTheme.typography.bodyMedium)
                            }
                        } else {
                            // 등록된 약이 있을 때: 개별 체크박스 (iOS takenMeds 대응)
                            uiState.savedMedications.forEach { med ->
                                val isTaken = uiState.takenMedications.contains(med)
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .clickable { viewModel.toggleMedTaken(med) }
                                        .padding(vertical = 2.dp)
                                ) {
                                    Checkbox(
                                        checked = isTaken,
                                        onCheckedChange = { viewModel.toggleMedTaken(med) },
                                        colors = CheckboxDefaults.colors(
                                            checkedColor = Color(0xFF34C759)
                                        )
                                    )
                                    Text(
                                        med,
                                        style = MaterialTheme.typography.bodySmall
                                    )
                                }
                            }
                        }
                    }
                }
            }

            // 약물 설정 다이얼로그 (iOS MedicationSettingView 대응)
            if (uiState.showMedSettings) {
                MedicationSettingDialog(
                    medications = uiState.savedMedications,
                    onAdd = { viewModel.addMedication(it) },
                    onRemove = { viewModel.removeMedication(it) },
                    onDismiss = { viewModel.hideMedSettings() }
                )
            }

            // [Crisis Detection] 위기감지 SOS 다이얼로그
            if (uiState.showCrisisSOSDialog) {
                val context = androidx.compose.ui.platform.LocalContext.current
                AlertDialog(
                    onDismissRequest = { /* 의도적으로 쉽게 닫히지 않음 */ },
                    icon = { Text("🆘", fontSize = 36.sp) },
                    title = {
                        Text(
                            "당신은 혼자가 아닙니다",
                            fontWeight = FontWeight.Bold,
                            textAlign = TextAlign.Center
                        )
                    },
                    text = {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                "지금 힘든 순간도 반드시 지나갑니다.\n전문가의 도움을 받아보세요.",
                                textAlign = TextAlign.Center,
                                color = Color.Gray
                            )
                            Spacer(modifier = Modifier.height(16.dp))

                            // 긴급 연락처 버튼들
                            Button(
                                onClick = {
                                    val intent = android.content.Intent(
                                        android.content.Intent.ACTION_DIAL,
                                        android.net.Uri.parse("tel:1393")
                                    )
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
                                    val intent = android.content.Intent(
                                        android.content.Intent.ACTION_DIAL,
                                        android.net.Uri.parse("tel:15770199")
                                    )
                                    context.startActivity(intent)
                                },
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text("🏥 정신건강 상담전화 1577-0199")
                            }
                            Spacer(modifier = Modifier.height(8.dp))
                            OutlinedButton(
                                onClick = {
                                    val intent = android.content.Intent(
                                        android.content.Intent.ACTION_DIAL,
                                        android.net.Uri.parse("tel:112")
                                    )
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
                            viewModel.dismissCrisisSOSDialog()
                        }) {
                            Text("닫기", color = Color.Gray)
                        }
                    }
                )
            }

            // 3. 질문 카드들
            QuestionCard(
                title = "잠은 잘 주무셨나요?",
                placeholder = "수면 상태를 적어보세요...",
                value = uiState.sleepDesc,
                onValueChange = { viewModel.updateSleep(it) }
            )
            QuestionCard(
                title = "오늘 무슨 일이 있었나요?",
                placeholder = "오늘 있었던 일을 적어보세요...",
                value = uiState.event,
                onValueChange = { viewModel.updateEvent(it) },
                isRequired = true
            )
            QuestionCard(
                title = "어떤 감정이 들었나요?",
                placeholder = "느낀 감정을 표현해보세요...",
                value = uiState.emotionDesc,
                onValueChange = { viewModel.updateEmotionDesc(it) },
                isRequired = true
            )
            QuestionCard(
                title = "감정의 의미는 무엇인가요? (선택)",
                placeholder = "그 감정이 나에게 어떤 의미인지...",
                value = uiState.emotionMeaning,
                onValueChange = { viewModel.updateEmotionMeaning(it) }
            )
            QuestionCard(
                title = "나에게 해주고 싶은 말 (선택)",
                placeholder = "스스로에게 해주고 싶은 말...",
                value = uiState.selfTalk,
                onValueChange = { viewModel.updateSelfTalk(it) }
            )

            // 에러 메시지
            if (uiState.errorMessage != null) {
                Text(
                    text = uiState.errorMessage!!,
                    color = MaterialTheme.colorScheme.error,
                    modifier = Modifier.fillMaxWidth(),
                    textAlign = TextAlign.Center
                )
            }

            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

/** 기분 선택기 (1~5) */
@Composable
fun MoodSelector(selectedMood: Int, onMoodSelected: (Int) -> Unit) {
    val moods = listOf(
        Triple(1, "😡", "화가나"),
        Triple(2, "😢", "우울해"),
        Triple(3, "😐", "그저그래"),
        Triple(4, "🙂", "평온해"),
        Triple(5, "😊", "행복해"),
    )
    val moodColors = listOf(
        Color(0xFFFF453A), Color(0xFF5856D6), Color(0xFFFF9500),
        Color(0xFF34C759), Color(0xFFFF2D55)
    )

    Card(
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                "오늘의 기분",
                style = MaterialTheme.typography.titleSmall,
                color = Color.Gray,
                modifier = Modifier.padding(bottom = 12.dp)
            )
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                moods.forEachIndexed { idx, (level, emoji, label) ->
                    val isSelected = selectedMood == level
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier
                            .clip(RoundedCornerShape(12.dp))
                            .clickable { onMoodSelected(level) }
                            .then(
                                if (isSelected) Modifier
                                    .background(moodColors[idx].copy(alpha = 0.15f))
                                    .border(2.dp, moodColors[idx], RoundedCornerShape(12.dp))
                                else Modifier
                            )
                            .padding(8.dp)
                            .scale(if (isSelected) 1.1f else 1f)
                    ) {
                        Text(emoji, fontSize = 28.sp)
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            label,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Medium,
                            color = if (isSelected) moodColors[idx] else Color.Gray
                        )
                    }
                }
            }
        }
    }
}

/** 질문 카드 */
@Composable
fun QuestionCard(
    title: String,
    placeholder: String,
    value: String,
    onValueChange: (String) -> Unit,
    isRequired: Boolean = false
) {
    Card(
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row {
                Text(
                    title,
                    style = MaterialTheme.typography.titleSmall,
                    color = Color.Gray
                )
                if (isRequired) {
                    Text(" *", color = MaterialTheme.colorScheme.error, fontWeight = FontWeight.Bold)
                }
            }
            Spacer(modifier = Modifier.height(8.dp))
            OutlinedTextField(
                value = value,
                onValueChange = onValueChange,
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 100.dp),
                placeholder = { Text(placeholder, color = Color.Gray.copy(alpha = 0.5f)) },
                shape = RoundedCornerShape(12.dp),
                maxLines = 6
            )
        }
    }
}

// ═══════════════════════════════════════════
// 약물 설정 다이얼로그 — iOS MedicationSettingView 대응
// ═══════════════════════════════════════════

@Composable
fun MedicationSettingDialog(
    medications: List<String>,
    onAdd: (String) -> Unit,
    onRemove: (String) -> Unit,
    onDismiss: () -> Unit
) {
    var newMedName by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text("나의 약물 관리", fontWeight = FontWeight.Bold)
        },
        text = {
            Column {
                // 입력창 + 추가 버튼
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    OutlinedTextField(
                        value = newMedName,
                        onValueChange = { newMedName = it },
                        modifier = Modifier.weight(1f),
                        placeholder = { Text("약 이름 (예: 비타민)") },
                        singleLine = true,
                        shape = RoundedCornerShape(10.dp)
                    )
                    IconButton(
                        onClick = {
                            onAdd(newMedName)
                            newMedName = ""
                        },
                        enabled = newMedName.isNotBlank()
                    ) {
                        Icon(
                            Icons.Default.Add,
                            contentDescription = "추가",
                            tint = if (newMedName.isNotBlank()) Color(0xFF007AFF) else Color.Gray
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // 약물 목록
                if (medications.isEmpty()) {
                    Text(
                        "등록된 약이 없습니다.\n위 입력창에서 약을 추가해보세요.",
                        color = Color.Gray,
                        fontSize = 14.sp,
                        textAlign = TextAlign.Center,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 16.dp)
                    )
                } else {
                    Column(
                        verticalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        medications.forEach { med ->
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .background(
                                        Color(0xFFF5F5F5),
                                        RoundedCornerShape(10.dp)
                                    )
                                    .padding(horizontal = 12.dp, vertical = 10.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text("💊", fontSize = 16.sp)
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(med, modifier = Modifier.weight(1f))
                                IconButton(
                                    onClick = { onRemove(med) },
                                    modifier = Modifier.size(24.dp)
                                ) {
                                    Icon(
                                        Icons.Default.Delete,
                                        contentDescription = "삭제",
                                        tint = Color.Red.copy(alpha = 0.7f),
                                        modifier = Modifier.size(18.dp)
                                    )
                                }
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    "등록된 약들은 일기 작성 시\n확인할 수 있습니다.",
                    fontSize = 12.sp,
                    color = Color.Gray,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("닫기")
            }
        }
    )
}
