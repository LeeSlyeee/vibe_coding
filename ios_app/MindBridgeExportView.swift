
import SwiftUI

// MARK: - 마음 브릿지 감정 리포트 Export
// Phase 2: 감정 상태를 이미지 카드로 생성 → 카카오톡/메시지로 공유
// 서버를 거치지 않고, 기기에서 직접 이미지를 생성하여 프라이버시 보장

struct MindBridgeExportView: View {
    @Environment(\.dismiss) var dismiss
    @StateObject private var viewModel = ExportViewModel()
    
    // 공유 범위 토글
    @State private var includeMoodScore = true
    @State private var includeWeeklyTrend = true
    @State private var includeAIComment = true
    @State private var includeEmoji = true
    
    // 공유 시트
    @State private var showShareSheet = false
    @State private var exportedImage: UIImage?
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 24) {
                    
                    // MARK: - 미리보기 카드
                    reportCardPreview
                        .padding(.horizontal)
                    
                    // MARK: - 공유 깊이 설정
                    shareDepthSection
                        .padding(.horizontal)
                    
                    // MARK: - 내보내기 버튼
                    exportButton
                        .padding(.horizontal)
                    
                    // MARK: - 안내 문구
                    privacyNotice
                        .padding(.horizontal)
                }
                .padding(.vertical)
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("감정 리포트 공유")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("닫기") { dismiss() }
                }
            }
            .onAppear {
                viewModel.loadRecentData()
            }
            .sheet(isPresented: $showShareSheet) {
                if let image = exportedImage {
                    ActivityView(activityItems: [image, shareMessage])
                }
            }
        }
    }
    
    // MARK: - 감정 리포트 카드 (미리보기 + 이미지 생성 소스)
    var reportCardPreview: some View {
        VStack(spacing: 0) {
            // 헤더
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(viewModel.userName + "님의 마음 리포트")
                        .font(.headline)
                        .fontWeight(.bold)
                        .foregroundColor(.white)
                    Text(viewModel.dateRangeText)
                        .font(.caption)
                        .foregroundColor(.white.opacity(0.8))
                }
                Spacer()
                Image(systemName: "heart.text.clipboard")
                    .font(.title2)
                    .foregroundColor(.white.opacity(0.8))
            }
            .padding(20)
            .background(
                LinearGradient(
                    colors: [Color(hexString: "6366f1"), Color(hexString: "8b5cf6")],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
            
            VStack(spacing: 16) {
                // 오늘의 감정
                if includeEmoji {
                    HStack(spacing: 12) {
                        Text(viewModel.todayEmoji)
                            .font(.system(size: 32, weight: .bold))
                            .foregroundColor(Color(hexString: "6366f1"))
                        VStack(alignment: .leading, spacing: 4) {
                            Text("오늘의 감정")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            Text(viewModel.todayMoodLabel)
                                .font(.title3)
                                .fontWeight(.bold)
                        }
                        Spacer()
                    }
                }
                
                // 감정 온도
                if includeMoodScore {
                    HStack {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("마음 온도")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            HStack(alignment: .bottom, spacing: 4) {
                                Text("\(viewModel.moodScore)")
                                    .font(.system(size: 36, weight: .bold))
                                    .foregroundColor(moodColor(viewModel.moodScore))
                                Text("/ 100")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                    .padding(.bottom, 6)
                            }
                        }
                        Spacer()
                        // 미니 게이지
                        ZStack(alignment: .leading) {
                            RoundedRectangle(cornerRadius: 6)
                                .fill(Color(.systemGray5))
                                .frame(width: 120, height: 12)
                            RoundedRectangle(cornerRadius: 6)
                                .fill(moodColor(viewModel.moodScore))
                                .frame(width: CGFloat(viewModel.moodScore) * 1.2, height: 12)
                        }
                    }
                    
                    Divider()
                }
                
                // 주간 추이
                if includeWeeklyTrend {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("최근 7일 감정 변화")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        HStack(alignment: .bottom, spacing: 8) {
                            ForEach(viewModel.weeklyMoods, id: \.day) { mood in
                                VStack(spacing: 4) {
                                    RoundedRectangle(cornerRadius: 4)
                                        .fill(moodColor(mood.score))
                                        .frame(width: 28, height: CGFloat(mood.score) * 0.6 + 10)
                                    Text(mood.day)
                                        .font(.system(size: 9))
                                        .foregroundColor(.secondary)
                                }
                            }
                        }
                        .frame(maxWidth: .infinity)
                    }
                    
                    Divider()
                }
                
                // AI 코멘트
                if includeAIComment {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Image(systemName: "sparkles")
                                .foregroundColor(Color(hexString: "6366f1"))
                            Text("AI 분석 요약")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        Text(viewModel.aiSummary)
                            .font(.subheadline)
                            .foregroundColor(.primary)
                            .lineSpacing(4)
                    }
                }
                
                // 워터마크
                HStack {
                    Spacer()
                    Text("마음온 maumON")
                        .font(.system(size: 10))
                        .foregroundColor(.secondary.opacity(0.5))
                }
            }
            .padding(20)
            .background(Color(.systemBackground))
        }
        .cornerRadius(20)
        .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 5)
    }
    
    // MARK: - 공유 깊이 설정 섹션
    var shareDepthSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "slider.horizontal.3")
                    .foregroundColor(Color(hexString: "6366f1"))
                Text("공유할 항목 선택")
                    .font(.headline)
            }
            Text("어떤 정보를 포함할지 직접 결정하세요")
                .font(.caption)
                .foregroundColor(.secondary)
            
            VStack(spacing: 0) {
                ExportToggleRow(
                    icon: "감정",
                    title: "오늘의 감정 (이모지)",
                    isOn: $includeEmoji
                )
                Divider().padding(.leading, 50)
                ExportToggleRow(
                    icon: "온도",
                    title: "마음 온도 (점수)",
                    isOn: $includeMoodScore
                )
                Divider().padding(.leading, 50)
                ExportToggleRow(
                    icon: "",
                    title: "7일간 감정 변화",
                    isOn: $includeWeeklyTrend
                )
                Divider().padding(.leading, 50)
                ExportToggleRow(
                    icon: "✨",
                    title: "AI 분석 코멘트",
                    isOn: $includeAIComment
                )
            }
            .background(Color(.systemBackground))
            .cornerRadius(12)
        }
    }
    
    // MARK: - 내보내기 버튼
    var exportButton: some View {
        Button(action: generateAndShare) {
            HStack {
                Image(systemName: "square.and.arrow.up")
                Text("이미지로 공유하기")
                    .fontWeight(.bold)
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background(
                LinearGradient(
                    colors: [Color(hexString: "6366f1"), Color(hexString: "8b5cf6")],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .cornerRadius(14)
            .shadow(color: Color(hexString: "6366f1").opacity(0.3), radius: 8, x: 0, y: 4)
        }
    }
    
    // MARK: - 프라이버시 안내
    var privacyNotice: some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: "lock.shield.fill")
                .foregroundColor(.green)
            VStack(alignment: .leading, spacing: 4) {
                Text("프라이버시 보호")
                    .font(.caption)
                    .fontWeight(.bold)
                    .foregroundColor(.green)
                Text("일기 원문은 절대 포함되지 않습니다.\n서버를 거치지 않고 기기에서 직접 이미지를 생성합니다.")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
    
    // MARK: - 이미지 생성 및 공유
    func generateAndShare() {
        let renderer = ImageRenderer(content:
            reportCardPreview
                .frame(width: 360)
                .padding()
                .background(Color.white)
        )
        renderer.scale = 3.0 // @3x 해상도
        
        if let image = renderer.uiImage {
            exportedImage = image
            showShareSheet = true
        }
    }
    
    var shareMessage: String {
        "\(viewModel.userName)님의 마음 리포트 — 마음온 maumON"
    }
    
    // 감정 점수에 따른 색상
    func moodColor(_ score: Int) -> Color {
        switch score {
        case 0..<30: return .red
        case 30..<50: return .orange
        case 50..<70: return .yellow
        case 70..<85: return Color(hexString: "10b981")
        default: return Color(hexString: "6366f1")
        }
    }
}

// MARK: - Export Toggle Row
struct ExportToggleRow: View {
    let icon: String
    let title: String
    @Binding var isOn: Bool
    
    var body: some View {
        HStack {
            Text(icon)
                .font(.title2)
                .frame(width: 36)
            Text(title)
                .font(.subheadline)
            Spacer()
            Toggle("", isOn: $isOn)
                .labelsHidden()
        }
        .padding(.horizontal)
        .padding(.vertical, 10)
    }
}

// MARK: - ViewModel (로컬 데이터 기반)
class ExportViewModel: ObservableObject {
    @Published var userName: String = ""
    @Published var todayEmoji: String = "보통"
    @Published var todayMoodLabel: String = "보통"
    @Published var moodScore: Int = 65
    @Published var weeklyMoods: [WeeklyMood] = []
    @Published var aiSummary: String = ""
    @Published var dateRangeText: String = ""
    
    struct WeeklyMood {
        let day: String
        let score: Int
    }
    
    func loadRecentData() {
        // UserDefaults에서 사용자 이름 가져오기
        let defaults = UserDefaults.standard
        userName = defaults.string(forKey: "userNickname")
            ?? defaults.string(forKey: "authUsername")
            ?? "사용자"
        
        // 날짜 범위
        let formatter = DateFormatter()
        formatter.dateFormat = "M월 d일"
        let today = Date()
        let weekAgo = Calendar.current.date(byAdding: .day, value: -6, to: today)!
        dateRangeText = "\(formatter.string(from: weekAgo)) ~ \(formatter.string(from: today))"
        
        // 최근 일기 데이터에서 감정 정보 로드
        loadFromRecentDiaries()
    }
    
    private func loadFromRecentDiaries() {
        // APIService를 통해 최근 7일 데이터 조회
        let api = APIService.shared
        
        api.fetchDiaries { [weak self] diaries in
            DispatchQueue.main.async {
                guard let self = self else { return }
                
                guard let diaries = diaries, !diaries.isEmpty else {
                    self.aiSummary = "데이터를 불러올 수 없습니다."
                    // 빈 주간 데이터
                    let shortFormatter = DateFormatter()
                    shortFormatter.locale = Locale(identifier: "ko_KR")
                    shortFormatter.dateFormat = "E"
                    self.weeklyMoods = (0..<7).reversed().map { i in
                        let date = Calendar.current.date(byAdding: .day, value: -i, to: Date())!
                        return WeeklyMood(day: shortFormatter.string(from: date), score: 0)
                    }
                    return
                }
                
                let sortedDiaries = diaries.sorted { ($0["date"] as? String ?? "") > ($1["date"] as? String ?? "") }
                
                // 오늘 일기
                if let latest = sortedDiaries.first {
                    self.todayEmoji = (latest["mood_label"] as? String) ?? "보통"
                    self.todayMoodLabel = (latest["mood_label"] as? String) ?? "보통"
                    
                    // score 처리 (Int 또는 Double)
                    if let score = latest["score"] as? Int {
                        self.moodScore = score
                    } else if let score = latest["score"] as? Double {
                        self.moodScore = Int(score)
                    }
                    
                    // AI 분석 요약
                    if let aiResult = latest["ai_analysis"] as? [String: Any],
                       let comment = aiResult["comment"] as? String {
                        self.aiSummary = self.extractComment(from: comment)
                    } else if let comment = latest["ai_comment"] as? String {
                        self.aiSummary = self.extractComment(from: comment)
                    } else {
                        self.aiSummary = "아직 AI 분석 결과가 없습니다."
                    }
                }
                
                // 주간 데이터
                let dayFormatter = DateFormatter()
                dayFormatter.dateFormat = "yyyy-MM-dd"
                let shortFormatter = DateFormatter()
                shortFormatter.locale = Locale(identifier: "ko_KR")
                shortFormatter.dateFormat = "E"
                
                let calendar = Calendar.current
                var weekData: [WeeklyMood] = []
                
                for i in (0..<7).reversed() {
                    let date = calendar.date(byAdding: .day, value: -i, to: Date())!
                    let dateStr = dayFormatter.string(from: date)
                    let dayLabel = shortFormatter.string(from: date)
                    
                    if let diary = sortedDiaries.first(where: { ($0["date"] as? String)?.prefix(10) == dateStr.prefix(10) }) {
                        var score = 50
                        if let s = diary["score"] as? Int { score = s }
                        else if let s = diary["score"] as? Double { score = Int(s) }
                        weekData.append(WeeklyMood(day: dayLabel, score: score))
                    } else {
                        weekData.append(WeeklyMood(day: dayLabel, score: 0))
                    }
                }
                self.weeklyMoods = weekData
            }
        }
    }
    
    private func extractComment(from text: String) -> String {
        let cleanText = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if cleanText.contains("{") && cleanText.contains("}") {
            guard let startRange = cleanText.range(of: "{"),
                  let endRange = cleanText.range(of: "}", options: .backwards) else {
                return text
            }
            
            let jsonString = String(cleanText[startRange.lowerBound...endRange.upperBound])
            if let data = jsonString.data(using: .utf8),
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                if let c = json["comment"] as? String { return c }
                if let c = json["ai_comment"] as? String { return c }
                if let c = json["analysis"] as? String { return c }
                if let c = json["message"] as? String { return c }
            }
        }
        return text
    }
}

// MARK: - UIActivityViewController Wrapper
struct ActivityView: UIViewControllerRepresentable {
    let activityItems: [Any]
    
    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: activityItems, applicationActivities: nil)
    }
    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}
