
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
        
        var id: String {
            switch self {
            case .shareAuth: return "shareAuth"
            case .sharedStats(let id, _): return "sharedStats_\(id)"
            case .weeklyLetter(let id): return "weeklyLetter_\(id ?? -1)"
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
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { granted, error in
            if granted {
                DispatchQueue.main.async {
                    application.registerForRemoteNotifications()
                }
            } else {
            }
        }
        return true
    }

    // APNs 토큰을 Firebase에 전달 (Firebase가 FCM 토큰으로 변환)
    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        Messaging.messaging().apnsToken = deviceToken
        let hex = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        UserDefaults.standard.set(hex, forKey: "apns_device_token")
        // APNs 토큰을 즉시 서버에 별도 전송
        sendAPNsTokenToServer(apnsToken: hex)
    }
    
    private func sendAPNsTokenToServer(apnsToken: String) {
        guard let authToken = UserDefaults.standard.string(forKey: "serverAuthToken"), !authToken.isEmpty else { return }
        var components = URLComponents(string: "https://217.142.253.35.nip.io/api/device/apns")
        components?.queryItems = [URLQueryItem(name: "jwt", value: authToken)]
        guard let url = components?.url else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        request.httpBody = try? JSONSerialization.data(withJSONObject: ["apns_token": apnsToken])
        URLSession.shared.dataTask(with: request) { _, response, _ in
            if let r = response as? HTTPURLResponse, r.statusCode == 200 {
            }
        }.resume()
    }

    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {
    }

    // MARK: - MessagingDelegate (FCM 토큰 수신)
    
    func messaging(_ messaging: Messaging, didReceiveRegistrationToken fcmToken: String?) {
        guard let token = fcmToken else { return }
        
        // Firebase에서 APNs 토큰 직접 읽기
        if let apnsData = messaging.apnsToken {
            let hex = apnsData.map { String(format: "%02.2hhx", $0) }.joined()
            UserDefaults.standard.set(hex, forKey: "apns_device_token")
        }
        
        // 1초 후 재시도 (APNs 토큰이 아직 없을 수 있음)
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
            if let apnsData = Messaging.messaging().apnsToken {
                let hex = apnsData.map { String(format: "%02.2hhx", $0) }.joined()
                UserDefaults.standard.set(hex, forKey: "apns_device_token")
                self.sendAPNsTokenToServer(apnsToken: hex)
            } else {
            }
        }
        
        registerFCMTokenToServer(token: token)
    }

    // MARK: - Notification Display (포그라운드에서도 알림 표시)
    
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        completionHandler([.banner, .list, .sound, .badge])
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        let userInfo = response.notification.request.content.userInfo
        
        if let type = userInfo["type"] as? String {
            // FCM/APNs 페이로드에서 String 또는 Int로 넘어올 수 있는 값을 안전하게 처리
            let extractInt: (String) -> Int? = { key in
                if let str = userInfo[key] as? String { return Int(str) }
                if let num = userInfo[key] as? Int { return num }
                return nil
            }
            
            if type == "weekly_letter" {
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
    
    private func registerFCMTokenToServer(token: String) {
        guard let authToken = UserDefaults.standard.string(forKey: "serverAuthToken"), !authToken.isEmpty else {
            UserDefaults.standard.set(token, forKey: "pending_fcm_token")
            return
        }
        
        var components = URLComponents(string: "https://217.142.253.35.nip.io/api/device/register")
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
                } else {
                    let respBody = data.flatMap { String(data: $0, encoding: .utf8) } ?? "no body"
                }
            } else {
            }
        }.resume()
    }
}
