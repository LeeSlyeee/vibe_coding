
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
    
    // [DeepLink] 뷰 렌더링에 직접 쓰일 안전한 로컬 상태
    @State private var activeFullScreen: DeepLinkManager.ActiveScreen?
    @State private var pendingFullScreen: DeepLinkManager.ActiveScreen?
    
    // 🔥 앱의 현재 상태(백그라운드/포그라운드) 추적
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
                
                // [DeepLink Routing Anchor] 완전히 격리된 투명 뷰 위에서 라우팅 수행 (트리 충돌 방지)
                Color.clear
                    .frame(width: 0, height: 0)
                    .zIndex(999)
                    .fullScreenCover(item: Binding(
                        get: { self.activeFullScreen },
                        set: { newValue in
                            self.activeFullScreen = newValue
                            DeepLinkManager.shared.activeScreen = newValue
                        }
                    )) { item in
                        switch item {
                        case .shareAuth:
                            NavigationView {
                                AppShareView()
                                    .navigationBarItems(leading: Button("닫기") {
                                        self.activeFullScreen = nil
                                        DeepLinkManager.shared.activeScreen = nil
                                    })
                            }
                        case .sharedStats(let targetId, let targetName):
                            NavigationView {
                                SharedStatsView(targetId: targetId, targetName: targetName)
                                    .navigationBarItems(leading: Button("닫기") {
                                        self.activeFullScreen = nil
                                        DeepLinkManager.shared.activeScreen = nil
                                    })
                            }
                        case .weeklyLetter(let targetId):
                            NavigationView {
                                WeeklyLetterView(targetLetterId: targetId)
                                    .navigationBarItems(leading: Button(action: {
                                        self.activeFullScreen = nil
                                        DeepLinkManager.shared.activeScreen = nil
                                    }) {
                                        HStack(spacing: 4) {
                                            Image(systemName: "chevron.left")
                                            Text("닫기")
                                        }.foregroundColor(.blue)
                                    })
                            }
                        }
                    }
            }
            .preferredColorScheme(.light) // Force Light Mode
            .onReceive(DeepLinkManager.shared.$activeScreen) { newScreen in
                print("🔄 [DeepLink] 전역 상태 변경 감지: \(String(describing: newScreen))")
                guard let newScreen = newScreen else {
                    self.activeFullScreen = nil
                    return
                }
                
                // 앱이 스플래시 중이거나 백그라운드일 때는 즉시 띄우지 않고 예약만 함
                if showSplash || scenePhase != .active {
                    print("🔄 [DeepLink] 화면 준비 안 됨 (splash: \(showSplash), phase: \(scenePhase)). 대기열에 등록")
                    self.pendingFullScreen = newScreen
                } else {
                    print("🔄 [DeepLink] 포그라운드 상태. 0.3초 대기 후 호출 (렌더 무시 방어)")
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                        self.activeFullScreen = newScreen
                    }
                }
            }
            .onChange(of: scenePhase) { newPhase in
                if newPhase == .active && !showSplash {
                    if let pending = self.pendingFullScreen {
                        print("⏳ [DeepLink] 앱 활성화(Active)됨. 대기중인 라우팅 실행: \(pending)")
                        // 화면 전환 애니메이션 및 iOS 렌더링 큐 안정화 고려해 0.6초 딜레이
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) {
                            self.activeFullScreen = pending
                            self.pendingFullScreen = nil
                        }
                    }
                }
            }
            .onChange(of: showSplash) { isSplash in
                if !isSplash {
                    // 콜드스타트: 스플래시 종료 직후 딥링크가 대기 중이라면 애니메이션 후 라우팅
                    if let pending = self.pendingFullScreen ?? DeepLinkManager.shared.activeScreen {
                        print("⏳ [DeepLink] 스플래시 종료, 대기중인 라우팅 실행: \(pending)")
                        // 스플래시 종료 애니메이션(0.5초) 후 충분한 여유(1.0초) 확보
                        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                            self.activeFullScreen = pending
                            self.pendingFullScreen = nil
                        }
                    }
                }
            }
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
                    DeepLinkManager.shared.activeScreen = .weeklyLetter(letterId: letterId)
                }
                print("📮 딥링크: 주간 편지 열기 (letter_id=\(letterId ?? -1))")
            } else if type == "mood_alert" || type == "kick_flag_alert" || type == "ai_report_alert" || type == "crisis_alert" {
                let sharerId = extractInt("sharer_id")
                DispatchQueue.main.async {
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
                print("📮 딥링크: 알림 (type=\(type), sharer_id=\(sharerId ?? -1))")
            }
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
