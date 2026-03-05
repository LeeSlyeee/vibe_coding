import Foundation

struct WeeklyLetter: Codable, Identifiable {
    let id: Int
    let title: String
    let content: String?
    let startDate: String? // start_date from API
    let endDate: String? // end_date from API
    var isRead: Bool // is_read from API
    let createdAt: String? // created_at from API
    
    enum CodingKeys: String, CodingKey {
        case id, title, content
        case startDate = "start_date"
        case endDate = "end_date"
        case isRead = "is_read"
        case createdAt = "created_at"
    }
}

// Relational Map node structure
struct RelationalNode: Codable, Identifiable {
    let id: String
    let group: Int
    let size: Int
    let color: String
}

// Relational Map link structure
struct RelationalLink: Codable {
    let source: String
    let target: String
    let value: Int
}

struct RelationalMapResponse: Codable {
    let nodes: [RelationalNode]
    let links: [RelationalLink]
}
