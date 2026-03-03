
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
    
    // [New] 마음 온도 State
    @State private var moodTemperature: Double = 36.5
    @State private var moodTempLabel: String = "측정 중"
    @State private var moodTempDesc: String = ""
    @State private var moodTempColor: String = "#86868b"
    @State private var moodTempLoaded = false
    
    
    
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
                            Text("⚠️ 주의가 필요한 상태입니다.\n전문가의 도움을 받기 위해\n보건소/정신건강복지센터와 연동해주세요.")
                                .multilineTextAlignment(.center)
                                .foregroundColor(.red)
                                .fontWeight(.semibold)
                        } else {
                            // 경증(일반) 사용자용 메시지
                            Text("보건소/정신건강복지센터와 연동하시면\n심층 통계 분석 기능을 이용하실 수 있습니다.")
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
                        Text("보건소나 정신건강복지센터에서 발급받은\n코드를 입력해주세요.")
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
                .padding(.bottom, 10)
                .background(Color.white.opacity(0.8))
                
                // 마음 온도 카드
                if moodTempLoaded {
                    HStack(spacing: 16) {
                        // 온도계 아이콘
                        ZStack {
                            Circle()
                                .fill(Color(hexString: moodTempColor).opacity(0.15))
                                .frame(width: 60, height: 60)
                            Text(String(format: "%.1f°", moodTemperature))
                                .font(.system(size: 18, weight: .bold))
                                .foregroundColor(Color(hexString: moodTempColor))
                        }
                        
                        VStack(alignment: .leading, spacing: 4) {
                            Text("마음 온도")
                                .font(.caption)
                                .foregroundColor(.secondaryText)
                            Text(moodTempLabel)
                                .font(.headline)
                                .foregroundColor(Color(hexString: moodTempColor))
                            Text(moodTempDesc)
                                .font(.caption2)
                                .foregroundColor(.secondaryText)
                                .lineLimit(2)
                        }
                        
                        Spacer()
                    }
                    .padding(16)
                    .background(Color.white)
                    .cornerRadius(16)
                    .shadow(color: Color.black.opacity(0.05), radius: 5)
                    .padding(.horizontal, 24)
                    .padding(.bottom, 10)
                }
                
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
        // [Fix] 연동 여부와 상관없이 일단 로컬 데이터 계산 (잠금 화면 뒤에서도 준비)
        fetchStats()
        if b2gManager.isLinked {
            fetchExistingReports()
        }
        fetchMoodTemperature()
    }
    .onReceive(NotificationCenter.default.publisher(for: NSNotification.Name("RefreshStats"))) { _ in
        // [UX] 데이터 갱신 알림 수신 시 재계산
        print("🔄 [Stats] Refreshing stats due to data change...")
        fetchStats()
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
                    .environmentObject(authManager)
                    .navigationBarItems(trailing: Button("닫기") {
                        showSettings = false
                    })
                    .screenshotProtected(isProtected: false)
            }
        }
        .preferredColorScheme(.light) // ⭐️ 화이트 테마 강제
    }
    
    // [New] 마음 온도 API 호출
    func fetchMoodTemperature() {
        guard let token = authManager.token else { return }
        
        let baseURL = "https://217.142.253.35.nip.io/api"
        guard let url = URL(string: "\(baseURL)/mood-temperature") else { return }
        
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                return
            }
            
            DispatchQueue.main.async {
                if let temp = json["temperature"] as? Double {
                    self.moodTemperature = temp
                }
                if let label = json["label"] as? String {
                    self.moodTempLabel = label
                }
                if let desc = json["description"] as? String {
                    self.moodTempDesc = desc
                }
                if let color = json["color"] as? String {
                    self.moodTempColor = color
                }
                self.moodTempLoaded = true
            }
        }.resume()
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
            let originalDiaries = LocalDataManager.shared.diaries
            
            // [Filter] 미래 날짜 데이터 제외 (통계 오류 방지, 2026-08 등등)
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd"
            let todayStr = formatter.string(from: Date())
            
            // 오늘 날짜보다 미래인 데이터는 통계에서 제외
            let diaries = originalDiaries.filter { ($0.date ?? "") <= todayStr }
            
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
                // [Fix] 1~5 범위로 정규화 (Clamp)
                let normalizedMood = min(max(diary.mood_level, 1), 5)
                moodCounts[normalizedMood, default: 0] += 1
            }
            let moods = moodCounts.map { StatsMoodItem(_id: $0.key, count: $0.value) }
            
            // 4. Weather (날씨별 감정 통계 구현)
            var weatherMap = [String: [Int: Int]]()
            
            for diary in diaries {
                let w = diary.weather ?? "알 수 없음"
                // [Fix] 날씨 데이터가 없으면 통계 제외
                if w == "알 수 없음" || w.isEmpty { continue }
                
                if weatherMap[w] == nil { weatherMap[w] = [:] }
                
                let normalizedMood = min(max(diary.mood_level, 1), 5)
                weatherMap[w]![normalizedMood, default: 0] += 1
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
        
        // 로컬 일기 데이터 수집
        let diaries = LocalDataManager.shared.diaries
        let diaryPayloads: [[String: Any]] = diaries.prefix(20).map { diary in
            return [
                "date": diary.date ?? "",
                "content": diary.event ?? "",
                "mood_level": diary.mood_level,
                "weather": diary.weather ?? ""
            ]
        }
        
        guard !diaryPayloads.isEmpty else {
            self.reportContent = "아직 기록이 없어요.\n괜찮아요, 편안할 때 한마디 남겨보세요. 🌿"
            self.isGeneratingReport = false
            return
        }
        
        // [1순위] 서버 API (RunPod → Ollama)
        APIService.shared.requestAnalysisReport(diaries: diaryPayloads, mode: "short") { result in
            DispatchQueue.main.async {
                switch result {
                case .success(let report):
                    self.reportContent = report
                    self.isGeneratingReport = false
                    print("✅ [Stats] 분석 리포트 수신 (서버)")
                    
                case .failure(let error):
                    print("⚠️ [Stats] 서버 분석 실패: \(error.localizedDescription). 온디바이스 LLM 시도...")
                    // [2순위] 온디바이스 LLM
                    self.generateReportOnDevice(diaries: diaries, mode: "short")
                }
            }
        }
    }
    
    func startLongTermReport() { 
        isGeneratingLongTerm = true
        
        let diaries = LocalDataManager.shared.diaries
        let diaryPayloads: [[String: Any]] = diaries.prefix(30).map { diary in
            return [
                "date": diary.date ?? "",
                "content": diary.event ?? "",
                "mood_level": diary.mood_level,
                "weather": diary.weather ?? ""
            ]
        }
        
        guard !diaryPayloads.isEmpty else {
            self.longTermContent = "장기 분석을 위해 최소 3일 이상의 일기가 필요해요. 꾸준히 기록해주세요! 💪"
            self.isGeneratingLongTerm = false
            return
        }
        
        // [1순위] 서버 API (RunPod → Ollama)
        APIService.shared.requestAnalysisReport(diaries: diaryPayloads, mode: "long") { result in
            DispatchQueue.main.async {
                switch result {
                case .success(let report):
                    self.longTermContent = report
                    self.isGeneratingLongTerm = false
                    print("✅ [Stats] 메타 분석 수신 (서버)")
                    
                case .failure(let error):
                    print("⚠️ [Stats] 서버 메타 분석 실패: \(error.localizedDescription). 온디바이스 LLM 시도...")
                    // [2순위] 온디바이스 LLM
                    self.generateReportOnDevice(diaries: diaries, mode: "long")
                }
            }
        }
    }
    
    // [2순위] 온디바이스 LLM → [3순위] 하드코딩 Fallback
    private func generateReportOnDevice(diaries: [Diary], mode: String) {
        let llmService = LLMService.shared
        
        // 온디바이스 모델이 로드되어 있는지 확인
        guard llmService.isModelLoaded else {
            print("⚠️ [Stats] 온디바이스 모델 미로드. Fallback 텍스트 사용.")
            applyFallbackReport(mode: mode, diaries: diaries)
            return
        }
        
        // 일기 요약 텍스트 생성
        let summaryParts = diaries.prefix(10).compactMap { diary -> String? in
            guard let content = diary.event, !content.isEmpty else { return nil }
            return "[\(diary.date ?? "")] 기분:\(diary.mood_level)/5 | \(String(content.prefix(100)))"
        }
        let summaryText = summaryParts.joined(separator: "\n")
        
        let prompt: String
        if mode == "long" {
            prompt = "아래 일기를 보고 장기적인 감정 패턴을 분석하고, 따뜻하게 조언해줘. 300자 내외로.\n\n\(summaryText)\n\n분석:"
        } else {
            prompt = "아래 일기를 보고 전반적인 감정 상태를 3줄로 요약하고 격려해줘. 200자 내외로.\n\n\(summaryText)\n\n요약:"
        }
        
        Task {
            do {
                let response = try await llmService.generateText(prompt: prompt)
                await MainActor.run {
                    if mode == "long" {
                        self.longTermContent = response
                        self.isGeneratingLongTerm = false
                    } else {
                        self.reportContent = response
                        self.isGeneratingReport = false
                    }
                    print("✅ [Stats] 분석 완료 (온디바이스 LLM)")
                }
            } catch {
                print("⚠️ [Stats] 온디바이스 LLM 실패: \(error.localizedDescription). Fallback 사용.")
                await MainActor.run {
                    self.applyFallbackReport(mode: mode, diaries: diaries)
                }
            }
        }
    }
    
    // [3순위] 하드코딩 Fallback (로컬 데이터 기반 통계)
    private func applyFallbackReport(mode: String, diaries: [Diary]) {
        let avgMood = diaries.isEmpty ? 3.0 : Double(diaries.reduce(0) { $0 + $1.mood_level }) / Double(diaries.count)
        let totalDays = diaries.count
        let moodLabel: String
        if avgMood >= 4.0 { moodLabel = "긍정적" }
        else if avgMood >= 3.0 { moodLabel = "안정적" }
        else { moodLabel = "다소 힘든" }
        
        if mode == "long" {
            self.longTermContent = """
            [로컬 분석] 총 \(totalDays)일간의 기록을 분석했어요.
            평균 기분 점수는 \(String(format: "%.1f", avgMood))/5로, 전반적으로 \(moodLabel)인 상태예요.
            꾸준히 기록하고 계신 것만으로도 정말 대단해요. 계속 응원할게요! 💛
            (서버 연결 시 더 정밀한 AI 분석을 받아보실 수 있어요)
            """
            self.isGeneratingLongTerm = false
        } else {
            self.reportContent = """
            [로컬 분석] \(totalDays)일간의 기록을 살펴봤어요.
            전반적으로 \(moodLabel)인 기분 흐름이에요.
            매일 기록하는 습관이 마음 건강에 큰 도움이 된답니다! 🌱
            (서버 연결 시 더 정밀한 AI 분석을 받아보실 수 있어요)
            """
            self.isGeneratingReport = false
        }
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
                
                VStack(alignment: .leading, spacing: 2) {
                    Text("💡 AI 분석은 참고용이며, 전문 의료 서비스를 대체하지 않습니다.")
                        .font(.caption2)
                        .foregroundColor(.gray)
                    Text("⚠️ 위기 감지는 보조적 수단이며, 100% 정확성을 보장하지 않습니다.")
                        .font(.caption2)
                        .foregroundColor(.orange)
                }
                .padding(.top, 4)
            }
        }
        .modifier(CardModifier())
    }
}


