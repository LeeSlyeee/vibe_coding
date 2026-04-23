
import SwiftUI
import Combine

// MARK: - Safe Data Wrapper
struct WriteTargetDate: Identifiable {
    let id = UUID()
    let date: Date
}

// MARK: - Helper Struct
struct CalendarDay: Identifiable {
    let id = UUID()
    let date: Date?
}

struct MoodCalendarView: View {
    @EnvironmentObject var authManager: AuthManager // ✅ Auth Manager
    @ObservedObject var dataManager = LocalDataManager.shared // ✅ Data Observer
    // State Removed
    
    // ... existing vars ...
    @State private var currentDate = Date()
    @State private var diaries: [String: Diary] = [:] // "YYYY-MM-DD" : Diary Object
    @State private var isLoading = false
    @State private var slideDirection: Edge = .trailing // Animation direction
    
    // Navigation State
    @State private var selectedDiary: Diary?
    @State private var showDetail = false
    @State private var errorMessage: String?
    @State private var showErrorAlert = false
    
    // [New] Settings Modal State
    @State private var showSettings = false
    
    // [Step 4] Soft Nudge State
    @State private var showNudgeBanner = true
    @State private var showPremiumFromNudge = false
    
    // Write Modal State (Identifiable Item for Safe Presentation)
    @State private var writeTarget: WriteTargetDate?
    
    // ✅ Base URL (Managed by APIService)
    // let baseURL = "https://217.142.253.35.nip.io/api"
    
    let columns = Array(repeating: GridItem(.flexible()), count: 7)
    
