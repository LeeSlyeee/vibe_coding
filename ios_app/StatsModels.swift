import Foundation

// MARK: - AppStatsView Data Models

struct StatisticsResponse: Codable {
    let timeline: [StatsTimelineItem]?
    let daily: [StatsDailyItem]?
    let moods: [StatsMoodItem]?
    let weather: [StatsWeatherItem]?
}

struct StatsTimelineItem: Codable, Identifiable {
    var id: String { date }
    let date: String
    let mood_level: Int
    let ai_label: String?
}

struct StatsDailyItem: Codable {
    let _id: String
    let count: Int
}

struct StatsMoodItem: Codable, Identifiable {
    var id: Int { _id }
    let _id: Int
    let count: Int
}

struct StatsWeatherItem: Codable, Identifiable {
    var id: String { _id }
    let _id: String
    let moods: [StatsMoodCount]?
}

struct StatsMoodCount: Codable, Hashable {
    let mood: Int
    let count: Int
}

struct ReportStatusResponse: Codable {
    let status: String
    let report: String?
    let insight: String?
}
