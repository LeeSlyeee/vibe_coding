package com.maumon.app.ui.settings

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.maumon.app.ui.theme.Primary

/**
 * 사용 가이드 화면 — iOS AppGuideView 1:1 대응
 * 마음온 앱의 사용법을 설명하는 가이드 페이지
 */
@Composable
fun GuideScreen(onBack: () -> Unit) {
    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFF5F5F7))
    ) {
        // 상단 바
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shadowElevation = 1.dp
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 8.dp, vertical = 4.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                TextButton(onClick = onBack) {
                    Text("← 뒤로", color = Primary)
                }
                Spacer(modifier = Modifier.weight(1f))
                Text(
                    "사용 설명서",
                    fontWeight = FontWeight.Bold,
                    fontSize = 17.sp
                )
                Spacer(modifier = Modifier.weight(1f))
                Spacer(modifier = Modifier.width(72.dp)) // 좌우 균형
            }
        }

        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(scrollState)
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(30.dp)
        ) {
            // 헤더
            Column(
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Text(
                    "📖 사용 설명서",
                    fontSize = 28.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF1D1D1F)
                )
                Text(
                    "마음온(maumON)을 100% 활용하는 방법을 알려드려요.",
                    fontSize = 15.sp,
                    color = Color(0xFF86868B)
                )
            }

            // ═════════════════════════════
            // 섹션 1: 일기 작성하기
            // ═════════════════════════════
            Column(verticalArrangement = Arrangement.spacedBy(20.dp)) {
                GuideSectionHeader(
                    title = "📝 일기 작성하기",
                    desc = "하루의 감정을 4단계로 나누어 천천히 기록해보세요."
                )
                Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                    GuideStepCard("1", "사실", "오늘 있었던 일이나 상황을 객관적으로 적어보세요.")
                    GuideStepCard("2", "감정", "그 상황에서 느낀 솔직한 감정들을 단어나 문장으로 표현해요.")
                    GuideStepCard("3", "의미", "왜 그런 감정이 들었는지, 나에게 어떤 의미인지 깊이 생각해보세요.")
                    GuideStepCard("4", "위로", "오늘 하루 고생한 나에게 따뜻한 위로와 격려의 말을 건네주세요.")
                }
            }

            // ═════════════════════════════
            // 섹션 2: AI 감정 분석
            // ═════════════════════════════
            Column(verticalArrangement = Arrangement.spacedBy(20.dp)) {
                GuideSectionHeader(
                    title = "🤖 AI 감정 분석 & 코멘트",
                    desc = "AI가 당신의 마음을 따뜻하게 읽어드립니다."
                )
                GuideFeatureCard(
                    icon = "🧠",
                    title = "60가지 섬세한 감정의 언어",
                    desc = "단순히 '좋다/나쁘다'가 아닌, 60가지의 세분화된 감정으로 당신의 마음을 정확하게 읽어냅니다."
                )
                GuideFeatureCard(
                    icon = "💬",
                    title = "AI 감정 분석 코멘트",
                    desc = "구글의 최신 모델 Gemma 4 (2b)가 문맥과 숨겨진 의미를 파악하여 따뜻한 위로를 건넵니다."
                )
            }

            // ═════════════════════════════
            // 섹션 3: 프라이버시 & 심층 분석
            // ═════════════════════════════
            Column(verticalArrangement = Arrangement.spacedBy(20.dp)) {
                GuideSectionHeader(
                    title = "📊 프라이버시 & 심층 분석",
                    desc = "안전하고 깊이 있는 분석을 경험하세요."
                )
                GuideFeatureCard(
                    icon = "🛡️",
                    title = "🔒 철통 보안 AI 감정 분석",
                    desc = "외부 클라우드 전송 NO! 안전한 로컬/개인 서버 AI가 당신만의 비밀 공간에서 분석합니다.",
                    highlight = true
                )
                GuideFeatureCard(
                    icon = "📑",
                    title = "🧠 심층 감정 리포트",
                    desc = "일기가 3개 이상 모이면, 나만의 감정 분석 보고서를 발행해 드려요. (숨겨진 욕구, 스트레스 원인 분석)"
                )
                GuideFeatureCard(
                    icon = "🔭",
                    title = "🔬 과거 기록 통합 분석",
                    desc = "과거와 현재를 비교 분석하여 감정의 흐름과 성장을 장기적인 통찰로 제공합니다."
                )

                // 작은 피처 카드 2열
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    GuideSmallFeatureCard(
                        title = "🧩 감정 패턴 통계",
                        desc = "날씨와 기분의 상관관계 한눈에 보기",
                        modifier = Modifier.weight(1f)
                    )
                    GuideSmallFeatureCard(
                        title = "🔍 키워드 검색",
                        desc = "감정, 사건 키워드로 과거의 나 찾기",
                        modifier = Modifier.weight(1f)
                    )
                }
            }

            Spacer(modifier = Modifier.height(50.dp))
        }
    }
}

// ═════════════════════════════
// 가이드 공통 컴포넌트
// ═════════════════════════════

@Composable
private fun GuideSectionHeader(title: String, desc: String) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(
            title,
            fontSize = 22.sp,
            fontWeight = FontWeight.Bold,
            color = Color(0xFF1D1D1F)
        )
        Text(desc, fontSize = 15.sp, color = Color(0xFF666666))
    }
}

@Composable
private fun GuideStepCard(num: String, title: String, desc: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color(0xFFFBFBFD), RoundedCornerShape(16.dp))
            .border(1.dp, Color(0xFFF2F2F7), RoundedCornerShape(16.dp))
            .padding(20.dp),
        horizontalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // 번호 원
        Box(
            modifier = Modifier
                .size(28.dp)
                .clip(CircleShape)
                .background(Color(0xFF1D1D1F)),
            contentAlignment = Alignment.Center
        ) {
            Text(num, color = Color.White, fontWeight = FontWeight.Bold, fontSize = 14.sp)
        }

        Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(title, fontWeight = FontWeight.Bold, fontSize = 16.sp, color = Color(0xFF1D1D1F))
            Text(desc, fontSize = 14.sp, color = Color(0xFF555555), lineHeight = 20.sp)
        }
    }
}

@Composable
private fun GuideFeatureCard(
    icon: String,
    title: String,
    desc: String,
    highlight: Boolean = false
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                if (highlight) Color.White else Color(0xFFFBFBFD),
                RoundedCornerShape(20.dp)
            )
            .border(
                width = if (highlight) 2.dp else 1.dp,
                color = if (highlight) Color(0xFF34C759) else Color(0xFFF0F0F5),
                shape = RoundedCornerShape(20.dp)
            )
            .padding(24.dp),
        horizontalArrangement = Arrangement.spacedBy(16.dp),
        verticalAlignment = Alignment.Top
    ) {
        Column(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(title, fontWeight = FontWeight.Bold, fontSize = 16.sp, color = Color(0xFF1D1D1F))
            Text(desc, fontSize = 14.sp, color = Color(0xFF555555), lineHeight = 20.sp)
        }
        Text(icon, fontSize = 32.sp)
    }
}

@Composable
private fun GuideSmallFeatureCard(
    title: String,
    desc: String,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .background(Color(0xFFFBFBFD), RoundedCornerShape(16.dp))
            .border(1.dp, Color(0xFFF0F0F5), RoundedCornerShape(16.dp))
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Text(title, fontWeight = FontWeight.Bold, fontSize = 16.sp, color = Color(0xFF1D1D1F))
        Text(desc, fontSize = 12.sp, color = Color(0xFF555555), lineHeight = 16.sp)
    }
}
