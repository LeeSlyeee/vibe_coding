package com.maumon.app.ui.main

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.maumon.app.data.model.Diary
import com.maumon.app.ui.calendar.CalendarScreen
import com.maumon.app.ui.chat.ChatScreen
import com.maumon.app.ui.emergency.EmergencyScreen
import com.maumon.app.ui.stats.StatsScreen

/**
 * iOS AppMainTabView 1:1 대응
 * Tab 0: 캘린더 / Tab 1: 분석 / Tab 2: 한마디 / Tab 3: 긴급 (빨간색)
 */
enum class TabItem(val label: String, val icon: ImageVector) {
    Calendar("캘린더", Icons.Default.CalendarMonth),
    Stats("분석", Icons.Default.BarChart),
    Chat("한마디", Icons.Default.Chat),
    Emergency("긴급", Icons.Default.Warning),
}

@Composable
fun MainScreen(
    onLogout: () -> Unit,
    onWriteDiary: (dateStr: String) -> Unit = {},
    onViewDiary: (Diary) -> Unit = {},
) {
    var selectedTab by remember { mutableStateOf(TabItem.Calendar) }

    Scaffold(
        bottomBar = {
            NavigationBar(
                containerColor = Color.White,
                tonalElevation = 8.dp
            ) {
                TabItem.entries.forEach { tab ->
                    val isEmergency = tab == TabItem.Emergency
                    val isSelected = selectedTab == tab

                    NavigationBarItem(
                        selected = isSelected,
                        onClick = { selectedTab = tab },
                        icon = {
                            Icon(
                                tab.icon,
                                contentDescription = tab.label,
                                tint = when {
                                    isEmergency && isSelected -> Color.Red
                                    isEmergency -> Color.Red.copy(alpha = 0.6f)
                                    isSelected -> Color.Black
                                    else -> Color.Gray.copy(alpha = 0.5f)
                                }
                            )
                        },
                        label = {
                            Text(
                                tab.label,
                                fontWeight = if (isSelected) FontWeight.Bold
                                    else FontWeight.Normal,
                                color = when {
                                    isEmergency && isSelected -> Color.Red
                                    isEmergency -> Color.Gray
                                    isSelected -> Color.Black
                                    else -> Color.Gray
                                }
                            )
                        }
                    )
                }
            }
        }
    ) { padding ->
        Box(modifier = Modifier.padding(padding)) {
            when (selectedTab) {
                TabItem.Calendar -> CalendarScreen(
                    onWriteDiary = onWriteDiary,
                    onViewDiary = onViewDiary,
                    onLogout = onLogout
                )
                TabItem.Stats -> StatsScreen()
                TabItem.Chat -> ChatScreen()
                TabItem.Emergency -> EmergencyScreen()
            }
        }
    }
}
