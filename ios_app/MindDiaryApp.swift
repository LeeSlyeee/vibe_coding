
import SwiftUI
import UserNotifications
import FirebaseCore
import FirebaseMessaging

// MARK: - DeepLink Manager (푸시 알림 딥링크 풀스크린 라우터)
class DeepLinkManager: ObservableObject {
    static let shared = DeepLinkManager()
    
    enum ActiveScreen: Identifiable, Equatable {
        case shareAuth
        case sharedStats(targetId: String, targetName: String)
        case weeklyLetter(letterId: Int?)
        case safetyCheck(username: String)
        
        var id: String {
            switch self {
            case .shareAuth: return "shareAuth"
            case .sharedStats(let id, _): return "sharedStats_\(id)"
            case .weeklyLetter(let id): return "weeklyLetter_\(id ?? -1)"
            case .safetyCheck: return "safetyCheck"
            }
        }
        
        static func == (lhs: ActiveScreen, rhs: ActiveScreen) -> Bool {
            lhs.id == rhs.id
        }
    }
    
    @Published var activeScreen: ActiveScreen?
}

@main
struct MindDiaryApp: App {
    // [Push Notification] APNs 등록을 위한 AppDelegate 연결
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    @StateObject private var authManager = AuthManager()
    @State private var showSplash = true
    
    //  앱의 현재 상태(백그라운드/포그라운드) 추적
    @Environment(\.scenePhase) private var scenePhase
    
    var body: some Scene {
        WindowGroup {
            ZStack {
                Color.white.ignoresSafeArea(.all)
                
                if showSplash {
                    AppSplashView()
                        .transition(AnyTransition.opacity)
                        .zIndex(1)
                } else {
                    AppMainTabView()
                        .environmentObject(authManager)
                        .transition(AnyTransition.opacity)
                        .zIndex(0)
                }
            }
            .preferredColorScheme(.light) // Force Light Mode
            .onAppear {
                // 2. 스플래시 화면 제어 (최소 2초)
                Task {
                    // (A) 로고 감상을 위한 최소 대기 시간 (2초)
                    try? await Task.sleep(nanoseconds: 2 * 1_000_000_000)
                    
                    
                    // (C) 메인 화면 전환
                    await MainActor.run {
                        withAnimation(.easeOut(duration: 0.5)) {
                            self.showSplash = false
                        }
                    }
                }
                
                // 일기 알림: 앱 실행 시 랜덤 메시지로 재스케줄링
                DiaryReminderManager.refreshIfEnabled()
            }
        }
    }
}

// MARK: - Push Notification AppDelegate (Firebase Messaging)

class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate, MessagingDelegate {

    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        // Firebase 초기화
        FirebaseApp.configure()
        
        // Messaging delegate
        Messaging.messaging().delegate = self
        
        // Notification delegate
        UNUserNotificationCenter.current().delegate = self
        
        // [Safety Check] 안전 확인 알림 카테고리 등록 (반드시 requestAuthorization 전에!)
        let okAction = UNNotificationAction(
            identifier: "SAFETY_OK",
            title: "괜찮아요 👋",
            options: []
        )
        let helpAction = UNNotificationAction(
            identifier: "SAFETY_HELP",
            title: "도움이 필요해요 🆘",
            options: [.foreground]
        )
        let safetyCategory = UNNotificationCategory(
            identifier: "SAFETY_CHECK",
            actions: [okAction, helpAction],
            intentIdentifiers: [],
            options: []
        )
        UNUserNotificationCenter.current().setNotificationCategories([safetyCategory])
        print("🛡️ [Safety] SAFETY_CHECK 카테고리 등록 완료")
        
        // 알림 권한 요청 (카테고리 등록 후에 호출)
        print("📱 [Push] 알림 권한 요청 시작...")
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { granted, error in
            print("📱 [Push] 권한 결과: granted=\(granted), error=\(error?.localizedDescription ?? "없음")")
            if granted {
                DispatchQueue.main.async {
                    print("📱 [Push] registerForRemoteNotifications() 호출!")
                    application.registerForRemoteNotifications()
                }
            } else {
                print("📱 [Push] ⚠️ 알림 권한 거부됨 → APNs 등록 안 함")
            }
        }
        
