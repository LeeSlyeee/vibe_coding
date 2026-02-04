
import SwiftUI
import Charts

// MARK: - Data Models
// (Moved to StatsModels.swift)


// MARK: - Design System
// MARK: - Design System
// (Moved to ViewExtensions.swift)

// MARK: - Main View
struct AppStatsView: View {
    @EnvironmentObject var authManager: AuthManager
    @ObservedObject var b2gManager = B2GManager.shared // B2G 연동 상태 관찰
    @State private var currentTab = "flow"
    @State private var stats: StatisticsResponse?
    @State private var isLoading = true
    
    @State private var isGeneratingReport = false
    @State private var reportContent: String = ""
    @State private var isGeneratingLongTerm = false

    @State private var longTermContent: String = ""
    
    // [New] B2G Connection UI State
    @State private var showingConnectAlert = false
    @State private var inputCode = ""
    @State private var connectMessage = ""
    @State private var showingResultAlert = false
    
    // [New] Settings Modal State
    @State private var showSettings = false
    
    let baseURL = "http://150.230.7.76"
    
    let tabs = [
        ("flow", "흐름"),
        ("monthly", "월별"),
        ("mood", "분포"),
        ("weather", "날씨"),
        ("report", "AI분석")
    ]
    
    var body: some View {
        ZStack {
            Color.bgMain.edgesIgnoringSafeArea(.all) // 배경만 전체 채움
            
            // [B2G] 무조건 연동해야만 통계 해금
            if !b2gManager.isLinked {
                VStack(spacing: 24) {
                    Spacer()
                    Image(systemName: "lock.shield.fill")
                        .font(.system(size: 80))
                        .foregroundColor(authManager.riskLevel >= 2 ? .red.opacity(0.6) : .gray.opacity(0.5))
                    
                    VStack(spacing: 8) {
                        Text("전문 분석 기능 잠김")
                            .font(.title2)
                            .fontWeight(.bold)
                            .foregroundColor(.primary)
                        
                        if authManager.riskLevel >= 2 {
                            // 중증(위험) 사용자용 메시지
                            Text("⚠️ 주의가 필요한 상태입니다.\n전문가의 도움을 받기 위해\n보건소/상담센터와 연동해주세요.")
                                .multilineTextAlignment(.center)
                                .foregroundColor(.red)
                                .fontWeight(.semibold)
                        } else {
                            // 경증(일반) 사용자용 메시지
                            Text("보건소/상담센터와 연동하시면\n심층 통계 분석 기능을 이용하실 수 있습니다.")
                                .multilineTextAlignment(.center)
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    Text("설정 > 기관 연동(B2G) 메뉴에서도\n언제든 연동할 수 있습니다.")
                        .font(.caption)
                        .foregroundColor(.gray)
                        .multilineTextAlignment(.center)
                        .padding(.top, 10)
                    
                    // [New] Direct Connect Button
                    Button(action: { showingConnectAlert = true }) {
                        Text("지금 연동하기")
                            .fontWeight(.bold)
                            .foregroundColor(.white)
                            .padding(.vertical, 12)
                            .padding(.horizontal, 24)
                            .background(Color.blue)
                            .cornerRadius(12)
                            .shadow(radius: 3)
                    }
                    .padding(.top, 20)
                    .alert("기관 코드 입력", isPresented: $showingConnectAlert) {
                        TextField("코드 (예: CENTER001)", text: $inputCode)
                        Button("취소", role: .cancel) { }
                        Button("연동") {
                            connectToCenter()
                        }
                    } message: {
                        Text("보건소나 상담센터에서 발급받은\n코드를 입력해주세요.")
                    }
                        
                    Spacer()
                }
                .padding()
            } else {
                // Full Feature for Severe (Level 2+) Users
                VStack(spacing: 0) {
                    // Header
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("마음 분석")
                            .font(.system(size: 28, weight: .bold))
                            .foregroundColor(.primaryText)
                        Text("데이터로 보는 나의 하루")
                            .font(.subheadline)
                            .foregroundColor(.secondaryText)
                    }
                    Spacer()
                    
                    // [New] Settings Button
                    Button(action: { showSettings = true }) {
                        Image(systemName: "gearshape.fill")
                            .font(.title2)
                            .foregroundColor(.primaryText)
                            .padding(8)
                            .background(Color.white)
                            .clipShape(Circle())
                            .shadow(color: Color.black.opacity(0.1), radius: 2)
                    }
                }
                .padding(.horizontal, 24)
                .padding(.top, 20)
                .padding(.bottom, 20)
                .background(Color.white.opacity(0.8))
                
                // Modern Tab Bar
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(tabs, id: \.0) { tab in
                            Button(action: { 
                                withAnimation(.spring()) { currentTab = tab.0 }
                            }) {
                                Text(tab.1)
                                    .font(.system(size: 15, weight: .semibold))
                                    .padding(.vertical, 10)
                                    .padding(.horizontal, 18)
                                    .background(currentTab == tab.0 ? Color.accent : Color.white)
                                    .foregroundColor(currentTab == tab.0 ? .white : .secondaryText)
                                    .cornerRadius(20)
                                    .shadow(color: currentTab == tab.0 ? Color.accent.opacity(0.3) : Color.black.opacity(0.05), radius: 5, x: 0, y: 2)
                            }
                        }
                    }
                    .padding(.horizontal, 24)
                    .padding(.bottom, 15)
                }
                
                // Content
                if isLoading {
                    Spacer()
                    ProgressView().scaleEffect(1.2)
                    Spacer()
                } else if let stats = stats {
                    ScrollView(showsIndicators: false) {
                        VStack(spacing: 24) {
                            switch currentTab {
                            case "flow": FlowChartView(data: stats.timeline ?? [])
                            case "monthly": MonthlyChartView(data: stats.daily ?? [])
                            case "mood": MoodDistributionView(data: stats.moods ?? [])
                            case "weather": WeatherStatsView(data: stats.weather ?? [])
                            case "report": ReportView(
                                isGenerating: $isGeneratingReport,
                                content: $reportContent,
                                isGeneratingLong: $isGeneratingLongTerm,
                                longContent: $longTermContent,
                                startReport: startReport,
                                startLongTerm: startLongTermReport
                            )
                            default: EmptyView()
                            }
                        }
                        .padding(.horizontal, 24)
                        .padding(.top, 10)
                        .padding(.bottom, 100)
                    }
                }
            }
        } // End of Else (Full Features)
    }
    .onAppear {
            // 연동 상태라면 데이터 로딩 (위험도 상관없음)
            if b2gManager.isLinked {
                fetchStats()
                fetchExistingReports()
            }
        }
        // 연동 상태가 바뀌면 즉시 감지하여 데이터 로드
        .onChangeCompat(of: b2gManager.isLinked) { linked in
            if linked {
                fetchStats()
                fetchExistingReports()
            }
        }
        .alert(isPresented: $showingResultAlert) {
            Alert(title: Text("알림"), message: Text(connectMessage), dismissButton: .default(Text("확인")))
        }
        .sheet(isPresented: $showSettings) {
            NavigationView {
                AppSettingsView()
                    .navigationBarItems(trailing: Button("닫기") {
                        showSettings = false
                    })
            }
        }
        .preferredColorScheme(.light) // ⭐️ 화이트 테마 강제
    }
    
    // [New] Connect Helper
    func connectToCenter() {
        b2gManager.connect(code: inputCode) { success, msg in
            self.connectMessage = msg
            self.showingResultAlert = true
        }
    }
    
    // Local Data Logic
    func fetchStats() {
        // 로컬 데이터 로딩 시뮬레이션 (빠름)
        DispatchQueue.main.async {
            let diaries = LocalDataManager.shared.diaries
            
            // 1. Timeline Data
            let timeline = diaries.map { diary in
                StatsTimelineItem(
                    date: diary.date ?? "",
                    mood_level: diary.mood_level,
                    ai_label: nil
                )
            }.sorted { $0.date < $1.date } // 날짜 오름차순
            
            // 2. Daily (Monthly) Data - 사실상 일별 빈도수인데, 여기선 일기 개수를 무드로 표현하는 로직이 있었나봄.
            // 기존 MonthlyChartView 로직: _id가 "YYYY-MM-DD", count가 무드? 아니면 개수?
            // "BarMark(y: .value("Mood", item.count))" 코드를 보면 item.count가 Y축(높이)임.
            // 그리고 color는 `moodColor(item.count)`
            // 아하, 기존 로직은 "그 날의 기분 점수(count?)"를 보여주는 것 같음. 네이밍이 count라 헷갈리지만.
            // 여기선 "날짜별 평균 기분"으로 매핑.
            let daily = diaries.map { diary in
                StatsDailyItem(_id: diary.date ?? "", count: diary.mood_level)
            }
            
            // 3. Mood Distribution
            var moodCounts = [Int: Int]()
            for diary in diaries {
                moodCounts[diary.mood_level, default: 0] += 1
            }
            let moods = moodCounts.map { StatsMoodItem(_id: $0.key, count: $0.value) }
            
            // 4. Weather (날씨별 감정 통계 구현)
            // Group by weatherDesc -> moodLevel -> count
            var weatherMap = [String: [Int: Int]]()
            
            for diary in diaries {
                let w = diary.weather ?? "알 수 없음"
                if weatherMap[w] == nil { weatherMap[w] = [:] }
                weatherMap[w]![diary.mood_level, default: 0] += 1
            }
            
            let weather = weatherMap.map { (weatherDesc, moodCounts) in
                let moodItems = moodCounts.map { StatsMoodCount(mood: $0.key, count: $0.value) }
                return StatsWeatherItem(_id: weatherDesc, moods: moodItems)
            }.sorted { $0._id < $1._id }
            
            self.stats = StatisticsResponse(
                timeline: timeline,
                daily: daily,
                moods: moods,
                weather: weather
            )
            self.isLoading = false
        }
    }
    
    func fetchExistingReports() {
        // 로컬 리포트 로직 또는 보건소 연동 리포트 (추후 구현)
        // 현재는 빈 상태로 둠
        self.isGeneratingReport = false
        self.isGeneratingLongTerm = false
    }

    func startReport() { 
        isGeneratingReport = true
        // 로컬 AI 분석 시뮬레이션 (3초 후 완료)
        DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
            self.reportContent = """
            [AI 분석 리포트]
            최근 작성하신 일기를 분석해보니, 전반적으로 안정적인 기분을 유지하고 계시네요.
            특히 어제 기록하신 '편안함'이 긍정적인 영향을 주고 있습니다.
            보건소 연동이 완료되어 담당 선생님도 님의 상태를 파악하고 계시니 안심하세요.
            """
            self.isGeneratingReport = false
        }
    }
    
    func startLongTermReport() { 
        isGeneratingLongTerm = true
        // 로컬 장기 분석 시뮬레이션
        DispatchQueue.main.asyncAfter(deadline: .now() + 4.0) {
            self.longTermContent = """
            [장기 패턴 분석]
            지난 2주간의 감정 흐름을 보면, 월요일마다 다소 스트레스가 높아지는 경향이 있습니다.
            하지만 주말로 갈수록 회복탄력성이 높게 나타나고 있어요.
            규칙적인 수면 패턴이 큰 도움이 되고 있는 것으로 보입니다.
            """
            self.isGeneratingLongTerm = false
        }
    }
    
    // pollStatus는 더 이상 필요 없음
    func apiCall(path: String, method: String, completion: @escaping (Data?) -> Void) {
        guard let token = UserDefaults.standard.string(forKey: "authToken") else { return }
        guard let url = URL(string: "\(baseURL)\(path)") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        URLSession.shared.dataTask(with: request) { d, _, _ in completion(d) }.resume()
    }
}

