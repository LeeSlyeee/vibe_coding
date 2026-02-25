package com.maumon.app.ui.emergency

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
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

/**
 * 긴급 도움 화면 - iOS AppEmergencyView 대응
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EmergencyScreen() {
    val context = LocalContext.current

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
    ) {
        // 헤더
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 40.dp, bottom = 20.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text("🚨", fontSize = 48.sp)
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                "당신은 혼자가 아닙니다.",
                fontSize = 22.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                "지금 힘든 순간도 반드시 지나갑니다.\n전문가의 도움을 받아보세요.",
                textAlign = TextAlign.Center,
                color = Color.Gray,
                fontSize = 15.sp,
                lineHeight = 22.sp
            )
        }

        // 연락처 카드
        Column(
            modifier = Modifier.padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            ContactCard(
                icon = "📞",
                name = "자살예방 상담전화",
                number = "1393",
                isHighlight = true,
                onClick = {
                    val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:1393"))
                    context.startActivity(intent)
                }
            )
            ContactCard(
                icon = "🏥",
                name = "정신건강 상담전화",
                number = "1577-0199",
                onClick = {
                    val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:15770199"))
                    context.startActivity(intent)
                }
            )
            ContactCard(
                icon = "👮",
                name = "경찰청 (긴급신고)",
                number = "112",
                onClick = {
                    val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:112"))
                    context.startActivity(intent)
                }
            )
        }

        Spacer(modifier = Modifier.height(32.dp))

        // 안내 카드
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF3F3))
        ) {
            Column(modifier = Modifier.padding(20.dp)) {
                Text(
                    "💡 이런 경우 연락하세요",
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp
                )
                Spacer(modifier = Modifier.height(12.dp))
                listOf(
                    "• 죽고 싶다는 생각이 자주 들 때",
                    "• 자해를 하고 싶은 충동이 있을 때",
                    "• 극심한 불안이나 공황이 올 때",
                    "• 주변 사람이 위험해 보일 때"
                ).forEach { text ->
                    Text(
                        text,
                        fontSize = 14.sp,
                        color = Color(0xFF666666),
                        lineHeight = 22.sp
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(40.dp))
    }
}

@Composable
fun ContactCard(
    icon: String,
    name: String,
    number: String,
    isHighlight: Boolean = false,
    onClick: () -> Unit
) {
    Card(
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        modifier = if (isHighlight) Modifier.fillMaxWidth() else Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(icon, fontSize = 28.sp)
            Spacer(modifier = Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    name,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = Color.Black.copy(alpha = 0.8f)
                )
                Text(
                    number,
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.Black
                )
            }
            Button(
                onClick = onClick,
                shape = RoundedCornerShape(20.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (isHighlight) Color(0xFFE74C3C) else Color(0xFF212529)
                )
            ) {
                Text("전화하기", fontSize = 14.sp, fontWeight = FontWeight.Bold)
            }
        }
    }
}
