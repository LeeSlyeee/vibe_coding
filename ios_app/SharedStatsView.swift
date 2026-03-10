
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
                    // --- 🎨 공유받은 내담자의 마음 리포트 카드 ---
                    VStack(spacing: 0) {
                        // 헤더
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("\(targetName)님의 마음 리포트")
                                    .font(.headline)
                                    .fontWeight(.bold)
                                    .foregroundColor(.white)
                                Text("마음온 AI 요약 브리핑")
                                    .font(.caption)
                                    .foregroundColor(.white.opacity(0.8))
                            }
                            Spacer()
                            Image(systemName: "sparkles")
                                .font(.title2)
                                .foregroundColor(.white.opacity(0.8))
                        }
                        .padding(20)
                        .background(
                            LinearGradient(
                                colors: [.blue, .purple],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        
                        VStack(spacing: 16) {
                            // 1. 상태 및 마음 온도
                            HStack {
                                VStack(alignment: .leading, spacing: 8) {
                                    Text("최근 감정 상태")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                    Text(stats.recentStatus)
                                        .font(.system(size: 24, weight: .bold))
                                        .foregroundColor(.primary)
                                }
                                Spacer()
                                if let avgInt = stats.avgMood {
                                    VStack(alignment: .trailing, spacing: 8) {
                                        Text("평균 온도")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                        Text("\(String(format: "%.1f", avgInt))도")
                                            .font(.title2)
                                            .fontWeight(.bold)
                                            .foregroundColor(.blue)
                                    }
                                }
                            }
                            
                            Divider()
                            
                            // 2. 주간 추이
                            if let moodRestricted = stats.moodRestricted, moodRestricted {
                                HStack {
                                    Image(systemName: "lock.fill")
                                        .foregroundColor(.gray)
                                    Text("내담자가 감정 흐름을 비공개로 설정했습니다.")
                                        .font(.caption)
                                        .foregroundColor(.gray)
                                }
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.vertical, 4)
                            } else if !stats.moodTrend.isEmpty {
                                VStack(alignment: .leading, spacing: 8) {
                                    Text("최근 감정 변화")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                    
                                    HStack(alignment: .bottom, spacing: 8) {
                                        ForEach(stats.moodTrend.reversed(), id: \.date) { item in
                                            VStack(spacing: 4) {
                                                RoundedRectangle(cornerRadius: 4)
                                                    .fill(getTrendColor(item.mood))
                                                    .frame(width: 28, height: CGFloat(item.mood) * 10 + 10)
                                                Text(formatShortDate(item.date))
                                                    .font(.system(size: 9))
                                                    .foregroundColor(.secondary)
                                            }
                                        }
                                    }
                                    .frame(maxWidth: .infinity)
                                }
                                Divider()
                            }
                            
                            // 3. AI 분석 보고서
                            if let narrative = stats.narrativeSummary, !narrative.isEmpty {
                                VStack(alignment: .leading, spacing: 8) {
                                    HStack {
                                        Image(systemName: "text.bubble.fill")
                                            .foregroundColor(.purple)
                                        Text("AI 분석 요약")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                    
                                    ForEach(narrative, id: \.self) { line in
                                        Text(line)
                                            .font(.subheadline)
                                            .lineSpacing(4)
                                            .foregroundColor(.primary)
                                            .multilineTextAlignment(.leading)
                                    }
                                }
                                .frame(maxWidth: .infinity, alignment: .leading)
                            }
                        }
                        .padding(20)
                        .background(Color(.systemBackground))
                    }
                    .cornerRadius(20)
                    .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 5)
                    .padding(.horizontal)
                    
                    // 기존 통계치
                    HStack(spacing: 15) {
                        VStack {
                            Text("총 기록일")
                                .font(.caption)
                                .foregroundColor(.gray)
                            Text("\(stats.totalEntries)일")
                                .font(.title3)
                                .fontWeight(.bold)
                        }
                        Divider().frame(height: 30)
                        VStack {
                            Text("연속 기록")
                                .font(.caption)
                                .foregroundColor(.gray)
                            Text("\(stats.writingStreak)일")
                                .font(.title3)
                                .fontWeight(.bold)
                        }
                    }
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(Color(.systemBackground))
                    .cornerRadius(16)
                    .shadow(color: .black.opacity(0.05), radius: 5, x: 0, y: 2)
                    .padding(.horizontal)
                    
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
        .onReceive(NotificationCenter.default.publisher(for: UIApplication.willEnterForegroundNotification)) { _ in
            // 포그라운드 복귀 시(푸시 탭 등으로 이미 켜져 있을 때) 최신 데이터로 리프레시
            shareManager.fetchSharedStats(targetId: targetId) { _ in }
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
        case 1: return "최악"
        case 2: return "나쁨"
        case 3: return "보통"
        case 4: return "좋음"
        case 5: return "최고"
        default: return ""
        }
    }
    
    func getTrendColor(_ level: Int) -> Color {
        switch level {
        case 1: return .red
        case 2: return .orange
        case 3: return .yellow
        case 4: return .green
        case 5: return .blue
        default: return .gray
        }
    }
}