// MARK: - Reusable Card Style
struct CardModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(24)
            .background(Color.cardBg)
            .cornerRadius(24)
            .shadow(color: Color.black.opacity(0.06), radius: 15, x: 0, y: 5)
    }
}

// MARK: - Charts with Improved Design
struct FlowChartView: View {
    let data: [StatsTimelineItem]
    
    var contentWidth: CGFloat {
        let screenWidth = UIScreen.main.bounds.width - 48 // 좌우 패딩 고려
        let minWidth: CGFloat = screenWidth
        let itemWidth: CGFloat = 100 // 아이템 폭 대폭 증가 (스크롤 확실시)
        let computedWidth = CGFloat(data.count) * itemWidth
        return max(minWidth, computedWidth)
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "chart.xyaxis.line").foregroundColor(.accent)
                Text("감정 흐름").font(.title3).fontWeight(.bold).foregroundColor(.primaryText)
            }
            if #available(iOS 16.0, *) {
                ScrollView(.horizontal, showsIndicators: false) {
                    Chart {
                        ForEach(data) { item in
                            LineMark(x: .value("Date", String(item.date.suffix(5))), y: .value("Mood", item.mood_level))
                                .interpolationMethod(.catmullRom)
                                .lineStyle(StrokeStyle(lineWidth: 3))
                                .symbol { Circle().fill(moodColor(item.mood_level)).frame(width: 8) }
                            
                            AreaMark(x: .value("Date", String(item.date.suffix(5))), y: .value("Mood", item.mood_level))
                                .interpolationMethod(.catmullRom)
                                .foregroundStyle(LinearGradient(colors: [moodColor(3).opacity(0.2), .clear], startPoint: .top, endPoint: .bottom))
                        }
                    }
                    .chartYScale(domain: 0...6)
                    .chartYAxis { AxisMarks(values: [1,3,5]) { v in AxisValueLabel(moodEmoji(v.as(Int.self) ?? 0)) } }
                    .frame(width: contentWidth, height: 280)
                    .contentShape(Rectangle()) // ✅ 터치 영역 확보
                }
            } else { Text("iOS 16+ 필요") }
        }
        .modifier(CardModifier())
    }
    func moodEmoji(_ l: Int) -> String { ["", "🤬", "😢", "😐", "😌", "🥰"][l] }
    func moodColor(_ l: Int) -> Color { [Color.gray, .mood1, .mood2, .mood3, .mood4, .mood5][min(l, 5)] }
}

