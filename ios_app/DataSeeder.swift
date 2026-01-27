
import Foundation

class DataSeeder {
    static let shared = DataSeeder()
    
    private init() {}
    
    func seedDummyData(completion: @escaping (Int) -> Void) {
        var dummyDiaries: [Diary] = []
        let today = Date()
        let calendar = Calendar.current
        
        // 지난 14일간의 데이터 생성
        for i in 0..<14 {
            guard let date = calendar.date(byAdding: .day, value: -i, to: today) else { continue }
            let dateStr = formatDate(date)
            let timeStr = formatDateTime(date)
            
            // 랜덤 감정 및 내용 생성
            let moodLevel = Int.random(in: 1...5) // 1:매우나쁨 ~ 5:매우좋음
            let content = generateContent(for: moodLevel)
            
            let diary = Diary(
                id: UUID().uuidString,
                _id: nil,
                date: dateStr,
                mood_level: moodLevel,
                event: content.event,
                emotion_desc: content.emotion,
                emotion_meaning: "이 감정이 나에게 어떤 의미인지 생각해보았다.",
                self_talk: "그래도 오늘 하루 잘 버텼어. 내일은 더 좋을 거야.",
                sleep_desc: Bool.random() ? "푹 잤다." : "중간에 깼다.",
                weather: ["맑음", "흐림", "비", "눈"].randomElement(),
                temperature: Double.random(in: -5...15),
                sleep_condition: nil,
                ai_prediction: nil,
                ai_comment: "당신의 마음을 이해합니다. " + content.emotion,
                ai_analysis: nil,
                ai_advice: nil,
                created_at: timeStr
            )
            
            dummyDiaries.append(diary)
        }
        
        // 로컬 매니저에 저장
        let group = DispatchGroup()
        var count = 0
        
        for diary in dummyDiaries {
            group.enter()
            LocalDataManager.shared.saveDiary(diary) { success in
                if success { count += 1 }
                group.leave()
            }
        }
        
        group.notify(queue: .main) {
            completion(count)
        }
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }
    
    private func formatDateTime(_ date: Date) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter.string(from: date)
    }
    
    private func generateContent(for mood: Int) -> (event: String, emotion: String) {
        switch mood {
        case 1:
            return ("직장에서 큰 실수를 했다.", "정말 최악의 하루였다. 기분이 너무 가라앉는다.")
        case 2:
            return ("친구와 말다툼을 했다.", "속상하고 마음이 복잡하다. 왜 그랬을까 후회된다.")
        case 3:
            return ("평범한 하루였다.", "특별한 일은 없었고 그냥 무덤덤하다.")
        case 4:
            return ("오랜만에 산책을 다녀왔다.", "상쾌하고 기분이 한결 가벼워졌다.")
        case 5:
            return ("프로젝트가 성공적으로 끝났다!", "날아갈 것 같이 기쁘다. 성취감이 느껴진다.")
        default:
            return ("오늘 하루를 기록한다.", "그저 그런 하루.")
        }
    }
}
