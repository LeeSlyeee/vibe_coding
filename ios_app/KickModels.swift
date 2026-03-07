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
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(Int.self, forKey: .id)
        title = try container.decode(String.self, forKey: .title)
        content = try container.decodeIfPresent(String.self, forKey: .content)
        startDate = try container.decodeIfPresent(String.self, forKey: .startDate)
        endDate = try container.decodeIfPresent(String.self, forKey: .endDate)
        isRead = try container.decodeIfPresent(Bool.self, forKey: .isRead) ?? true
        createdAt = try container.decodeIfPresent(String.self, forKey: .createdAt)
    }
    
    // 데모 데이터용 직접 초기화
    init(id: Int, title: String, content: String?, startDate: String?, endDate: String?, isRead: Bool, createdAt: String?) {
        self.id = id
        self.title = title
        self.content = content
        self.startDate = startDate
        self.endDate = endDate
        self.isRead = isRead
        self.createdAt = createdAt
    }
}

// Relational Map node structure
struct RelationalNode: Codable, Identifiable {
    let id: String
    let group: Int
    let size: Int
    let color: String
    let mentionCount: Int?    // 언급 횟수
    let lastSeen: String?     // 마지막 언급일
    let summary: String?      // 인물별 고유 한 줄 요약
    
    enum CodingKeys: String, CodingKey {
        case id, group, size, color
        case mentionCount = "mention_count"
        case lastSeen = "last_seen"
        case summary
    }
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
