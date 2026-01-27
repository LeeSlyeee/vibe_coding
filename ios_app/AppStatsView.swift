
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
    @State private var currentTab = "flow"
    @State private var stats: StatisticsResponse?
    @State private var isLoading = true
    
    @State private var isGeneratingReport = false
    @State private var reportContent: String = ""
    @State private var isGeneratingLongTerm = false
    @State private var longTermContent: String = ""
    
    let baseURL = "https://217.142.253.35.nip.io"
    
    let tabs = [
        ("flow", "흐름"),
        ("monthly", "월별"),
        ("mood", "분포"),
        ("weather", "날씨"),
        ("report", "AI분석")
    ]
    
    var body: some View {
        NavigationView {
            ZStack {
                Color.bgMain.edgesIgnoringSafeArea(.all)
                
                // [RBAC] Access Control for Mild Users (Level 1)
                if authManager.riskLevel == 1 {
                    VStack(spacing: 24) {
                        Spacer()
                        Image(systemName: "lock.shield.fill")
                            .font(.system(size: 80))
                            .foregroundColor(.gray.opacity(0.5))
                        
                        VStack(spacing: 8) {
                            Text("전문 분석 기능 잠김")
                                .font(.title2)
                                .fontWeight(.bold)
                                .foregroundColor(.primary)
                            Text("현재 '경증(안정)' 상태로 분류되어\n심층 통계 분석이 제한됩니다.")
                                .multilineTextAlignment(.center)
                                .foregroundColor(.secondary)
                        }
                        
                        Text("더 자세한 분석을 원하시면\n전문 상담사 모드로 전환해주세요.")
                            .font(.caption)
                            .foregroundColor(.gray)
                            .multilineTextAlignment(.center)
                            .padding(.top, 20)
                            
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
            #if os(iOS)
            .navigationBarHidden(true)
            #endif
            .onAppear {
                if authManager.riskLevel > 1 {
                    fetchStats()
                    fetchExistingReports()
                }
            }
        }
        .preferredColorScheme(.light) // ⭐️ 화이트 테마 강제
    }
    
    // API Logic
    func fetchStats() {
        guard let token = UserDefaults.standard.string(forKey: "authToken") else { return }
        guard let url = URL(string: "\(baseURL)/api/statistics") else { return }
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        URLSession.shared.dataTask(with: request) { d, _, _ in
            DispatchQueue.main.async { isLoading = false }
            guard let d = d else { return }
            do { self.stats = try JSONDecoder().decode(StatisticsResponse.self, from: d) } catch { print("\(error)") }
        }.resume()
    }
    func fetchExistingReports() {
        // Short-term report check
        apiCall(path: "/api/report/status", method: "GET") { data in
            guard let data = data, let res = try? JSONDecoder().decode(ReportStatusResponse.self, from: data) else { return }
            if res.status == "completed", let report = res.report {
                DispatchQueue.main.async { self.reportContent = report }
            }
        }
        
        // Long-term report check
        apiCall(path: "/api/report/longterm/status", method: "GET") { data in
            guard let data = data, let res = try? JSONDecoder().decode(ReportStatusResponse.self, from: data) else { return }
            if res.status == "completed", let insight = res.insight {
                DispatchQueue.main.async { self.longTermContent = insight }
            }
        }
    }

    func startReport() { 
        isGeneratingReport = true
        apiCall(path: "/api/report/start", method: "POST") { _ in pollStatus(isLongTerm: false) } 
    }
    
    func startLongTermReport() { 
        isGeneratingLongTerm = true
        apiCall(path: "/api/report/longterm/start", method: "POST") { _ in pollStatus(isLongTerm: true) } 
    }
    
    func pollStatus(isLongTerm: Bool) {
        let endpoint = isLongTerm ? "/api/report/longterm/status" : "/api/report/status"
        Timer.scheduledTimer(withTimeInterval: 3.0, repeats: true) { timer in
            apiCall(path: endpoint, method: "GET") { data in
                guard let data = data, let res = try? JSONDecoder().decode(ReportStatusResponse.self, from: data) else { return }
                if res.status == "completed" {
                    timer.invalidate()
                    DispatchQueue.main.async {
                        if isLongTerm { self.longTermContent = res.insight ?? ""; self.isGeneratingLongTerm = false }
                        else { self.reportContent = res.report ?? ""; self.isGeneratingReport = false }
                    }
                } else if res.status == "failed" {
                    timer.invalidate(); DispatchQueue.main.async { if isLongTerm { self.isGeneratingLongTerm = false } else { self.isGeneratingReport = false } }
                }
            }
        }
    }
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
        let minWidth: CGFloat = 350
        let itemWidth: CGFloat = 50
        return max(minWidth, CGFloat(data.count) * itemWidth)
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
                .padding(20).background(Color(hex: "F8F9FE")).cornerRadius(16)
                
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
                    }.padding(20).background(Color(hex: "F0FDF4")).cornerRadius(16)
                }
                Button("🔄 다시 분석") { startReport() }.font(.caption).foregroundColor(.gray).padding(.top, 10)
            }
        }
        .modifier(CardModifier())
    }
}
