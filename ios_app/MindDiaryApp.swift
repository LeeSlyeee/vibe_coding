
import SwiftUI
import UserNotifications
import FirebaseCore
import FirebaseMessaging

// MARK: - DeepLink Manager (푸시 알림 딥링크 처리)
class DeepLinkManager: ObservableObject {
    static let shared = DeepLinkManager()
    @Published var pendingDeepLink: DeepLink?
    
    enum DeepLink {
        case weeklyLetter(letterId: Int?)
    }
}

@main
struct MindDiaryApp: App {
    // [Push Notification] APNs 등록을 위한 AppDelegate 연결
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    @StateObject private var authManager = AuthManager()
    @State private var showSplash = true
    
    var body: some Scene {
        WindowGroup {
            ZStack {
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
            .screenshotProtected(isProtected: false) // 스크린샷 방지 적용 (검은 화면 처리)
            .ignoresSafeArea() // [Fix] 전체 화면 꽉 차게 (스플래시 상하 여백 제거)
            .preferredColorScheme(.light) // Force Light Mode
            .onAppear {
                // 2. 스플래시 화면 제어 (최소 2초)
                Task {
                    // (A) 로고 감상을 위한 최소 대기 시간 (2초)
                    try? await Task.sleep(nanoseconds: 2 * 1_000_000_000)
                    
                    print("✅ Splash Time Completed. Dismising Splash.")
                    
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
                print("✅ 푸시 알림 권한 허용")
                DispatchQueue.main.async {
                    application.registerForRemoteNotifications()
                }
            } else {
                print("⚠️ 푸시 알림 권한 거부: \(error?.localizedDescription ?? "")")
            }
        }
        return true
    }

    // APNs 토큰을 Firebase에 전달 (Firebase가 FCM 토큰으로 변환)
    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        Messaging.messaging().apnsToken = deviceToken
        let hex = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        print("✅ APNs 디바이스 토큰: \(hex)")
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
                print("✅ APNs 토큰 서버 등록 완료")
            }
        }.resume()
    }

    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {
        print("❌ APNs 등록 실패: \(error.localizedDescription)")
    }

    // MARK: - MessagingDelegate (FCM 토큰 수신)
    
    func messaging(_ messaging: Messaging, didReceiveRegistrationToken fcmToken: String?) {
        guard let token = fcmToken else { return }
        print("✅ FCM 토큰 수신: \(token.prefix(30))...")
        
        // Firebase에서 APNs 토큰 직접 읽기
        if let apnsData = messaging.apnsToken {
            let hex = apnsData.map { String(format: "%02.2hhx", $0) }.joined()
            print("✅ APNs 토큰 확인: \(hex.prefix(20))...")
            UserDefaults.standard.set(hex, forKey: "apns_device_token")
        }
        
        // 1초 후 재시도 (APNs 토큰이 아직 없을 수 있음)
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
            if let apnsData = Messaging.messaging().apnsToken {
                let hex = apnsData.map { String(format: "%02.2hhx", $0) }.joined()
                UserDefaults.standard.set(hex, forKey: "apns_device_token")
                print("✅ APNs 토큰 (지연 확인): \(hex.prefix(20))...")
                self.sendAPNsTokenToServer(apnsToken: hex)
            } else {
                print("⚠️ APNs 토큰 없음 (시뮬레이터?)")
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
        print("📩 알림 탭: \(userInfo)")
        
        // 딥링크 처리: 주간 편지
        if let type = userInfo["type"] as? String, type == "weekly_letter" {
            let letterId = (userInfo["letter_id"] as? String).flatMap { Int($0) }
            DispatchQueue.main.async {
                DeepLinkManager.shared.pendingDeepLink = .weeklyLetter(letterId: letterId)
            }
            print("📮 딥링크: 주간 편지 열기 (letter_id=\(letterId ?? -1))")
        }
        
        completionHandler()
    }

    // MARK: - FCM 토큰을 서버에 등록
    
    private func registerFCMTokenToServer(token: String) {
        guard let authToken = UserDefaults.standard.string(forKey: "serverAuthToken"), !authToken.isEmpty else {
            print("⏳ FCM 토큰 등록 대기: 로그인 토큰 없음")
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
                    print("✅ FCM 토큰 서버 등록 완료")
                    UserDefaults.standard.removeObject(forKey: "pending_fcm_token")
                } else {
                    let respBody = data.flatMap { String(data: $0, encoding: .utf8) } ?? "no body"
                    print("❌ FCM 토큰 등록 실패: HTTP \(httpResponse.statusCode) | \(respBody)")
                }
            } else {
                print("❌ FCM 토큰 등록 네트워크 에러: \(error?.localizedDescription ?? "unknown")")
            }
        }.resume()
    }
}
