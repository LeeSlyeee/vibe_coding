package com.maumon.app.ui.kick

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.maumon.app.data.api.ApiClient
import com.maumon.app.data.model.RelationalLink
import com.maumon.app.data.model.RelationalMapResponse
import com.maumon.app.data.model.RelationalNode
import kotlin.math.cos
import kotlin.math.min
import kotlin.math.sin

// ━━━━━━━━━━━━━━━━━━━━━━━━━
// 데모 데이터
// ━━━━━━━━━━━━━━━━━━━━━━━━━
private val demoMapData = RelationalMapResponse(
    nodes = listOf(
        RelationalNode("Me", 0, 35, "FFD700", null, null, "당신은 이 별자리의 중심이에요. 소중한 사람들이 주변을 밝히고 있어요 💛"),
        RelationalNode("엄마", 1, 26, "FF6B9D", 12, "2026-03-04", "이번 달 가장 많이 떠올린 사람이에요. 안부 전화 한 통은 어떨까요? 📞"),
        RelationalNode("민수", 1, 22, "45B7D1", 7, "2026-03-03", "최근 민수와 함께한 시간 이야기가 많았어요. 좋은 에너지를 주는 친구네요 🙌"),
        RelationalNode("지현", 2, 19, "96CEB4", 5, "2026-03-01", "주로 고민 상담이나 진지한 대화에서 등장했어요. 마음을 나누는 관계인 것 같아요 🌿"),
        RelationalNode("팀장님", 3, 21, "FFEAA7", 9, "2026-03-05", "업무 관련 언급이 많았어요. 이번 주 특히 자주 등장했네요 💼"),
        RelationalNode("수아", 2, 16, "DDA0DD", 3, "2026-02-25", "최근 언급이 줄었어요. 오랜만에 연락해보는 건 어떨까요? 💜"),
        RelationalNode("강아지", 1, 18, "F39C12", 6, "2026-03-05", "매일 함께하는 소중한 존재! 산책 이야기가 기분을 밝게 해주고 있어요 🐾"),
    ),
    links = listOf(
        RelationalLink("Me", "엄마", 12),
        RelationalLink("Me", "민수", 7),
        RelationalLink("Me", "지현", 5),
        RelationalLink("Me", "팀장님", 9),
        RelationalLink("Me", "수아", 3),
        RelationalLink("Me", "강아지", 6),
    )
)

private fun parseHexColor(hex: String): Color {
    val cleanHex = hex.removePrefix("#")
    return try {
        Color(android.graphics.Color.parseColor("#$cleanHex"))
    } catch (_: Exception) {
        Color.Gray
    }
}

