package com.maumon.app.ui.share

import androidx.compose.animation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.maumon.app.ui.theme.Primary
import kotlinx.coroutines.launch

/**
 * 보호자/친구 연결 화면 - iOS AppShareView 대응
 * 탭 1: 연결하기 (보호자) - 코드 입력하여 연결
 * 탭 2: 공유하기 - 내 코드 발급, 보호자 목록
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ShareScreen(onBack: () -> Unit = {}) {
    var selectedTab by remember { mutableIntStateOf(0) }
    val tabs = listOf("연결하기 (보호자)", "공유하기")

    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    val connectedUsers by ShareManager.connectedUsers.collectAsState()
    val myGuardians by ShareManager.myGuardians.collectAsState()
    val myCode by ShareManager.myCode.collectAsState()
    val isLoading by ShareManager.isLoading.collectAsState()

    LaunchedEffect(Unit) {
        ShareManager.fetchList("viewer")
        ShareManager.fetchList("sharer")
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("보호자/친구 연결", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, "뒤로")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            TabRow(
                selectedTabIndex = selectedTab,
                containerColor = MaterialTheme.colorScheme.surface
            ) {
                tabs.forEachIndexed { index, title ->
                    Tab(
                        selected = selectedTab == index,
                        onClick = { selectedTab = index },
                        text = {
                            Text(
                                title,
                                fontWeight = if (selectedTab == index) FontWeight.Bold else FontWeight.Normal,
                                fontSize = 14.sp
                            )
                        }
                    )
                }
            }

            when (selectedTab) {
                0 -> ConnectTab(
                    connectedUsers = connectedUsers,
                    isLoading = isLoading,
                    onConnect = { code ->
                        scope.launch { ShareManager.connectWithCode(code) }
                    },
                    onRefresh = {
                        scope.launch { ShareManager.fetchList("viewer") }
                    }
                )
                1 -> ShareTab(
                    myCode = myCode,
                    myGuardians = myGuardians,
                    onGenerateCode = {
                        scope.launch { ShareManager.generateCode(context) }
                    },
                    onRefresh = {
                        scope.launch { ShareManager.fetchList("sharer") }
                    }
                )
            }
        }
    }
}

@Composable
private fun ConnectTab(
    connectedUsers: List<ShareManager.SharedUser>,
    isLoading: Boolean,
    onConnect: (String) -> Unit,
    onRefresh: () -> Unit
) {
    var inputCode by remember { mutableStateOf("") }

    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            Card(
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                elevation = CardDefaults.cardElevation(2.dp)
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Text("초대 코드 입력", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                    Spacer(modifier = Modifier.height(12.dp))
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        OutlinedTextField(
                            value = inputCode,
                            onValueChange = { inputCode = it.uppercase() },
                            modifier = Modifier.weight(1f),
                            placeholder = { Text("8자리 코드") },
                            shape = RoundedCornerShape(12.dp),
                            singleLine = true
                        )
                        Button(
                            onClick = {
                                if (inputCode.isNotBlank()) {
                                    onConnect(inputCode)
                                    inputCode = ""
                                }
                            },
                            shape = RoundedCornerShape(12.dp),
                            enabled = inputCode.isNotBlank(),
                            colors = ButtonDefaults.buttonColors(containerColor = Primary)
                        ) {
                            Text("연결", fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
        }

        item {
            Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Text("연결된 사용자 목록", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                Spacer(modifier = Modifier.weight(1f))
                IconButton(onClick = onRefresh) {
                    Icon(Icons.Default.Refresh, "새로고침", tint = Primary)
                }
            }
        }

        if (isLoading) {
            item {
                Box(modifier = Modifier.fillMaxWidth().padding(32.dp), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            }
        } else if (connectedUsers.isEmpty()) {
            item {
                Text(
                    "아직 연결된 사용자가 없어요.\n위에서 초대 코드를 입력해보세요!",
                    color = Color.Gray, textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth().padding(32.dp), lineHeight = 22.sp
                )
            }
        } else {
            items(connectedUsers) { user -> UserCard(user = user) }
        }
    }
}

@Composable
private fun ShareTab(
    myCode: String,
    myGuardians: List<ShareManager.SharedUser>,
    onGenerateCode: () -> Unit,
    onRefresh: () -> Unit
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        item {
            Spacer(modifier = Modifier.height(32.dp))
            Card(
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFFF3E5F5)),
                elevation = CardDefaults.cardElevation(4.dp)
            ) {
                Column(
                    modifier = Modifier.padding(32.dp).fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text("내 공유 코드", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                    Spacer(modifier = Modifier.height(12.dp))
                    if (myCode.isNotEmpty()) {
                        Text(myCode, fontSize = 32.sp, fontWeight = FontWeight.ExtraBold,
                            color = Color(0xFF7B1FA2), letterSpacing = 4.sp)
                    } else {
                        Text("코드를 발급받으세요", color = Color.Gray, fontSize = 16.sp)
                    }
                }
            }
        }

        item {
            Button(
                onClick = onGenerateCode,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF7B1FA2))
            ) {
                Text(
                    if (myCode.isEmpty()) "코드 발급받기" else "코드 재생성",
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(vertical = 8.dp)
                )
            }
        }

        item {
            Text(
                "이 코드를 보호자/친구에게 전달하세요.\n상대방이 '연결하기' 탭에서 입력하면 연결됩니다.",
                textAlign = TextAlign.Center, color = Color.Gray,
                fontSize = 13.sp, lineHeight = 20.sp
            )
        }

        item {
            Spacer(modifier = Modifier.height(16.dp))
            Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Text("연결된 보호자", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                Spacer(modifier = Modifier.weight(1f))
                IconButton(onClick = onRefresh) {
                    Icon(Icons.Default.Refresh, "새로고침", tint = Primary)
                }
            }
        }

        if (myGuardians.isEmpty()) {
            item {
                Text("아직 연결된 보호자가 없어요.", color = Color.Gray,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth().padding(16.dp))
            }
        } else {
            items(myGuardians) { user -> UserCard(user = user) }
        }
    }
}

@Composable
private fun UserCard(user: ShareManager.SharedUser) {
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(1.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Surface(modifier = Modifier.size(44.dp), shape = CircleShape, color = Primary.copy(alpha = 0.15f)) {
                Box(contentAlignment = Alignment.Center) { Text("👤", fontSize = 20.sp) }
            }
            Spacer(modifier = Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(user.name, fontWeight = FontWeight.Bold, fontSize = 16.sp)
                if (user.connectedAt != null) {
                    Text("연결됨: ${user.connectedAt.take(10)}", fontSize = 12.sp, color = Color.Gray)
                }
            }
            Icon(Icons.Default.ChevronRight, "상세", tint = Color.Gray)
        }
    }
}
