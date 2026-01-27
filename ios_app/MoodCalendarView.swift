
import SwiftUI

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
    @State private var showPremiumModal = false // ✅ Modal State
    
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
    
    // Write Modal State (Identifiable Item for Safe Presentation)
    @State private var writeTarget: WriteTargetDate?
    
    // ✅ Base URL
    let baseURL = "https://217.142.253.35.nip.io"
    
    let columns = Array(repeating: GridItem(.flexible()), count: 7)
    
    var body: some View {
        ZStack {
            NavigationView {
                VStack(spacing: 20) {
                    // 상단 헤더
                    HStack {
                        Button(action: { changeMonth(by: -1) }) {
                            Image(systemName: "chevron.left").font(.title2).foregroundColor(.black)
                        }
                        Spacer()
                        Text(monthYearString(currentDate)).font(.title2).fontWeight(.bold)
                        Spacer()
                        
                        // ✅ Premium Button (If Eligible)
                        if !authManager.isPremium && authManager.riskLevel < 3 {
                            Button(action: { showPremiumModal = true }) {
                                HStack(spacing: 4) {
                                    Text("✨")
                                    Text("Upgrade")
                                        .fontWeight(.bold)
                                        .font(.caption)
                                }
                                .padding(.horizontal, 12)
                                .padding(.vertical, 6)
                                .background(LinearGradient(gradient: Gradient(colors: [Color(hex: "6366F1"), Color(hex: "8B5CF6")]), startPoint: .topLeading, endPoint: .bottomTrailing))
                                .foregroundColor(.white)
                                .cornerRadius(20)
                                .shadow(radius: 2)
                            }
                            .padding(.trailing, 8)
                        }
                        
                        Button(action: { changeMonth(by: 1) }) {
                            Image(systemName: "chevron.right").font(.title2).foregroundColor(.black)
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
                    
                    // 달력 그리드
                    if isLoading {
                        Spacer(); ProgressView(); Spacer()
                    } else {
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
                                                    // 2. 사용자 선택 이모지 (이미지)
                                                    let asset = getMoodAsset(level: d.mood_level)
                                                    Image(asset.image)
                                                        .resizable()
                                                        .scaledToFit()
                                                        .frame(width: 28, height: 28)
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
                        .transition(.asymmetric(
                            insertion: .move(edge: slideDirection),
                            removal: .move(edge: slideDirection == .trailing ? .leading : .trailing)
                        ))
                        .animation(.easeInOut(duration: 0.3), value: currentDate) // Apply animation
                    }
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
                .onAppear(perform: fetchDiaries)
                .onChange(of: currentDate) { _ in fetchDiaries() }
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
                }
                // ✅ 제스처 추가: 좌우 스와이프로 월 이동
                .gesture(
                    DragGesture()
                        .onEnded { value in
                            if value.translation.width < -50 {
                                // 왼쪽으로 스와이프 -> 다음 달
                                changeMonth(by: 1)
                            } else if value.translation.width > 50 {
                                // 오른쪽으로 스와이프 -> 이전 달
                                changeMonth(by: -1)
                            }
                        }
                )
            }
            
            // ✅ Premium Modal Overlay
            if showPremiumModal {
                ZStack {
                    Color.black.opacity(0.4).edgesIgnoringSafeArea(.all)
                        .onTapGesture {
                            showPremiumModal = false
                        }
                    
                    PremiumModalView(isPresented: $showPremiumModal, onUpgrade: performUpgrade)
                }
                .zIndex(100)
            }
        }
    }
    
    // MARK: - Logic
    
    // ✅ Handle Upgrade (Local Mock)
    func performUpgrade() {
        isLoading = true
        // Simulate network delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            isLoading = false
            authManager.setPremium(true)
            showPremiumModal = false
        }
    }

    func parseAI(_ text: String?) -> (String, String) {
        guard var raw = text, !raw.isEmpty else { return ("", "") }
        
        // 1. Extract from single quotes if present (e.g., 'Happy (80%)')
        if let start = raw.firstIndex(of: "'"), let end = raw.lastIndex(of: "'"), start != end {
            raw = String(raw[raw.index(after: start)..<end])
        }
        
        // 2. Extract Label and Percent
        // Check for format "Label (N%)"
        if raw.hasSuffix(")"), let openParen = raw.lastIndex(of: "(") {
            let label = String(raw[..<openParen]).trimmingCharacters(in: .whitespaces)
            let percent = String(raw[openParen...])
            if percent.contains("%") {
                 return (label, percent)
            }
        }
        
        // Fallback: Return raw string as label if parsing fails
        return (raw, "")
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
                if let dStr = item.created_at {
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
    
    // Helpers
    func changeMonth(by value: Int) {
        slideDirection = value > 0 ? .trailing : .leading
        if let newDate = Calendar.current.date(byAdding: .month, value: value, to: currentDate) {
            withAnimation(.easeInOut(duration: 0.3)) {
                currentDate = newDate
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
}

// MARK: - Premium Modal View
struct PremiumModalView: View {
    @Binding var isPresented: Bool
    var onUpgrade: () -> Void
    @State private var showingAlert = false
    
    var body: some View {
        VStack(spacing: 24) {
            // Close Button
            HStack {
                Spacer()
                Button(action: { isPresented = false }) {
                    Image(systemName: "xmark")
                        .foregroundColor(.gray)
                        .padding(5)
                }
            }
            
            // Header
            VStack(spacing: 8) {
                Text("마음챙김 플러스 +")
                    .font(.title2)
                    .fontWeight(.bold)
                Text("더 깊은 이해와 치유를 위한 선택")
                    .font(.subheadline)
                    .foregroundColor(.gray)
            }
            
            // Features
            VStack(alignment: .leading, spacing: 16) {
                FeatureRow(icon: "chart.bar.fill", title: "심층 분석 리포트", desc: "나의 감정 패턴과 원인을 깊이 있게 분석해드려요.")
                FeatureRow(icon: "message.fill", title: "AI 심리 상담사", desc: "24시간 언제든 내 마음을 털어놓고 위로받으세요.")
                FeatureRow(icon: "calendar", title: "월간 감정 통계", desc: "한 달간의 감정 변화를 그래프로 확인하세요.")
            }
            .padding(.vertical)
            
            // ✅ Dobong-gu Notice (Green Box)
            HStack(alignment: .top, spacing: 10) {
                Text("🏥")
                VStack(alignment: .leading, spacing: 4) {
                    Text("도봉구청 상담 안내")
                        .font(.system(size: 14, weight: .bold))
                        .foregroundColor(Color(hex: "15803d"))
                    Text("도봉구청에서 상담을 받으면 무료 업그레이드가 가능합니다.")
                        .font(.system(size: 13))
                        .foregroundColor(Color(hex: "15803d"))
                        .fixedSize(horizontal: false, vertical: true)
                }
                Spacer()
            }
            .padding(15)
            .background(Color(hex: "f0fdf4"))
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(Color(hex: "dcfce7"), lineWidth: 1)
            )
            
            // Price
            HStack(alignment: .lastTextBaseline, spacing: 8) {
                Text("₩9,900")
                    .font(.callout)
                    .strikethrough()
                    .foregroundColor(.gray)
                
                Text("₩4,900")
                    .font(.title)
                    .fontWeight(.bold)
                    .foregroundColor(.primary)
                
                Text("/월")
                    .font(.caption)
                    .foregroundColor(.gray)
                
                Text("런칭 특가 50%")
                    .font(.caption)
                    .fontWeight(.bold)
                    .padding(4)
                    .background(Color.red.opacity(0.1))
                    .foregroundColor(.red)
                    .cornerRadius(4)
            }
            
            Button(action: { showingAlert = true }) {
                Text("지금 시작하기")
                    .fontWeight(.bold)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(14)
            }
            .alert(isPresented: $showingAlert) {
                Alert(
                    title: Text("결제 확인"),
                    message: Text("4,900원을 결제하시겠습니까? (테스트)"),
                    primaryButton: .default(Text("결제하기"), action: onUpgrade),
                    secondaryButton: .cancel()
                )
            }
            
            Text("언제든 해지 가능합니다.")
                .font(.caption)
                .foregroundColor(.gray)
        }
        .padding(24)
        .background(Color.white)
        .cornerRadius(24)
        .shadow(radius: 20)
        .padding(20)
    }
}

struct FeatureRow: View {
    let icon: String
    let title: String
    let desc: String
    
    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 20))
                .foregroundColor(.black)
                .frame(width: 40, height: 40)
                .background(Color(hex: "F5F5F7"))
                .cornerRadius(10)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.bold)
                Text(desc)
                    .font(.caption)
                    .foregroundColor(.gray)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }
}
