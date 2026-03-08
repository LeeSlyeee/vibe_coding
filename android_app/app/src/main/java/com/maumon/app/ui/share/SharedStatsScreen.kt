package com.maumon.app.ui.share

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.maumon.app.data.api.ApiClient
import com.maumon.app.ui.theme.Primary
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@Composable
fun SharedStatsScreen(
    targetId: String,
    targetName: String,
    onBack: () -> Unit
) {
    val scope = rememberCoroutineScope()
    var isLoading by remember { mutableStateOf(true) }
    var stats by remember { mutableStateOf<ShareManager.SharedStats?>(null) }
    val lifecycleOwner = androidx.lifecycle.compose.LocalLifecycleOwner.current

    val fetchData = {
        scope.launch {
            withContext(Dispatchers.IO) {
                try {
                    val response = ApiClient.flaskApi.getShareInsights(targetId.toInt())
                    if (response.isSuccessful && response.body() != null) {
                        val gson = com.google.gson.Gson()
                        val json = gson.toJsonTree(response.body())
                        stats = gson.fromJson(json, ShareManager.SharedStats::class.java)
                    }
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
            isLoading = false
        }
    }

    LaunchedEffect(targetId) {
        fetchData()
    }

    DisposableEffect(lifecycleOwner) {
        val observer = androidx.lifecycle.LifecycleEventObserver { _, event ->
            if (event == androidx.lifecycle.Lifecycle.Event.ON_RESUME) {
                fetchData()
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
        }
    }

    Column(modifier = Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)) {
        // Header
        Box(modifier = Modifier.fillMaxWidth().padding(16.dp)) {
            IconButton(onClick = onBack, modifier = Modifier.align(Alignment.CenterStart)) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "뒤로가기")
            }
            Text(
                "${targetName}님의 마음",
                fontSize = 20.sp, fontWeight = FontWeight.Bold,
                modifier = Modifier.align(Alignment.Center)
            )
        }

        if (isLoading) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
        } else if (stats == null) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("데이터를 불러올 수 없습니다.", color = Color.Gray)
            }
        } else {
            val s = stats!!
            LazyColumn(
                modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
                contentPadding = PaddingValues(vertical = 16.dp)
            ) {
                // 1. 요약 카드
                item {
                    Card(
                        shape = RoundedCornerShape(16.dp),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                        elevation = CardDefaults.cardElevation(2.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth().padding(20.dp),
                            horizontalArrangement = Arrangement.SpaceEvenly,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            StatItem("총 기록일", "${s.totalEntries}일")
                            VerticalDivider(modifier = Modifier.height(40.dp))
                            StatItem("연속 기록", "${s.writingStreak}일")
                            VerticalDivider(modifier = Modifier.height(40.dp))
                            StatItem("현재 상태", s.recentStatus)
                        }
                    }
                }

                // 2. 기분 온도 요약
                if (s.moodRestricted == true) {
                    item {
                        Card(
                            shape = RoundedCornerShape(16.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                            elevation = CardDefaults.cardElevation(2.dp)
                        ) {
                            Column(modifier = Modifier.padding(20.dp)) {
                                Text("🔒 감정 통계 비공개", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                                Spacer(modifier = Modifier.height(4.dp))
                                Text("내담자가 마음 온도 통계를 비공개로 설정했습니다.", fontSize = 13.sp, color = Color.Gray)
                            }
                        }
                    }
                } else if (s.avgMood != null) {
                    item {
                        Card(
                            shape = RoundedCornerShape(16.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                            elevation = CardDefaults.cardElevation(2.dp)
                        ) {
                            Column(modifier = Modifier.padding(20.dp)) {
                                Text("📊 마음 온도 요약", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                                Spacer(modifier = Modifier.height(12.dp))
                                Row(verticalAlignment = Alignment.Bottom) {
                                    Text(
                                        String.format("%.1f", s.avgMood),
                                        fontSize = 48.sp, fontWeight = FontWeight.Bold, color = Primary
                                    )
                                    Text(
                                        "점 / 5점",
                                        fontSize = 16.sp, color = Color.Gray,
                                        modifier = Modifier.padding(bottom = 8.dp, start = 4.dp)
                                    )
                                }
                                Spacer(modifier = Modifier.height(8.dp))
                                // 기분 바
                                val progress = ((s.avgMood ?: 0.0) / 5.0).toFloat()
                                val barColor = when {
                                    s.avgMood!! <= 1.5 -> Color.Red
                                    s.avgMood <= 2.5 -> Color(0xFFFFA500)
                                    s.avgMood <= 3.5 -> Color(0xFFFFD700)
                                    s.avgMood <= 4.5 -> Color(0xFF90EE90)
                                    else -> Color(0xFF32CD32)
                                }
                                LinearProgressIndicator(
                                    progress = { progress },
                                    modifier = Modifier.fillMaxWidth().height(8.dp),
                                    color = barColor,
                                    trackColor = Color.Gray.copy(alpha = 0.1f)
                                )
                            }
                        }
                    }
                }

                // 3. 감정 분석 보고서 (문장 형태)
                if (!s.narrativeSummary.isNullOrEmpty()) {
                    item {
                        Card(
                            shape = RoundedCornerShape(16.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                            elevation = CardDefaults.cardElevation(2.dp)
                        ) {
                            Column(modifier = Modifier.padding(20.dp)) {
                                Text("📝 감정 분석 보고서", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                                Spacer(modifier = Modifier.height(12.dp))
                                s.narrativeSummary.forEach { line ->
                                    Text(
                                        text = line,
                                        fontSize = 14.sp,
                                        lineHeight = 22.sp,
                                        modifier = Modifier.padding(bottom = 8.dp)
                                    )
                                }
                            }
                        }
                    }
                }

                // 4. 위기 신호
                if (s.hasSafetyConcern == true) {
                    item {
                        Card(
                            shape = RoundedCornerShape(12.dp),
                            colors = CardDefaults.cardColors(containerColor = Color.Red.copy(alpha = 0.05f)),
                            border = androidx.compose.foundation.BorderStroke(1.dp, Color.Red.copy(alpha = 0.3f))
                        ) {
                            Row(modifier = Modifier.padding(16.dp), verticalAlignment = Alignment.Top) {
                                Text("🚨", fontSize = 24.sp, modifier = Modifier.padding(end = 12.dp))
                                Column {
                                    Text("위기 신호 감지됨", fontWeight = FontWeight.Bold, color = Color.Red)
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text(
                                        "최근 기록에서 위험할 수 있는 감정이 파악되었습니다. 내담자의 안부를 확인해주세요.",
                                        fontSize = 13.sp, color = Color.Gray
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun StatItem(label: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(label, fontSize = 12.sp, color = Color.Gray)
        Spacer(modifier = Modifier.height(4.dp))
        Text(value, fontWeight = FontWeight.Bold, fontSize = 16.sp)
    }
}

@Composable
private fun VerticalDivider(modifier: Modifier = Modifier) {
    Box(
        modifier = modifier.width(1.dp).background(Color.Gray.copy(alpha = 0.2f))
    )
}
