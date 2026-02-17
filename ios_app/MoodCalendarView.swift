
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
                                    .foregroundColor(.black)
                            }
                            
                            Text(monthYearString(currentDate))
                                .font(.title2)
                                .fontWeight(.bold)
                                .foregroundColor(.primary)
                            
                            Button(action: { changeMonth(by: 1) }) {
                                Image(systemName: "chevron.right")
                                    .font(.title2)
                                    .foregroundColor(.black)
                            }
                        }
                        
                        // 2. Trailing Group: [ Hamburger ]
                        HStack {
                            Spacer()
                            Button(action: { showSettings = true }) {
                                Image(systemName: "line.3.horizontal") // 햄버거 메뉴
                                    .font(.title2)
                                    .fontWeight(.semibold)
                                    .foregroundColor(.black)
                            }
                        }
                    }
                    .padding(.horizontal)
                    .padding(.top, 20)
                    
                    // 요일 헤더
                    HStack {
                        ForEach(["일", "월", "화", "수", "목", "금", "토"], id: \.self) { day in
                            Text(day).font(.caption).fontWeight(.bold).foregroundColor(.gray).frame(maxWidth: .infinity)
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
                                            // 1. 날짜
                                            Text("\(Calendar.current.component(.day, from: date))")
                                                .font(.system(size: 10, weight: diary != nil ? .bold : .regular)) // 날짜 크기 축소
                                                .foregroundColor(Calendar.current.isDateInToday(date) ? .blue : .primary)
                                                .padding(.top, 4)
                                            
                                            if let d = diary {
                                                VStack(spacing: 0) {
                                                    // 2. 감정 이모지 (AI 우선 적용)
                                                    let aiAsset = getAIAsset(for: d.ai_prediction)
                                                    let asset = aiAsset ?? getMoodAsset(level: d.mood_level)
                                                    
                                                    ZStack(alignment: .bottomTrailing) {
                                                        Image(asset.image)
                                                            .resizable()
                                                            .scaledToFit()
                                                            .frame(width: 28, height: 28)
                                                        
                                                        // [New] 약물 복용 표시 💊
                                                        if d.medication == true {
                                                            Image(systemName: "pills.fill")
                                                                .font(.system(size: 10))
                                                                .foregroundColor(.green)
                                                                .background(Circle().fill(Color.white).frame(width: 12, height: 12))
                                                                .offset(x: 4, y: 2)
                                                        }
                                                    }
                                                    .padding(.bottom, 2)
                                                    
                                                    // 3 & 4. AI 예측 (감정 + 퍼센트)
                                                    let (label, percent) = parseAI(d.ai_prediction)
                                                    if !label.isEmpty {
                                                        Text(label)
                                                            .font(.system(size: 8, weight: .bold)) // 텍스트 크기 축소
                                                            .foregroundColor(.primary)
                                                            .lineLimit(1)
                                                            .minimumScaleFactor(0.7)
                                                        
                                                        if !percent.isEmpty {
                                                            Text(percent)
                                                                .font(.system(size: 7))
                                                                .foregroundColor(.secondary)
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
                                            RoundedRectangle(cornerRadius: 8)
                                                .fill(diary != nil ? getMoodAsset(level: diary!.mood_level).color.opacity(0.15) : Color.clear)
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
                        print("🔄 [UI] Pull-to-Refresh Triggered")
                        await refreshData()
                    }
                    
                    // [New] Bottom Manual Sync Button
                    Button(action: {
                        print("🔄 [UI] Manual Sync Triggered (Bottom)")
                        self.isLoading = true
                        LocalDataManager.shared.syncWithServer()
                        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                            self.isLoading = false
                        }
                    }) {
                        HStack {
                            Image(systemName: "arrow.clockwise")
                            Text("데이터 새로고침")
                        }
                        .font(.caption)
                        .foregroundColor(.gray)
                        .padding(8)
                        .background(Color.gray.opacity(0.1))
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
                    print("🔔 [Calendar] Received Refresh Signal. Updating UI...")
                    fetchDiaries()
                }
                .alert(isPresented: $showErrorAlert) {
                    Alert(title: Text("알림"), message: Text(errorMessage ?? "알 수 없는 오류가 발생했습니다."), dismissButton: .default(Text("확인")))
                }
                .sheet(item: $writeTarget) { target in
                     // 바인딩 전달을 위한 래퍼
                     AppDiaryWriteView(
                        isPresented: Binding(
                            get: { writeTarget != nil },
                            set: { if !$0 { writeTarget = nil } }
                        ),
                        date: target.date,
                        onSave: fetchDiaries
                     )
                     .screenshotProtected(isProtected: true) // 스크린샷 방지
                }
                .sheet(isPresented: $showSettings) {
                    NavigationView {
                        AppSettingsView()
                            .navigationBarItems(trailing: Button("닫기") {
                                showSettings = false
                            })
                    }
                    .screenshotProtected(isProtected: true) // 스크린샷 방지
                }
            }
            
            
            // Modal Removed

        }
        .contentShape(Rectangle()) // ✅ 전체 영역 터치 가능하게 설정
        .highPriorityGesture( // ✅ 버튼보다 스와이프 우선 인식하되,
            DragGesture(minimumDistance: 30, coordinateSpace: .local) // ⭐️ 30pt 이상 움직여야만 드래그로 인식 (단순 터치는 통과)
                .onEnded { value in
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
    func moodEmoji(_ l: Int) -> String { ["", "😠", "😢", "😐", "😌", "😊"][l] }
    func moodColor(_ l: Int) -> Color { [Color.clear, .red, .blue, .gray, .green, .yellow][l] }
    
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
