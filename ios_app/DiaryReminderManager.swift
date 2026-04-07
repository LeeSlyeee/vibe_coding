import Foundation
import UserNotifications

/// 매일 일기 작성 알림을 관리하는 싱글턴 매니저
/// iOS 로컬 알림(UNUserNotificationCenter)을 사용하여 서버 없이 동작
struct DiaryReminderManager {
    
    static let reminderID = "daily_diary_reminder"
    
    static let messages: [(String, String)] = [
        ("✍️ 오늘 하루는 어땠나요?", "잠깐 멈추고, 오늘의 마음을 기록해보세요."),
        ("🌙 하루를 마무리할 시간이에요", "오늘의 감정을 일기에 담아보세요."),
        ("💭 오늘 하루, 어떤 감정이 있었나요?", "마음온에 기록하면 마음이 한결 가벼워져요."),
        ("📝 일기 쓸 시간이에요!", "오늘 하루의 이야기를 들려주세요."),
        ("🌿 잠시 나를 돌아보는 시간", "오늘의 마음을 글로 남겨보세요."),
        ("🫧 오늘의 마음, 기록해볼까요?", "작은 기록이 큰 변화를 만들어요."),
        ("🌈 하루 한 줄, 마음 돌봄", "짧게라도 괜찮아요. 오늘의 감정을 적어보세요."),
    ]
    
    /// 알림 예약 (매일 반복)
    static func schedule(hour: Int, minute: Int) {
        let center = UNUserNotificationCenter.current()
        
        // 기존 알림 제거
        center.removePendingNotificationRequests(withIdentifiers: [reminderID])
        
        // 랜덤 메시지
        let msg = messages.randomElement() ?? messages[0]
        
        let content = UNMutableNotificationContent()
        content.title = msg.0
        content.body = msg.1
        content.sound = .default
        content.badge = 1
        
        // 매일 반복 트리거
        var dateComponents = DateComponents()
        dateComponents.hour = hour
        dateComponents.minute = minute
        let trigger = UNCalendarNotificationTrigger(dateMatching: dateComponents, repeats: true)
        
        let request = UNNotificationRequest(
            identifier: reminderID,
            content: content,
            trigger: trigger
        )
        
        center.add(request) { error in
            if let error = error {
                print("❌ 일기 알림 예약 실패: \(error.localizedDescription)")
            } else {
                let timeStr = String(format: "%02d:%02d", hour, minute)
                print("✅ 일기 알림 예약 완료: 매일 \(timeStr)")
            }
        }
    }
    
    /// 알림 해제
    static func cancel() {
        UNUserNotificationCenter.current().removePendingNotificationRequests(
            withIdentifiers: [reminderID]
        )
        print("🔕 일기 알림 해제됨")
    }
    
    /// 앱 실행 시 호출: 알림이 켜져 있으면 랜덤 메시지로 재스케줄링
    static func refreshIfEnabled() {
        let isEnabled = UserDefaults.standard.bool(forKey: "isDiaryReminderOn")
        guard isEnabled else { return }
        
        let hour = UserDefaults.standard.integer(forKey: "diaryReminderHour")
        let minute = UserDefaults.standard.integer(forKey: "diaryReminderMinute")
        
        // 기본값 체크 (둘 다 0이면 미설정 → 21:00으로)
        let finalHour = (hour == 0 && minute == 0 && !UserDefaults.standard.bool(forKey: "diaryReminderTimeSet")) ? 21 : hour
        
        schedule(hour: finalHour, minute: minute)
    }
}