/**
 * 마음 별자리 화면
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RelationalMapScreen(onBack: () -> Unit) {
    var mapData by remember { mutableStateOf(demoMapData) }
    var selectedNode by remember { mutableStateOf<RelationalNode?>(null) }

    // API 시도
    LaunchedEffect(Unit) {
        try {
            val response = ApiClient.flaskApi.getMyRelationalMap()
            if (response.isSuccessful) {
                val data = response.body()
                if (data != null && data.nodes.isNotEmpty()) mapData = data
            }
        } catch (_: Exception) { /* 데모 유지 */ }
    }

    // 떠다니는 애니메이션
    val infiniteTransition = rememberInfiniteTransition(label = "float")
    val floatOffset by infiniteTransition.animateFloat(
        initialValue = -6f,
        targetValue = 6f,
        animationSpec = infiniteRepeatable(
            animation = tween(3000, easing = EaseInOutSine),
            repeatMode = RepeatMode.Reverse
        ),
        label = "floatY"
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    colors = listOf(
                        Color(0xFF0F0C29),
                        Color(0xFF1A1A3E),
                        Color(0xFF24243E)
                    )
                )
            )
    ) {
        // 별자리 캔버스
        BoxWithConstraints(
            modifier = Modifier.fillMaxSize()
        ) {
            val widthDp = maxWidth
            val heightDp = maxHeight
            val centerXDp = widthDp / 2
            val centerYDp = heightDp * 0.42f
            val otherNodes = mapData.nodes.filter { it.id != "Me" }
            val nodeCount = otherNodes.size
            val radiusDp = min(widthDp.value, heightDp.value).dp * 0.34f

            // 연결선 Canvas
            Canvas(modifier = Modifier.fillMaxSize()) {
                val cx = size.width / 2
                val cy = size.height * 0.42f
                val radiusPx = radiusDp.toPx()

                mapData.links.forEach { link ->
                    val sourceNode = mapData.nodes.find { it.id == link.source }
                    val targetNode = mapData.nodes.find { it.id == link.target }
                    if (sourceNode != null && targetNode != null) {
                        val sPos = if (sourceNode.id == "Me") Offset(cx, cy) else getNodeOffset(sourceNode.id, otherNodes, cx, cy, radiusPx)
                        val tPos = if (targetNode.id == "Me") Offset(cx, cy) else getNodeOffset(targetNode.id, otherNodes, cx, cy, radiusPx)
                        drawLine(
                            color = Color.White.copy(alpha = 0.15f),
                            start = sPos,
                            end = tPos,
                            strokeWidth = 1.5f
                        )
                    }
                }
            }

            // 노드들
            mapData.nodes.forEach { node ->
                val isMe = node.id == "Me"
                val isSelected = selectedNode?.id == node.id
                val nodeColor = parseHexColor(node.color)
                val starSize = if (isMe) node.size * 2.2f else node.size * 1.6f

                val idx = otherNodes.indexOfFirst { it.id == node.id }
                val angle = if (isMe || idx < 0) 0.0 else (idx.toDouble() / nodeCount) * 2 * Math.PI - Math.PI / 2
                val posX = if (isMe) centerXDp else centerXDp + (radiusDp.value * cos(angle).toFloat()).dp
                val posY = if (isMe) centerYDp else centerYDp + (radiusDp.value * sin(angle).toFloat()).dp
                val animY = if (isMe) 0f else floatOffset * (if (idx % 2 == 0) 1f else -1f)

                Column(
                    modifier = Modifier
                        .offset(
                            x = posX - starSize.dp,
                            y = posY - starSize.dp + animY.dp
                        )
                        .width((starSize * 2f).dp)
                        .clickable {
                            selectedNode = if (selectedNode?.id == node.id) null else node
                        },
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    // 글로우
                    Box(contentAlignment = Alignment.Center) {
                        Box(
                            modifier = Modifier
                                .size((starSize + 20).dp)
                                .clip(CircleShape)
                                .background(nodeColor.copy(alpha = if (isSelected) 0.4f else 0.2f))
                                .blur(12.dp)
                        )
                        Box(
                            modifier = Modifier
                                .size(starSize.dp)
                                .clip(CircleShape)
                                .background(
                                    Brush.radialGradient(
                                        colors = listOf(
                                            Color.White,
                                            nodeColor,
                                            nodeColor.copy(alpha = 0.7f)
                                        )
                                    )
                                )
                        )
                        if (isSelected) {
                            Box(
                                modifier = Modifier
                                    .size((starSize + 6).dp)
                                    .border(2.dp, Color.White.copy(alpha = 0.6f), CircleShape)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(6.dp))

                    Text(
                        if (isMe) "나" else node.id,
                        fontSize = if (isMe) 16.sp else 13.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White,
                        textAlign = TextAlign.Center
                    )
                    if (isMe) {
                        Text("✨", fontSize = 10.sp)
                    }
                }
            }
        }

        // 뒤로가기 버튼
        IconButton(
            onClick = onBack,
            modifier = Modifier
                .padding(top = 44.dp, start = 12.dp)
                .clip(CircleShape)
                .background(Color.White.copy(alpha = 0.15f))
        ) {
            Icon(Icons.Default.ArrowBack, "뒤로", tint = Color.White)
        }

        // 하단 정보 카드
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .align(Alignment.BottomCenter)
                .padding(bottom = 30.dp, start = 20.dp, end = 20.dp)
        ) {
            selectedNode?.let { node ->
                Card(
                    shape = RoundedCornerShape(20.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = Color.White.copy(alpha = 0.1f)
                    ),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(
                                modifier = Modifier
                                    .size(14.dp)
                                    .clip(CircleShape)
                                    .background(parseHexColor(node.color))
                            )
                            Spacer(modifier = Modifier.width(10.dp))
                            Text(
                                if (node.id == "Me") "나" else node.id,
                                fontWeight = FontWeight.Bold,
                                fontSize = 18.sp,
                                color = Color.White
                            )
                            Spacer(modifier = Modifier.weight(1f))

                            node.mentionCount?.let { count ->
                                if (node.id != "Me") {
                                    Surface(
                                        shape = RoundedCornerShape(12.dp),
                                        color = parseHexColor(node.color).copy(alpha = 0.15f)
                                    ) {
                                        Text(
                                            "💬 ${count}회 언급",
                                            fontSize = 12.sp,
                                            fontWeight = FontWeight.Medium,
                                            color = parseHexColor(node.color),
                                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)
                                        )
                                    }
                                }
                            }
                        }

                        node.summary?.let { summary ->
                            Spacer(modifier = Modifier.height(10.dp))
                            Text(
                                summary,
                                fontSize = 14.sp,
                                color = Color.White.copy(alpha = 0.85f),
                                lineHeight = 20.sp
                            )
                        }

                        node.lastSeen?.let { lastSeen ->
                            if (node.id != "Me") {
                                Spacer(modifier = Modifier.height(8.dp))
                                Text(
                                    "📅 마지막 언급: $lastSeen",
                                    fontSize = 11.sp,
                                    color = Color.White.copy(alpha = 0.4f)
                                )
                            }
                        }
                    }
                }
            } ?: run {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.Center
                ) {
                    Text(
                        "👆 별을 터치하면 관계 정보를 볼 수 있어요",
                        fontSize = 12.sp,
                        color = Color.White.copy(alpha = 0.4f)
                    )
                }
            }
        }
    }
}

// 노드 위치 계산 (Canvas용)
private fun getNodeOffset(
    nodeId: String,
    otherNodes: List<RelationalNode>,
    cx: Float,
    cy: Float,
    radiusPx: Float
): Offset {
    val idx = otherNodes.indexOfFirst { it.id == nodeId }
    if (idx < 0) return Offset(cx, cy)
    val total = otherNodes.size
    val angle = (idx.toDouble() / total) * 2 * Math.PI - Math.PI / 2
    return Offset(
        cx + radiusPx * cos(angle).toFloat(),
        cy + radiusPx * sin(angle).toFloat()
    )
}

private val EaseInOutSine = CubicBezierEasing(0.37f, 0f, 0.63f, 1f)