struct MonthlyChartView: View {
    let data: [StatsDailyItem]
    
    var monthlyGroups: [(String, [StatsDailyItem])] {
        let grouped = Dictionary(grouping: data) { String($0._id.prefix(7)) }
        return grouped.sorted { $0.key > $1.key }
    }
    
    var body: some View {
        VStack(spacing: 24) {
            ForEach(monthlyGroups, id: \.0) { month, items in
                VStack(alignment: .leading, spacing: 16) {
                    HStack {
                        Image(systemName: "calendar").foregroundColor(.accent)
                        Text(formatMonthHeader(month)).font(.title3).fontWeight(.bold).foregroundColor(.primaryText)
                    }
                    if #available(iOS 16.0, *) {
                        Chart {
                            ForEach(items.sorted(by: { $0._id < $1._id }), id: \._id) { item in
                                BarMark(
                                    x: .value("Day", String(item._id.suffix(2))), // Show day "01", "02"
                                    y: .value("Mood", item.count)
                                )
                                .foregroundStyle(moodColor(item.count))
                                .cornerRadius(4)
                            }
                        }
                        .chartYScale(domain: 0...6)
                        .chartYAxis { AxisMarks(values: [1,3,5]) }
                        .frame(height: 200)
                    } else {
                        Text("iOS 16 이상 버전이 필요합니다.")
                    }
                }
                .modifier(CardModifier())
            }
        }
    }
    
    func formatMonthHeader(_ yyyymm: String) -> String {
        let parts = yyyymm.split(separator: "-")
        if parts.count == 2 { return "\(parts[0])년 \(parts[1])월" }
        return yyyymm
    }
    
    func moodColor(_ l: Int) -> Color { [Color.gray, .mood1, .mood2, .mood3, .mood4, .mood5][min(l, 5)] }
}

