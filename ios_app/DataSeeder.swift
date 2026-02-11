
import Foundation

class DataSeeder {
    static let shared = DataSeeder()
    
    private init() {}
    
    func seedDummyData(completion: @escaping (Int) -> Void) {
        var dummyDiaries: [Diary] = []
        let today = Date()
        let calendar = Calendar.current
        
        // Formatter (Local Date String)
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        dateFormatter.timeZone = TimeZone.current
        
        // 지난 14일간의 데이터 생성
        for i in 0..<14 {
            guard let date = calendar.date(byAdding: .day, value: -i, to: today) else { continue }
            let dateStr = dateFormatter.string(from: date)
            
            // [Realistic Time] 일기는 보통 밤 9시~11시에 씀
            // 해당 날짜(date)의 21:00 ~ 23:59 사이 랜덤 시간 생성
            var dateComponents = calendar.dateComponents([.year, .month, .day], from: date)
            dateComponents.hour = Int.random(in: 21...23)
            dateComponents.minute = Int.random(in: 0...59)
            dateComponents.second = Int.random(in: 0...59)
            let createdDate = calendar.date(from: dateComponents) ?? date
            
            // ISO8601 Format
            let isoFormatter = ISO8601DateFormatter()
            isoFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            let timeStr = isoFormatter.string(from: createdDate)
            
            // [Winter Context] 2월 날씨 반영
            let weather = ["맑음 ☀️", "맑음 ☀️", "흐림 ☁️", "눈 ❄️", "바람 💨"].randomElement() // 맑음 확률 높임
            let temp = Double.random(in: -7.0...8.0) // 2월 기온 (-7도 ~ 8도)
            
            // 랜덤 감정 및 내용 생성
            let moodLevel = Int.random(in: 1...5) // 1:매우나쁨 ~ 5:매우좋음
            let content = generateContent(for: moodLevel)
            
            // 약물 복용 시뮬레이션
            let tookMeds = Bool.random()
            var medDesc: String? = nil
            if tookMeds {
                let meds = ["비타민", "유산균", "혈압약", "진통제", "항우울제", "수면제"]
                let picked = meds.shuffled().prefix(Int.random(in: 1...2))
                medDesc = picked.joined(separator: ", ")
            }
            
            let diary = Diary(
                id: UUID().uuidString,
                _id: nil,
                date: dateStr,
                mood_level: moodLevel,
                event: content.event,
                emotion_desc: content.emotion,
                emotion_meaning: content.meaning,
                self_talk: content.selfTalk,
                sleep_desc: Bool.random() ? "푹 잤다. 개운하다." : "중간에 몇 번 깼지만 나쁘지 않다.",
                weather: weather,
                temperature: temp, 
                created_at: timeStr, // [Backdating] 과거 생성일 주입
                medication: tookMeds,
                medication_desc: medDesc
            )
            
            // AI 필드 (일부는 분석된 척)
            var finalDiary = diary
            if i > 0 { // 오늘 말고 과거 데이터는 분석 완료 처리
                 finalDiary.ai_prediction = ["평온", "우울", "기쁨", "불안"].randomElement()
                 finalDiary.ai_comment = "당신의 감정은 자연스러운 것입니다. " + content.emotion
                 finalDiary.ai_analysis = "전반적으로 감정의 기복이 보이지만, 긍정적인 신호도 있습니다."
                 finalDiary.ai_advice = "따뜻한 차를 마시며 휴식을 취해보세요."
            }
            
            dummyDiaries.append(finalDiary)
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
             print("🌱 Seeded \(count) dummy diaries.")
            // [UX] 통계 화면 갱신 트리거
            NotificationCenter.default.post(name: NSNotification.Name("RefreshStats"), object: nil)
            completion(count)
        }
    }
    
    // Content Tuple Update
    private func generateContent(for mood: Int) -> (event: String, emotion: String, meaning: String, selfTalk: String) {
        switch mood {
        case 1:
            return (
                "직장에서 큰 실수를 해서 상사에게 꾸중을 들었다.", 
                "정말 최악의 하루였다. 자괴감이 들고 숨고 싶다.",
                "내가 무능력하게 느껴진다. 실패가 두렵다.",
                "실수는 누구나 할 수 있어. 너무 자책하지 말자."
            )
        case 2:
            return (
                "친구와 사소한 일로 말다툼을 했다.", 
                "속상하고 마음이 복잡하다. 관계가 틀어질까 걱정된다.",
                "가까운 사람과의 갈등이 나를 힘들게 한다.",
                "먼저 사과하는 용기를 내보자. 별일 아닐 거야."
            )
        case 3:
            return (
                "출근하고 퇴근하고, 평소와 다름없는 하루였다.", 
                "특별한 일은 없었고 그냥 무덤덤하다. 지루하기도 하다.",
                "반복되는 일상이 안정감을 주지만 때로는 권태롭다.",
                "오늘 하루도 무사히 보낸 것에 감사하자."
            )
        case 4:
            return (
                "오랜만에 공원 산책을 다녀왔다.", 
                "상쾌하고 기분이 한결 가벼워졌다. 콧노래가 나온다.",
                "적당한 운동과 휴식이 나에게 에너지를 준다.",
                "가끔은 이렇게 여유를 즐기는 시간이 필요해."
            )
        case 5:
            return (
                "프로젝트가 성공적으로 끝났다! 칭찬도 받았다.", 
                "날아갈 것 같이 기쁘다. 무엇이든 할 수 있을 것 같다.",
                "노력한 만큼 결과가 나와서 성취감이 크다.",
                "정말 고생 많았어! 오늘은 스스로에게 큰 상을 주자."
            )
        default:
            return ("오늘 하루를 기록한다.", "그저 그런 하루.", "의미 없음", "파이팅")
        }
    }
}
