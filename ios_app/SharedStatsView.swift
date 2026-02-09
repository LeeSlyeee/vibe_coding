
import SwiftUI
import Charts

struct SharedStatsView: View {
    @ObservedObject var shareManager = ShareManager.shared
    let targetId: String
    let targetName: String
    
    @State private var isLoading = true
    
    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                if isLoading {
                    ProgressView("데이터 동기화 중...")
                        .padding(.top, 50)
                } else if let stats = shareManager.currentSharedStats {
                    // 1. Sync Time
                    HStack {
                        Spacer()
                        Text("마지막 업데이트: \(formatDate(stats.lastSync))")
                            .font(.caption2)
                            .foregroundColor(.gray)
                    }
                    .padding(.horizontal)
                    
                    // 2. Chart
                    VStack(alignment: .leading) {
                        Text("📊 최근 7일 기분 흐름")
                            .font(.headline)
                        
                        Chart {
                            ForEach(stats.recentMoods.reversed(), id: \.date) { item in
                                LineMark(
                                    x: .value("날짜", formatShortDate(item.date)),
                                    y: .value("기분", item.mood)
                                )
                                .interpolationMethod(.catmullRom)
                                .symbol(Circle())
                                .foregroundStyle(Color.blue)
                                
                                AreaMark(
                                    x: .value("날짜", formatShortDate(item.date)),
                                    y: .value("기분", item.mood)
                                )
                                .interpolationMethod(.catmullRom)
                                .foregroundStyle(
                                    LinearGradient(
                                        colors: [.blue.opacity(0.3), .clear],
                                        startPoint: .top,
                                        endPoint: .bottom
                                    )
                                )
                            }
                        }
                        .frame(height: 200)
                        .chartYScale(domain: 0...6)
                        .chartYAxis {
                            AxisMarks(values: [1, 2, 3, 4, 5]) { value in
                                AxisValueLabel {
                                    if let intVal = value.as(Int.self) {
                                        Text(moodEmoji(intVal))
                                    }
                                }
                            }
                        }
                    }
                    .padding()
                    .background(Color(.systemBackground))
                    .cornerRadius(16)
                    .shadow(color: .black.opacity(0.05), radius: 5, x: 0, y: 2)
                    .padding(.horizontal)
                    
                    // 3. AI Report
                    VStack(alignment: .leading, spacing: 10) {
                        Text("💌 최근 AI 리포트")
                            .font(.headline)
                        
                        if stats.latestReport.isEmpty || stats.latestReport.contains("없습니다") {
                            Text("아직 생성된 리포트가 없습니다.")
                                .foregroundColor(.gray)
                                .padding()
                        } else {
                            Text(stats.latestReport)
                                .font(.body)
                                .lineSpacing(4)
                        }
                    }
                    .padding()
                    .background(Color(.systemBackground))
                    .cornerRadius(16)
                    .shadow(color: .black.opacity(0.05), radius: 5, x: 0, y: 2)
                    .padding(.horizontal)
                    
                    // 4. Risk Alert
                    if stats.riskLevel >= 3 {
                        HStack {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundColor(.red)
                            VStack(alignment: .leading) {
                                Text("주의 필요")
                                    .font(.headline)
                                    .foregroundColor(.red)
                                Text("최근 감정 상태가 불안정할 수 있습니다.")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.red.opacity(0.1))
                        .cornerRadius(12)
                        .padding(.horizontal)
                    }
                    
                } else {
                    Text("데이터를 불러올 수 없습니다.")
                        .foregroundColor(.gray)
                        .padding(.top, 50)
                }
            }
            .padding(.vertical)
        }
        .navigationTitle("\(targetName)님의 마음")
        .background(Color(.systemGroupedBackground))
        .onAppear {
            shareManager.fetchSharedStats(targetId: targetId) { success in
                self.isLoading = false
            }
        }
    }
    
    // Helpers
    func formatDate(_ iso: String) -> String {
        // Simple formater
        let isoFormatter = ISO8601DateFormatter()
        isoFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds] 
        // Fallback or multiple format support might be needed
        
        // Fast hack for display
        return iso.replacingOccurrences(of: "T", with: " ").prefix(16).description
    }

    func formatShortDate(_ str: String) -> String {
        // "2025-02-09" -> "02-09"
        return String(str.dropFirst(5))
    }
    
    func moodEmoji(_ level: Int) -> String {
        switch level {
        case 1: return "🤬"
        case 2: return "😢"
        case 3: return "😐"
        case 4: return "😌"
        case 5: return "🥰"
        default: return ""
        }
    }
}