struct MoodDistributionView: View {
    let data: [StatsMoodItem]
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            HStack {
                Image(systemName: "paintpalette.fill").foregroundColor(.accent)
                Text("감정 비중").font(.title3).fontWeight(.bold).foregroundColor(.primaryText)
            }
            HStack {
                ZStack {
                    ForEach(calculateSegments(data: data), id: \.id) { seg in
                        Circle().trim(from: seg.start, to: seg.end)
                            .stroke(seg.color, style: StrokeStyle(lineWidth: 25, lineCap: .round))
                            .rotationEffect(.degrees(-90))
                    }
                    VStack {
                        Text("\(totalCount(data))").font(.title).fontWeight(.bold)
                        Text("TOTAL").font(.caption).foregroundColor(.secondaryText)
                    }
                }
                .frame(width: 140, height: 140).padding(.trailing, 20)
                
                VStack(alignment: .leading, spacing: 10) {
                    ForEach(data.sorted(by: { $0._id > $1._id }), id: \._id) { item in
                        HStack {
                            Circle().fill(moodColor(item._id)).frame(width: 8, height: 8)
                            Text(moodLabel(item._id)).font(.system(size: 14))
                            Spacer()
                            Text("\(item.count)").fontWeight(.bold).foregroundColor(.secondaryText)
                        }
                    }
                }
            }
        }
        .modifier(CardModifier())
    }
    struct Segment: Identifiable { let id = UUID(); let start: CGFloat; let end: CGFloat; let color: Color }
    func calculateSegments(data: [StatsMoodItem]) -> [Segment] {
        let total = Double(totalCount(data)); var start: CGFloat = 0; var segments: [Segment] = []
        for item in data { let ratio = Double(item.count) / max(total, 1); let end = start + CGFloat(ratio); segments.append(Segment(start: start, end: end, color: moodColor(item._id))); start = end }
        return segments
    }
    func totalCount(_ data: [StatsMoodItem]) -> Int { data.reduce(0) { $0 + $1.count } }
    func moodColor(_ l: Int) -> Color { [Color.gray, .mood1, .mood2, .mood3, .mood4, .mood5][min(l, 5)] }
    func moodLabel(_ l: Int) -> String { ["", "화남", "우울", "보통", "편안", "행복"][min(l, 5)] }
}

