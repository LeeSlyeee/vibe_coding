
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
                    // 1. 요약 정보
                    HStack(spacing: 15) {
                        VStack {
                            Text("총 기록일")
                                .font(.caption)
                                .foregroundColor(.gray)
                            Text("\(stats.totalEntries)일")
                                .font(.title2)
                                .fontWeight(.bold)
                        }
                        
                        Divider().frame(height: 40)
                        
                        VStack {
                            Text("연속 기록")
                                .font(.caption)
                                .foregroundColor(.gray)
                            Text("\(stats.writingStreak)일")
                                .font(.title2)
                                .fontWeight(.bold)
                        }
                        
                        Divider().frame(height: 40)
                        
                        VStack {
                            Text("현재 상태")
                                .font(.caption)
                                .foregroundColor(.gray)
                            Text(stats.recentStatus)
                                .font(.subheadline)
                                .fontWeight(.bold)
                        }
                        .layoutPriority(1)
                    }
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(Color(.systemBackground))
                    .cornerRadius(16)
                    .shadow(color: .black.opacity(0.05), radius: 5, x: 0, y: 2)
                    .padding(.horizontal)
                    
                    // 2. Chart
                    if let moodRestricted = stats.moodRestricted, moodRestricted {
                        VStack(alignment: .leading, spacing: 10) {
                            Text("🔒 감정 통계 비공개")
                                .font(.headline)
                            Text("내담자가 마음 온도 통계를 비공개로 설정했습니다.")
                                .font(.caption)
                                .foregroundColor(.gray)
                        }
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color(.systemBackground))
                        .cornerRadius(16)
                        .shadow(color: .black.opacity(0.05), radius: 5, x: 0, y: 2)
                        .padding(.horizontal)
                    } else if !stats.moodTrend.isEmpty {
                        VStack(alignment: .leading) {
                            HStack {
                                Text("📊 최근 7일 기분 흐름")
                                    .font(.headline)
                                Spacer()
                                if let avgInt = stats.avgMood {
                                    Text("평균 \(String(format: "%.1f", avgInt))도")
                                        .font(.caption)
                                        .foregroundColor(.gray)
                                }
                            }
                            
                            Chart {
                                ForEach(stats.moodTrend.reversed(), id: \.date) { item in
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
                    }
                    
                    // 3. 감정 분석 보고서 (문장 형태)
                    if let narrative = stats.narrativeSummary, !narrative.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("📝 감정 분석 보고서")
                                .font(.headline)
                            
                            ForEach(narrative, id: \.self) { line in
                                Text(line)
                                    .font(.subheadline)
                                    .lineSpacing(4)
                                    .foregroundColor(.primary)
                            }
                        }
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color(.systemBackground))
                        .cornerRadius(16)
                        .shadow(color: .black.opacity(0.05), radius: 5, x: 0, y: 2)
                        .padding(.horizontal)
                    }
                    
                    // 4. Risk Alert
                    if let hasConcern = stats.hasSafetyConcern, hasConcern {
                        HStack {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundColor(.red)
                            VStack(alignment: .leading) {
                                Text("위기 신호 감지됨")
                                    .font(.headline)
                                    .foregroundColor(.red)
                                Text("최근 기록에서 위험할 수 있는 감정이 파악되었습니다. 내담자의 안부를 확인해주세요.")
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