        // 이미 권한이 있는 경우를 위해 현재 상태도 확인
        UNUserNotificationCenter.current().getNotificationSettings { settings in
            print("📱 [Push] 현재 알림 상태: \(settings.authorizationStatus.rawValue) (0=notDetermined, 1=denied, 2=authorized, 3=provisional)")
            if settings.authorizationStatus == .authorized {
                DispatchQueue.main.async {
                    print("📱 [Push] 이미 권한 있음 → registerForRemoteNotifications() 재호출!")
                    application.registerForRemoteNotifications()
                }
            }
        }
        
        return true
    }

    // APNs 토큰을 Firebase에 전달 (Firebase가 FCM 토큰으로 변환)
    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        Messaging.messaging().apnsToken = deviceToken
        let hex = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        print("🍏 [APNs] 디바이스 토큰 발급됨: \(hex)")
        UserDefaults.standard.set(hex, forKey: "apns_device_token")
        // APNs 토큰을 즉시 서버에 별도 전송
        sendAPNsTokenToServer(apnsToken: hex)
    }
    
    private func sendAPNsTokenToServer(apnsToken: String) {
        guard let authToken = UserDefaults.standard.string(forKey: "serverAuthToken"), !authToken.isEmpty else {
            print("🍏 [APNs] ⚠️ serverAuthToken 없음 → APNs 토큰 서버 전송 건너뜀")
            return
        }
        print("🍏 [APNs] 서버에 토큰 전송 시도: \(apnsToken.prefix(20))...")
        var components = URLComponents(string: ServerConfig.apiBase + "/device/apns")
        components?.queryItems = [URLQueryItem(name: "jwt", value: authToken)]
        guard let url = components?.url else {
            print("🍏 [APNs] ❌ URL 생성 실패")
            return
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        request.httpBody = try? JSONSerialization.data(withJSONObject: ["apns_token": apnsToken])
        URLSession.shared.dataTask(with: request) { _, response, _ in
            if let r = response as? HTTPURLResponse {
                print("🍏 [APNs] 서버 응답: HTTP \(r.statusCode)")
            } else {
                print("🍏 [APNs] ❌ 서버 응답 없음")
            }
        }.resume()
    }

    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {
        print("🍏 [APNs] ❌ 푸시 등록 실패: \(error.localizedDescription)")
    }

    // MARK: - MessagingDelegate (FCM 토큰 수신)
    
    func messaging(_ messaging: Messaging, didReceiveRegistrationToken fcmToken: String?) {
        guard let token = fcmToken else { return }
        print("🔥 [FCM] 토큰 수신: \(token.prefix(30))...")
        
        // Firebase에서 APNs 토큰 직접 읽기
        if let apnsData = messaging.apnsToken {
            let hex = apnsData.map { String(format: "%02.2hhx", $0) }.joined()
            print("🔥 [FCM] APNs 토큰도 함께 확인됨: \(hex.prefix(20))...")
            UserDefaults.standard.set(hex, forKey: "apns_device_token")
        } else {
            print("🔥 [FCM] ⚠️ APNs 토큰 아직 없음 (2초 후 재시도)")
        }
        
        // 2초 후 재시도 (APNs 토큰이 아직 없을 수 있음)
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
            if let apnsData = Messaging.messaging().apnsToken {
                let hex = apnsData.map { String(format: "%02.2hhx", $0) }.joined()
                print("🔥 [FCM] 2초 후 APNs 토큰 확인됨: \(hex.prefix(20))...")
                UserDefaults.standard.set(hex, forKey: "apns_device_token")
                self.sendAPNsTokenToServer(apnsToken: hex)
            } else {
                print("🔥 [FCM] ⚠️ 2초 후에도 APNs 토큰 없음!")
            }
        }
        
        AppDelegate.registerFCMTokenToServer(token: token)
    }

    // MARK: - Notification Display (포그라운드에서도 알림 표시)
    
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        let catId = notification.request.content.categoryIdentifier
        print("🔔 [Push 수신] categoryIdentifier = '\(catId)'")
        print("🔔 [Push 수신] userInfo = \(notification.request.content.userInfo)")
        
        // 등록된 카테고리 확인
        center.getNotificationCategories { categories in
            let names = categories.map { $0.identifier }
            print("🔔 [등록된 카테고리 목록] \(names)")
        }
        
        completionHandler([.banner, .list, .sound, .badge])
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        let userInfo = response.notification.request.content.userInfo
        
        // [Safety Check] 안전 확인 액션 버튼 처리
        let actionId = response.actionIdentifier
        if actionId == "SAFETY_OK" || actionId == "SAFETY_HELP" {
            let status = (actionId == "SAFETY_OK") ? "ok" : "need_help"
            let username = userInfo["username"] as? String
                ?? UserDefaults.standard.string(forKey: "app_username") ?? ""
            sendSafetyConfirmToServer(username: username, status: status)
            
            // UI 피드백 표시
            DispatchQueue.main.async {
                guard let scene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
                      let rootVC = scene.windows.first?.rootViewController else { return }
                
                // 최상단 ViewController 찾기
                var topVC = rootVC
                while let presented = topVC.presentedViewController {
                    topVC = presented
                }
                
                if status == "need_help" {
                    let alert = UIAlertController(
                        title: "🆘 도움 요청이 전달되었습니다",
                        message: "연결된 보호자에게 긴급 알림이 발송되었습니다.\n\n즉시 도움이 필요하시면 아래 번호로 연락해주세요.\n\n🔴 자살예방상담전화: 1393\n🔴 정신건강위기상담전화: 1577-0199\n🔴 긴급신고: 112",
                        preferredStyle: .alert
                    )
                    alert.addAction(UIAlertAction(title: "확인", style: .default))
                    alert.addAction(UIAlertAction(title: "1393 전화걸기", style: .destructive) { _ in
                        if let url = URL(string: "tel://1393") {
                            UIApplication.shared.open(url)
                        }
                    })
                    topVC.present(alert, animated: true)
                } else {
                    let alert = UIAlertController(
                        title: "✅ 안전 확인 완료",
                        message: "괜찮다는 응답이 전달되었습니다.\n마음온이 항상 곁에 있을게요 💛",
                        preferredStyle: .alert
                    )
                    alert.addAction(UIAlertAction(title: "확인", style: .default))
                    topVC.present(alert, animated: true)
                }
            }
            
            completionHandler()
            return
        }
        
        if let type = userInfo["type"] as? String {
            // FCM/APNs 페이로드에서 String 또는 Int로 넘어올 수 있는 값을 안전하게 처리
            let extractInt: (String) -> Int? = { key in
                if let str = userInfo[key] as? String { return Int(str) }
                if let num = userInfo[key] as? Int { return num }
                return nil
            }
            
            // [Safety Check] 알림 자체를 탭한 경우 → 전용 안전확인 화면 열기
            if type == "safety_check" {
                let username = userInfo["username"] as? String
                    ?? UserDefaults.standard.string(forKey: "app_username") ?? ""
                DispatchQueue.main.async {
                    DeepLinkManager.shared.activeScreen = nil
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                        DeepLinkManager.shared.activeScreen = .safetyCheck(username: username)
                    }
                }
            } else if type == "weekly_letter" {
                let letterId = extractInt("letter_id")
                DispatchQueue.main.async {
                    DeepLinkManager.shared.activeScreen = nil
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                        DeepLinkManager.shared.activeScreen = .weeklyLetter(letterId: letterId)
                    }
                }
            } else if type == "mood_alert" || type == "kick_flag_alert" || type == "ai_report_alert" || type == "crisis_alert" {
                let sharerId = extractInt("sharer_id")
                DispatchQueue.main.async {
                    DeepLinkManager.shared.activeScreen = nil
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                        if let sid = sharerId {
                            let sidStr = String(sid)
                            var sName = "내담자"
                            if let user = ShareManager.shared.connectedUsers.first(where: { $0.id == sidStr }) {
                                sName = user.name
                            }
                            DeepLinkManager.shared.activeScreen = .sharedStats(targetId: sidStr, targetName: sName)
                        } else {
                            DeepLinkManager.shared.activeScreen = .shareAuth
                        }
                    }
                }
            }
        }
        
        completionHandler()
    }

    // MARK: - FCM 토큰을 서버에 등록
    
    /// 로그인 후 호출: pending FCM/APNs 토큰을 즉시 서버에 전송
    static func flushPendingTokens() {
        guard let authToken = UserDefaults.standard.string(forKey: "serverAuthToken"), !authToken.isEmpty else {
            print("🔥 [FCM] flushPendingTokens: serverAuthToken 없음 → 건너뜀")
            return
        }
        
        // 1. Pending FCM 토큰 처리
        if let pendingFCM = UserDefaults.standard.string(forKey: "pending_fcm_token"), !pendingFCM.isEmpty {
            print("🔥 [FCM] 📤 pending FCM 토큰 서버 전송: \(pendingFCM.prefix(20))...")
            AppDelegate.registerFCMTokenToServer(token: pendingFCM)
        }
        
        // 2. APNs 토큰도 별도 전송 (FCM 토큰 없이 APNs만 있을 수 있음)
        if let apnsToken = UserDefaults.standard.string(forKey: "apns_device_token"), !apnsToken.isEmpty {
            print("🍏 [APNs] 📤 로그인 후 APNs 토큰 재전송: \(apnsToken.prefix(20))...")
            // APNs 토큰을 별도 엔드포인트로도 전송
            var components = URLComponents(string: ServerConfig.apiBase + "/device/apns")
            components?.queryItems = [URLQueryItem(name: "jwt", value: authToken)]
            guard let url = components?.url else { return }
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
            request.httpBody = try? JSONSerialization.data(withJSONObject: ["apns_token": apnsToken])
            URLSession.shared.dataTask(with: request) { _, response, _ in
                if let r = response as? HTTPURLResponse {
                    print("🍏 [APNs] 로그인 후 재전송 응답: HTTP \(r.statusCode)")
                }
            }.resume()
        }
        
        // 3. 현재 FCM 토큰도 강제 재전송 (pending이 아니더라도)
        if let currentFCM = Messaging.messaging().fcmToken {
            print("🔥 [FCM] 📤 현재 FCM 토큰 강제 재전송: \(currentFCM.prefix(20))...")
            AppDelegate.registerFCMTokenToServer(token: currentFCM)
        }
    }
    
    static func registerFCMTokenToServer(token: String) {
        guard let authToken = UserDefaults.standard.string(forKey: "serverAuthToken"), !authToken.isEmpty else {
            UserDefaults.standard.set(token, forKey: "pending_fcm_token")
            print("🔥 [FCM] ⏳ serverAuthToken 없음 → pending에 저장: \(token.prefix(20))...")
            return
        }
        
        var components = URLComponents(string: ServerConfig.apiBase + "/device/register")
        components?.queryItems = [URLQueryItem(name: "jwt", value: authToken)]
        guard let url = components?.url else { return }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")

        let apnsToken = UserDefaults.standard.string(forKey: "apns_device_token") ?? ""
        let body: [String: String] = ["fcm_token": token, "platform": "ios", "apns_token": apnsToken]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        URLSession.shared.dataTask(with: request) { data, response, error in
            if let httpResponse = response as? HTTPURLResponse {
                if httpResponse.statusCode == 200 {
                    UserDefaults.standard.removeObject(forKey: "pending_fcm_token")
                    print("🔥 [FCM] ✅ 서버 등록 성공! (HTTP 200)")
                } else {
                    let respBody = data.flatMap { String(data: $0, encoding: .utf8) } ?? "no body"
                    print("🔥 [FCM] ❌ 서버 등록 실패: HTTP \(httpResponse.statusCode) - \(respBody)")
                }
            } else {
                print("🔥 [FCM] ❌ 서버 응답 없음: \(error?.localizedDescription ?? "unknown")")
            }
        }.resume()
    }
    
    // MARK: - 안전 확인 서버 전송
    
    private func sendSafetyConfirmToServer(username: String, status: String) {
        guard !username.isEmpty else {
            print("🛡️ [Safety] username 없음 → 전송 건너뜀")
            return
        }
        
        guard let url = URL(string: ServerConfig.apiBase + "/safety/quick-confirm") else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: [
            "username": username,
            "status": status
        ])
        
        URLSession.shared.dataTask(with: request) { _, response, error in
            if let r = response as? HTTPURLResponse {
                print("🛡️ [Safety] 생존 확인 응답 전송 완료: HTTP \(r.statusCode), status=\(status)")
            } else {
                print("🛡️ [Safety] ❌ 전송 실패: \(error?.localizedDescription ?? "unknown")")
            }
        }.resume()
    }
}