struct WeatherStatsView: View {
    let data: [StatsWeatherItem]
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Image(systemName: "cloud.sun.fill").foregroundColor(.accent)
                Text("날씨와 기분").font(.title3).fontWeight(.bold).foregroundColor(.primaryText)
            }
            if #available(iOS 16.0, *) {
                Chart {
                    ForEach(data) { wItem in
                        ForEach(wItem.moods ?? [], id: \.self) { mCount in
                            BarMark(x: .value("Weather", wItem._id), y: .value("Count", mCount.count))
                                .foregroundStyle(moodColor(mCount.mood))
                        }
                    }
                }
                .frame(height: 280)
            }
        }
        .modifier(CardModifier())
    }
    func moodColor(_ l: Int) -> Color { [Color.gray, .mood1, .mood2, .mood3, .mood4, .mood5][min(l, 5)] }
}

struct ReportView: View {
    @Binding var isGenerating: Bool
    @Binding var content: String
    @Binding var isGeneratingLong: Bool
    @Binding var longContent: String
    var startReport: () -> Void; var startLongTerm: () -> Void
    
    var body: some View {
        VStack(spacing: 20) {
            HStack {
                Image(systemName: "wand.and.stars").font(.title2).foregroundColor(.purple)
                Text("AI 심층 리포트").font(.title3).fontWeight(.bold)
                Spacer()
            }
            
            if content.isEmpty && !isGenerating {
                Button(action: startReport) {
                    HStack { Text("✨ 지금 바로 분석 시작하기"); Image(systemName: "arrow.right") }
                        .fontWeight(.bold).foregroundColor(.white).padding().frame(maxWidth: .infinity)
                        .background(LinearGradient(colors: [.purple, .blue], startPoint: .leading, endPoint: .trailing))
                        .cornerRadius(16)
                        .shadow(color: .purple.opacity(0.3), radius: 10, x: 0, y: 5)
                }
            } else if isGenerating {
                VStack(spacing: 15) {
                    ProgressView()
                    Text("AI가 일기장을 읽고 있어요...").font(.subheadline).foregroundColor(.secondaryText)
                }.frame(height: 150)
            } else {
                VStack(alignment: .leading, spacing: 10) {
                    HStack { Text("💬 3줄 요약").font(.headline); Spacer() }
                    Text(content).lineSpacing(4).font(.system(size: 15)).foregroundColor(.primaryText)
                }
                .padding(20).background(Color(hexString: "F8F9FE")).cornerRadius(16)
                
                if longContent.isEmpty && !isGeneratingLong {
                    Button(action: startLongTerm) {
                        Text("🧠 장기 기억 패턴 분석하기").fontWeight(.semibold).foregroundColor(.white).padding()
                            .frame(maxWidth: .infinity).background(Color.green).cornerRadius(16)
                    }
                } else if isGeneratingLong {
                    ProgressView("장기 패턴 분석 중...")
                } else {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("🧠 메타 분석").font(.headline).foregroundColor(.green)
                        Text(longContent).lineSpacing(4).font(.system(size: 15)).foregroundColor(.primaryText)
                    }.padding(20).background(Color(hexString: "F0FDF4")).cornerRadius(16)
                }
                Button("🔄 다시 분석") { startReport() }.font(.caption).foregroundColor(.gray).padding(.top, 10)
            }
        }
        .modifier(CardModifier())
    }
}


