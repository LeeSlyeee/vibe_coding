
import Foundation

struct Diary: Codable, Identifiable, Equatable {
    var id: String?
    var _id: String? // MongoDB ID
    var date: String?
    var mood_level: Int
    var event: String?
    var emotion_desc: String?
    var emotion_meaning: String?
    var self_talk: String?
    var sleep_desc: String?
    var weather: String?
    var temperature: Double?
    
    var sleep_condition: String? // Legacy support
    
    // AI Related
    var ai_prediction: String?
    var ai_comment: String?
    var ai_analysis: String?
    var ai_advice: String?
    
    var created_at: String?

    // Computed property for ID consistency
    var realId: String? {
        return _id ?? id
    }
    
    enum CodingKeys: String, CodingKey {
        case id
        case _id
        case date
        case mood_level
        case event
        case emotion_desc
        case emotion_meaning
        case self_talk
        case sleep_desc
        case sleep_condition
        case weather
        case temperature
        case ai_prediction
        case ai_comment
        case ai_analysis
        case ai_advice
        case created_at
    }
}