    var body: some View {
        ZStack {
            NavigationView {
                VStack(spacing: 20) {
                    // 상단 헤더
                    // 상단 헤더
                    ZStack {
                        // 1. Center Group: [ < ] [ YYYY년 M월 ] [ > ]
                        HStack(spacing: 20) {
                            Button(action: { changeMonth(by: -1) }) {
                                Image(systemName: "chevron.left")
                                    .font(.title2)
                                    .foregroundColor(.secondaryText)
                            }
                            
                            Text(monthYearString(currentDate))
                                .font(.journalTitle)
                                .foregroundColor(.primaryText)
                            
                            Button(action: { changeMonth(by: 1) }) {
                                Image(systemName: "chevron.right")
                                    .font(.title2)
                                    .foregroundColor(.secondaryText)
                            }
                        }
                        
                        // 2. Trailing Group: [ Hamburger ]
                        HStack {
                            Spacer()
                            Button(action: { showSettings = true }) {
                                Image(systemName: "line.3.horizontal") // 햄버거 메뉴
                                    .font(.title2)
                                    .fontWeight(.semibold)
                                    .foregroundColor(.secondaryText)
                            }
                            .accessibilityIdentifier("SettingsMenuButton")
                        }
                    }
                    .padding(.horizontal)
                    .padding(.top, 20)
                    
                    // 요일 헤더
                    HStack {
                        ForEach(Array(["일", "월", "화", "수", "목", "금", "토"].enumerated()), id: \.offset) { index, day in
                            Text(day)
                                .font(.journalCaption)
                                .fontWeight(.bold)
                                .foregroundColor(index == 0 ? .mood1 : (index == 6 ? .mood2 : .secondaryText))
                                .frame(maxWidth: .infinity)
                        }
                    }
                    
                    // 달력 그리드 (Pull-to-Refresh)
                    ScrollView {
                        // [Fix] Add Spacer to push content down slightly
                        Spacer(minLength: 10)
                        
                        if isLoading {
                            ProgressView().padding()
                        }
                        
                        LazyVGrid(columns: columns, spacing: 15) {
                            ForEach(calendarDays(), id: \.id) { dayItem in
                                if let date = dayItem.date {
                                    let dateStr = dateString(date)
                                    let diary = diaries[dateStr]
                                    
                                    Button(action: { handleDateTap(date, diary: diary) }) {
                                        VStack(spacing: 1) { // 간격 최소화
                                            // 1. 날짜 (토요일=파란, 일요일=빨간)
                                            let wd = Calendar.current.component(.weekday, from: date)
                                            let dayColor: Color = wd == 1 ? .mood1 : (wd == 7 ? .mood2 : (Calendar.current.isDateInToday(date) ? .accent : .primaryText))
                                            Text("\(Calendar.current.component(.day, from: date))")
                                                .font(.system(size: 10, weight: diary != nil ? .bold : .regular))
                                                .foregroundColor(dayColor)
                                                .padding(.top, 4)
                                            
                                            if let d = diary {
                                                VStack(spacing: 0) {
                                                    // 2. 감정 이모지 (AI 우선 적용)
                                                    let aiAsset = getAIAsset(for: d.ai_prediction)
                                                    let asset = aiAsset ?? getMoodAsset(level: d.mood_level)
                                                    
                                                    ZStack(alignment: .bottomTrailing) {
                                                        MoodFaceView(level: asset.level, size: 28)
                                                        
                                                        // [New] 약물 복용 표시
                                                        if d.medication == true {
                                                            Image(systemName: "pills.fill")
                                                                .font(.system(size: 10))
                                                                .foregroundColor(.mood4)
                                                                .background(Circle().fill(Color.cardBg).frame(width: 12, height: 12))
                                                                .offset(x: 4, y: 2)
                                                        }
                                                    }
                                                    .padding(.bottom, 2)
                                                    
                                                    // 3 & 4. AI 예측 (감정 + 퍼센트)
                                                    let (label, percent) = parseAI(d.ai_prediction)
                                                    if !label.isEmpty {
                                                        Text(label)
                                                            .font(.system(size: 8, weight: .bold))
                                                            .foregroundColor(.primaryText)
                                                            .lineLimit(1)
                                                            .minimumScaleFactor(0.7)
                                                        
                                                        if !percent.isEmpty {
                                                            Text(percent)
                                                                .font(.system(size: 7))
                                                                .foregroundColor(.secondaryText)
                                                                .lineLimit(1)
                                                                .minimumScaleFactor(0.7)
                                                        }
                                                    }
                                                }
                                            } else {
                                                Spacer()
                                            }
                                            Spacer(minLength: 2)
                                        }
                                        .frame(height: 75) // 셀 높이 약간 증가
                                        .frame(maxWidth: .infinity)
                                        .background(
                                            RoundedRectangle(cornerRadius: 12)
                                                .fill(diary != nil ? emotionBackgroundColor(for: diary!) : Color.bgMain)
                                        )
                                        .overlay(
                                            Calendar.current.isDateInToday(date) ?
                                                RoundedRectangle(cornerRadius: 12)
                                                    .stroke(Color.accent, lineWidth: 2)
                                                : nil
                                        )
                                    }
                                } else {
                                    Text("") // 빈 칸
                                }
                            }
                        }
                        .padding()
                        .id(currentDate) // Force view refresh for transition
                    }
                    .refreshable {
                        await refreshData()
                    }
                    
                    // [Step 4] Soft Nudge Banner (마음 브릿지 자연스러운 유도)
                    if shouldShowNudge && showNudgeBanner {
                        Button(action: {
                            showPremiumFromNudge = true
                        }) {
                            HStack(spacing: 12) {
                                // 아이콘
                                ZStack {
                                    Circle()
                                        .fill(
                                            LinearGradient(
                                                colors: [Color.gray900.opacity(0.15), Color.gray600.opacity(0.15)],
                                                startPoint: .topLeading,
                                                endPoint: .bottomTrailing
                                            )
                                        )
                                        .frame(width: 40, height: 40)
                                    Image(systemName: "bridge").foregroundColor(.accent)
                                        .font(.system(size: 20))
                                }
                                
                                // 텍스트
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("가족에게 내 마음을 전해보세요")
                                        .font(.system(size: 14, weight: .bold))
                                        .foregroundColor(.primary)
                                    Text("마음 브릿지로 감정 리포트를 안전하게 공유")
                                        .font(.system(size: 11))
                                        .foregroundColor(.secondary)
                                }
                                
                                Spacer()
                                
                                // 닫기 버튼
                                Button(action: {
                                    withAnimation(.easeOut(duration: 0.3)) {
                                        showNudgeBanner = false
                                    }
                                    // 오늘 하루 다시 표시하지 않음
                                    let formatter = DateFormatter()
                                    formatter.dateFormat = "yyyy-MM-dd"
                                    UserDefaults.standard.set(formatter.string(from: Date()), forKey: "nudge_dismissed_date")
                                }) {
                                    Image(systemName: "xmark")
                                        .font(.system(size: 12, weight: .bold))
                                        .foregroundColor(.hintText)
                                        .padding(6)
                                        .background(Color.softTan.opacity(0.3))
                                        .clipShape(Circle())
                                }
                                .buttonStyle(BorderlessButtonStyle())
                            }
                            .padding(14)
                            .background(
                                RoundedRectangle(cornerRadius: 14)
                                    .fill(Color(.systemBackground))
                                    .shadow(color: Color.gray900.opacity(0.1), radius: 8, x: 0, y: 2)
                            )
                            .overlay(
                                RoundedRectangle(cornerRadius: 14)
                                    .stroke(
                                        LinearGradient(
                                            colors: [Color.gray900.opacity(0.3), Color.gray600.opacity(0.15)],
                                            startPoint: .topLeading,
                                            endPoint: .bottomTrailing
                                        ),
                                        lineWidth: 1
                                    )
                            )
                        }
                        .buttonStyle(PlainButtonStyle())
                        .padding(.horizontal)
                        .padding(.top, 8)
                        .transition(.asymmetric(
                            insertion: .move(edge: .bottom).combined(with: .opacity),
                            removal: .opacity
                        ))
                    }
                    
                    // [New] Bottom Manual Sync Button
                    Button(action: {
                        self.isLoading = true
                        // [Fix] Force Sync to recover 'Tombstoned' (Deleted) diaries if they exist on server
                        LocalDataManager.shared.syncWithServer(force: true)
                        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                            self.isLoading = false
                        }
                    }) {
                        HStack {
                            Image(systemName: "arrow.clockwise")
                            Text("데이터 새로고침")
                        }
                        .font(.journalCaption)
                        .foregroundColor(.secondaryText)
                        .padding(8)
                        .background(Color.softTan.opacity(0.5))
                        .cornerRadius(8)
                    }
                    .padding(.top, 10)
                    
                    Spacer()
                    
                    // Hidden Navigation Link for Detail
                    NavigationLink(
                        destination: selectedDiary != nil ? AppDiaryDetailView(diary: selectedDiary!, onDelete: { fetchDiaries() }) : nil,
                        isActive: $showDetail
                    ) { EmptyView() }
                }
                #if os(iOS)
                .navigationBarHidden(true)
                #endif
                .onAppear {
                    fetchDiaries()
                    // [Safety Net] Force re-fetch after short delay to catch fast syncs
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                        fetchDiaries()
                    }
                }
                .onChangeCompat(of: currentDate) { _ in fetchDiaries() }
                .onChangeCompat(of: dataManager.diaries) { _ in fetchDiaries() } // ✅ Auto Refresh on Sync
                // [Fix] Listen for Explicit Sync Notification
                .onReceive(NotificationCenter.default.publisher(for: NSNotification.Name("RefreshDiaries"))) { _ in
                    fetchDiaries()
                }
                .alert(isPresented: $showErrorAlert) {
                    Alert(title: Text("알림"), message: Text(errorMessage ?? "알 수 없는 오류가 발생했습니다."), dismissButton: .default(Text("확인")))
                }
                .sheet(item: $writeTarget) { target in
                     // [Focus Fix] wrapper View로 감싸서 MoodCalendarView.body 재평가 시
                     // sheet content가 재생성되지 않도록 함
                     // 기존: 매번 새 Binding 인스턴스 생성 → SwiftUI가 prop 변경으로 판단 → 재생성
                     // 수정: wrapper가 @State로 내부 관리 → 안정적인 identity 유지
                     DiaryWriteSheetContent(
                         targetDate: target.date,
                         onDismiss: { writeTarget = nil },
                         onSave: fetchDiaries
                     )
                }
                .sheet(isPresented: $showSettings) {
                    NavigationView {
                        AppSettingsView()
                            .environmentObject(authManager)
                            .navigationBarItems(trailing: Button("닫기") {
                                showSettings = false
                            })
                    }
                }
                // [Step 4] Nudge → Paywall Sheet
                .sheet(isPresented: $showPremiumFromNudge) {
                    MindBridgePaywallView(isPresented: $showPremiumFromNudge)
                }
            }
            
            
            // Modal Removed

        }
        .contentShape(Rectangle()) // ✅ 전체 영역 터치 가능하게 설정
        .highPriorityGesture( // ✅ 버튼보다 스와이프 우선 인식하되,
            // [UX Fix] 일기 상세 보기 중에는 스와이프 비활성화 (minimumDistance를 극대화)
            DragGesture(minimumDistance: showDetail ? 10000 : 30, coordinateSpace: .local)
                .onEnded { value in
                    guard !showDetail else { return } // 이중 안전장치
                    if value.translation.width < 0 {
                        // 왼쪽으로 스와이프 -> 다음 달
                        changeMonth(by: 1)
                    } else if value.translation.width > 0 {
                        // 오른쪽으로 스와이프 -> 이전 달
                        changeMonth(by: -1)
                    }
                }
        )
    }
    
    // MARK: - Soft Nudge Logic
    
    /// 소프트 넛지 표시 조건: 일기 7개 이상 + 구독/B2G 미가입 + 오늘 닫지 않음
    private var shouldShowNudge: Bool {
        // 1. 이미 프리미엄 접근 가능하면 표시하지 않음
        if SubscriptionManager.shared.hasMindBridgeAccess { return false }
        
        // 2. 일기가 7개 미만이면 아직 이름
        if diaries.count < 7 { return false }
        
        // 3. 오늘 이미 닫았으면 표시하지 않음
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        let today = formatter.string(from: Date())
        if UserDefaults.standard.string(forKey: "nudge_dismissed_date") == today { return false }
        
        return true
    }
    
    // MARK: - Logic
    
    // Logic Removed

    func parseAI(_ text: String?) -> (String, String) {
        guard var raw = text?.trimmingCharacters(in: .whitespacesAndNewlines), !raw.isEmpty else { return ("", "") }
        
        // 1. Remove wrapping quotes (' or ")
        if (raw.hasPrefix("'") && raw.hasSuffix("'")) || (raw.hasPrefix("\"") && raw.hasSuffix("\"")) {
            raw = String(raw.dropFirst().dropLast())
        }
        
        var label = ""
        var percent = ""
        
        // 2. Extract Label and Percent (Flexible)
        if let openParen = raw.lastIndex(of: "("), let closeParen = raw.lastIndex(of: ")"), openParen < closeParen {
            label = String(raw[..<openParen]).trimmingCharacters(in: .whitespaces)
            percent = String(raw[openParen...closeParen])
        } else {
            label = raw.trimmingCharacters(in: .whitespaces)
        }

        // 3. Korean Translation Map (Normalized)
        let emotionTranslation: [String: String] = [
            "Happy": "행복",
            "Sad": "슬픔",
            "Angry": "분노",
            "Fear": "두려움",
            "Surprise": "놀람",
            "Neutral": "평온",
            "Disgust": "혐오",
            "Anxiety": "불안",
            "Depression": "우울",
            "Stress": "스트레스",
            "Joy": "기쁨",
            "Love": "사랑",
            "Confusion": "혼란",
            "Excitement": "흥분",
            "Tired": "지침"
        ]
        
        // 4. Normalize key (First letter Upper, rest lower) to match map keys
        let normalizedKey = label.prefix(1).uppercased() + label.dropFirst().lowercased()
        
        let translatedLabel = emotionTranslation[normalizedKey] ?? emotionTranslation[label] ?? label
        
        // Percent validation
        if !percent.isEmpty && !percent.contains("%") {
             percent = ""
        }
        
        return (translatedLabel, percent)
    }

    func handleDateTap(_ date: Date, diary: Diary?) {
        if let diary = diary {
            // 이미 일기가 있으면 상세 보기
            self.selectedDiary = diary
            self.showDetail = true
        } else {
            // [OOM Prevention] AI 모델 로딩 전 진입 차단
            if !LLMService.shared.isModelLoaded {
                self.errorMessage = "AI 모델을 폰으로 모셔오는 중이에요.\n잠시만 기다려주세요! (약 5초)"
                self.showErrorAlert = true
                return
            }
            
            // 일기가 없으면 작성 모달 (데이터를 먼저 담고 시트 오픈)
            self.writeTarget = WriteTargetDate(date: date)
        }
    }
    
    func fetchDiaries() {
        LocalDataManager.shared.fetchDiaries { list in
            var newMap: [String: Diary] = [:]
            for item in list {
                // [Fix] 날짜 매핑 시 created_at(작성시점) 대신 date(일기날짜)를 우선 사용
                if let dateStr = item.date, !dateStr.isEmpty {
                    let dateKey = String(dateStr.prefix(10))
                    newMap[dateKey] = item
                } else if let dStr = item.created_at {
                    let dateKey = String(dStr.prefix(10))
                    newMap[dateKey] = item
                }
            }
            DispatchQueue.main.async {
                self.isLoading = false
                self.diaries = newMap
            }
        }
    }
    
    // [New] Clean Async Wrapper for Refreshable
    func refreshData() async {
        return await withCheckedContinuation { continuation in
            LocalDataManager.shared.syncWithServer()
            // Wait for sync notification or just delay slightly to let sync trigger update
            // Ideally we wait for callback, but syncWithServer is void.
            // Let's just wait 1.5s for UX.
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                continuation.resume()
            }
        }
    }
    
    // Helpers
    func changeMonth(by value: Int) {
        if let newDate = Calendar.current.date(byAdding: .month, value: value, to: currentDate) {
            slideDirection = value > 0 ? .trailing : .leading // [Fix] Direction logic was reversed or confusing?
            // Actually, if value > 0 (Next Month), we are moving to future.
            // But slide animation usually implies: Next comes from Right.
            
            withAnimation(.easeInOut(duration: 0.3)) {
                currentDate = newDate
            }
            
            // [Auto-Sync] 달 변경 시에도 데이터 동기화 시도 (혹시 해당 월 데이터가 없을 수 있으므로)
            // 너무 잦은 요청 방지를 위해 약간의 딜레이나 조건이 필요할 수 있으나,
            // 현재 구조상 '서버 전체 데이터'를 가져오므로 한 번만 호출하면 됨.
            // 하지만 사용자가 오랫동안 켜놓았을 수 있으므로 안전하게 호출.
            DispatchQueue.global().async {
                LocalDataManager.shared.syncWithServer()
            }
        }
    }
    func calendarDays() -> [CalendarDay] {
        let cal = Calendar.current
        let components = cal.dateComponents([.year, .month], from: currentDate)
        let firstDay = cal.date(from: components)!
        let range = cal.range(of: .day, in: .month, for: firstDay)!
        let firstWeekday = cal.component(.weekday, from: firstDay) - 1
        
        var days: [CalendarDay] = []
        
        // 빈 칸 (이전 달)
        for _ in 0..<firstWeekday {
            days.append(CalendarDay(date: nil))
        }
        
        // 이번 달 날짜들
        for day in 1...range.count {
            if let date = cal.date(byAdding: .day, value: day-1, to: firstDay) {
                days.append(CalendarDay(date: date))
            }
        }
        return days
    }
    func monthYearString(_ d: Date) -> String { let f = DateFormatter(); f.dateFormat = "YYYY년 M월"; return f.string(from: d) }
    func dateString(_ d: Date) -> String { let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"; return f.string(from: d) }
    func moodEmoji(_ l: Int) -> String { ["", "매우나쁨", "나쁨", "보통", "좋음", "매우좋음"][l] }
    func moodColor(_ l: Int) -> Color { [Color.clear, .mood1, .mood2, .mood3, .mood4, .mood5][l] }
    
    /// AI 감정 분석 기반 배경색 (☕ Warm Journal 어스톤 파스텔)
    func emotionBackgroundColor(for diary: Diary) -> Color {
        let emotion = (diary.ai_prediction ?? diary.ai_comment ?? "").lowercased()
        
        if emotion.contains("행복") || emotion.contains("기쁨") || emotion.contains("즐거") || emotion.contains("사랑") {
            return Color.mood5.opacity(0.18) // 피치 코랄
        } else if emotion.contains("평온") || emotion.contains("편안") || emotion.contains("안정") || emotion.contains("감사") {
            return Color.mood4.opacity(0.18) // 세이지 그린
        } else if emotion.contains("보통") || emotion.contains("무난") || emotion.contains("그저") {
            return Color.mood3.opacity(0.20) // 샌드
        } else if emotion.contains("우울") || emotion.contains("슬") || emotion.contains("외로") {
            return Color.mood2.opacity(0.18) // 뮤트 블루
        } else if emotion.contains("화") || emotion.contains("짜증") || emotion.contains("분노") || emotion.contains("스트레스") {
            return Color.mood1.opacity(0.18) // 더스티 로즈
        } else if emotion.contains("불안") || emotion.contains("걱정") || emotion.contains("긴장") || emotion.contains("두려움") {
            return Color.mood2.opacity(0.15) // 뮤트 블루 (연하게)
        } else if emotion.contains("뿌듯") || emotion.contains("성취") || emotion.contains("흥분") {
            return Color.mood5.opacity(0.15) // 피치 코랄 (연하게)
        } else {
            // AI 감정 없으면 mood_level 기반 폴백
            switch diary.mood_level {
            case 5: return Color.mood5.opacity(0.15)
            case 4: return Color.mood4.opacity(0.15)
            case 3: return Color.mood3.opacity(0.15)
            case 2: return Color.mood2.opacity(0.15)
            case 1: return Color.mood1.opacity(0.15)
            default: return Color.softTan.opacity(0.3)
            }
        }
    }
    
    // [AI Logic] Convert AI Label to Mood Asset
    func getAIAsset(for prediction: String?) -> MoodAsset? {
        let (label, _) = parseAI(prediction)
        if label.isEmpty { return nil }
        
        // Map Korean Labels to Mood Levels (1-5)
        switch label {
        case "행복", "기쁨", "사랑", "흥분": return getMoodAsset(level: 5)
        case "평온", "놀람", "감사": return getMoodAsset(level: 4)
        case "불안", "두려움", "혼란", "보통": return getMoodAsset(level: 3)
        case "슬픔", "우울", "지침", "피곤": return getMoodAsset(level: 2)
        case "분노", "스트레스", "혐오", "짜증": return getMoodAsset(level: 1)
        default: return nil // Fallback to User Selection
        }
    }
}

// MARK: - PremiumModalView Moved to PremiumModalView.swift

// MARK: - [Focus Fix] Sheet Content Wrapper
// 부모 View(MoodCalendarView)의 body가 재평가되어도,
// .sheet 내부의 AppDiaryWriteView가 재생성되지 않도록 안정적인 identity를 제공합니다.
// @State isPresented를 내부에서 관리하여 매번 새 Binding이 생성되는 문제를 해결합니다.
struct DiaryWriteSheetContent: View {
    let targetDate: Date
    let onDismiss: () -> Void
    let onSave: () -> Void
    
    @State private var isPresented = true
    
    var body: some View {
        AppDiaryWriteView(
            isPresented: $isPresented,
            date: targetDate,
            onSave: onSave
        )
        .onChangeCompat(of: isPresented) { newValue in
            if !newValue {
                onDismiss()
            }
        }
    }
}
