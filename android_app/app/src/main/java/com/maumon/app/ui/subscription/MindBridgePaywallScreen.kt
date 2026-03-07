package com.maumon.app.ui.subscription

import android.app.Activity
import androidx.compose.animation.*
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
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.maumon.app.data.billing.SubscriptionManager

// 브랜드 컬러 (iOS와 동일)
private val BridgePurple = Color(0xFF6366F1)
private val BridgeViolet = Color(0xFF8B5CF6)
private val BridgeGreen = Color(0xFF10B981)
private val BridgeAmber = Color(0xFFF59E0B)
private val BridgeRed = Color(0xFFEF4444)

/**
 * 마음 브릿지 페이월 화면
 *
 * iOS MindBridgePaywallView.swift와 동일한 디자인/기능
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MindBridgePaywallScreen(
    onDismiss: () -> Unit
) {
    val context = LocalContext.current
    val subscriptionManager = remember { SubscriptionManager.getInstance(context) }

    val isLoading by subscriptionManager.isLoading.collectAsState()
    val purchaseError by subscriptionManager.purchaseError.collectAsState()
    val isSubscribed by subscriptionManager.instanceIsSubscribed.collectAsState()

    // 구독 완료 시 자동 닫기
    LaunchedEffect(isSubscribed) {
        if (isSubscribed) onDismiss()
    }

    // 진입 애니메이션
    var appeared by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) { appeared = true }

    val iconScale by animateFloatAsState(
        targetValue = if (appeared) 1f else 0.5f,
        animationSpec = spring(dampingRatio = 0.7f, stiffness = Spring.StiffnessLow),
        label = "iconScale"
    )

    Scaffold(
        containerColor = MaterialTheme.colorScheme.surfaceContainerLow
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            // 닫기 버튼
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End
            ) {
                IconButton(onClick = onDismiss) {
                    Icon(
                        Icons.Default.Close,
                        contentDescription = "닫기",
                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            // MARK: - 헤더
            Box(
                modifier = Modifier
                    .size((80 * iconScale).dp)
                    .clip(CircleShape)
                    .background(
                        Brush.linearGradient(listOf(BridgePurple, BridgeViolet))
                    ),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    Icons.Default.HealthAndSafety,
                    contentDescription = null,
                    tint = Color.White,
                    modifier = Modifier.size(36.dp)
                )
            }

            Text(
                "마음 브릿지",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold
            )

            Text(
                "소중한 사람에게\n내 마음을 안전하게 전해보세요",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center
            )

            // MARK: - 기능 목록
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surface
                ),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
            ) {
                Column(modifier = Modifier.padding(vertical = 8.dp)) {
                    BridgeFeatureItem(
                        icon = Icons.Default.People,
                        iconColor = BridgePurple,
                        title = "가족/보호자 안심 공유",
                        description = "매일 또는 매주, 감정 상태를 카카오톡으로 안전하게 전달",
                        index = 0
                    )
                    HorizontalDivider(modifier = Modifier.padding(start = 72.dp))

                    BridgeFeatureItem(
                        icon = Icons.Default.MedicalServices,
                        iconColor = BridgeGreen,
                        title = "상담사 전용 대시보드",
                        description = "AI 분석 리포트를 상담사에게 공유, 더 깊은 상담 가능",
                        index = 1
                    )
                    HorizontalDivider(modifier = Modifier.padding(start = 72.dp))

                    BridgeFeatureItem(
                        icon = Icons.Default.Tune,
                        iconColor = BridgeAmber,
                        title = "공유 깊이 직접 설정",
                        description = "누구에게, 어디까지 보여줄지 내가 직접 결정",
                        index = 2
                    )
                    HorizontalDivider(modifier = Modifier.padding(start = 72.dp))

                    BridgeFeatureItem(
                        icon = Icons.Default.Shield,
                        iconColor = BridgeRed,
                        title = "일기 원문은 절대 공유 안 됨",
                        description = "AI가 분석한 결과만 공유, 프라이버시 100% 보장",
                        index = 3
                    )
                }
            }

            // MARK: - B2G 안내 (보건소)
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(
                    containerColor = Color(0xFFF0FDF4) // 연한 녹색
                ),
                border = CardDefaults.outlinedCardBorder().copy(
                    // 커스텀 border
                )
            ) {
                Row(
                    modifier = Modifier.padding(15.dp),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Text("🏥", fontSize = 20.sp)
                    Column {
                        Text(
                            "보건소/정신건강복지센터 안내",
                            fontWeight = FontWeight.Bold,
                            fontSize = 14.sp,
                            color = Color(0xFF15803D)
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            "관할 보건소나 정신건강복지센터에서 서비스를 받으면 무료 업그레이드가 가능합니다.",
                            fontSize = 13.sp,
                            color = Color(0xFF15803D)
                        )
                    }
                }
            }

            // MARK: - 가격 & 구매
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                // 무료 체험 배지
                Surface(
                    shape = RoundedCornerShape(20.dp),
                    color = BridgePurple.copy(alpha = 0.1f)
                ) {
                    Text(
                        "7일 무료 체험",
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        color = BridgePurple
                    )
                }

                // 가격
                Row(
                    verticalAlignment = Alignment.Bottom,
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    Text(
                        subscriptionManager.priceText,
                        style = MaterialTheme.typography.headlineSmall,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        "/월",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }

                // 구매 버튼
                Button(
                    onClick = {
                        val activity = context as? Activity
                        if (activity != null) {
                            subscriptionManager.purchase(activity)
                        }
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(54.dp)
                        .shadow(
                            elevation = 8.dp,
                            shape = RoundedCornerShape(14.dp),
                            ambientColor = BridgePurple.copy(alpha = 0.3f)
                        ),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color.Transparent
                    ),
                    contentPadding = PaddingValues(0.dp),
                    enabled = !isLoading
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(
                                Brush.horizontalGradient(listOf(BridgePurple, BridgeViolet))
                            ),
                        contentAlignment = Alignment.Center
                    ) {
                        if (isLoading) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(20.dp),
                                    color = Color.White,
                                    strokeWidth = 2.dp
                                )
                                Text("처리 중...", color = Color.White, fontWeight = FontWeight.Bold)
                            }
                        } else {
                            Text(
                                "무료 체험 시작하기",
                                color = Color.White,
                                fontWeight = FontWeight.Bold,
                                fontSize = 17.sp
                            )
                        }
                    }
                }

                // 에러 메시지
                purchaseError?.let { error ->
                    Text(
                        error,
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.error,
                        textAlign = TextAlign.Center
                    )
                }

                // 구독 복원
                TextButton(onClick = {
                    subscriptionManager.updateSubscriptionStatus()
                }) {
                    Text(
                        "이전 구독 복원하기",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }

                // 안내 문구
                Text(
                    "언제든 해지 가능합니다. 무료 체험 기간 내 해지 시 과금되지 않습니다.",
                    fontSize = 10.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    textAlign = TextAlign.Center
                )
            }
        }
    }
}

/**
 * 기능 목록 아이템 (애니메이션 포함)
 */
@Composable
private fun BridgeFeatureItem(
    icon: ImageVector,
    iconColor: Color,
    title: String,
    description: String,
    index: Int
) {
    var appeared by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) {
        kotlinx.coroutines.delay((index * 100 + 100).toLong())
        appeared = true
    }

    AnimatedVisibility(
        visible = appeared,
        enter = fadeIn(tween(400)) + slideInHorizontally(tween(400)) { 40 }
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.spacedBy(16.dp),
            verticalAlignment = Alignment.Top
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(RoundedCornerShape(10.dp))
                    .background(iconColor.copy(alpha = 0.1f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    icon,
                    contentDescription = null,
                    tint = iconColor,
                    modifier = Modifier.size(20.dp)
                )
            }

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    title,
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    description,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}
