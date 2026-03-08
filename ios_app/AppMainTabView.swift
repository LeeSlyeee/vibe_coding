
import SwiftUI

struct AppMainTabView: View {
    @EnvironmentObject var authManager: AuthManager
    @Environment(\.scenePhase) var scenePhase // [New] Detect App Background/Foreground
    @StateObject private var networkMonitor = NetworkMonitor()
    #if os(iOS)
    @StateObject private var keyboardObserver = KeyboardObserver() // [Keyboard Fix] Direct observation
    #endif
    @State private var showAssessment = false
    @State private var selection = 0
    @State private var isTabBarHidden = false // [New] TabBar Visibility Control
    @State private var showToast = false // [New] AI Loaded Toast
    @State private var showBirthdayToast = false // [New] Birthday Toast State (Me)
    @State private var showFriendBirthdayToast = false // [New] Friend Birthday Toast (Others)
    
    // [New] Friends List with D-Day
    // struct because Tuple is not Equatable for @State strictly without wrappers, 
    // but array of tuples is okay for simple assignment. 
    // Or better, let's use a simple struct for state.
    struct BirthdayInfo: Identifiable {
        let id = UUID()
        let name: String
        let dDay: Int
    }
    @State private var upcomingBirthdays: [BirthdayInfo] = []
    
    // [Keyboard Fix] 탭바 표시 여부: KeyboardObserver가 직접 감지 (Notification 불필요)
    private var shouldShowTabBar: Bool {
        #if os(iOS)
        return !keyboardObserver.isKeyboardVisible
        #else
        return true
        #endif
    }
    
    var body: some View {
        if !authManager.isAuthenticated {
            AppLoginView()
        } else {
            ZStack(alignment: .bottom) {
                Color.clear.frame(height: 0)
                    .onAppear {
                        #if os(iOS)
                        dismissKeyboard()
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                            dismissKeyboard()
                        }
                        #endif
                    }
                // Main Content Area
                MoodCalendarView()
                    .opacity(selection == 0 ? 1 : 0)
                    .allowsHitTesting(selection == 0)
                    
                AppStatsView()
                    .opacity(selection == 1 ? 1 : 0)
                    .allowsHitTesting(selection == 1)
                    
                AppChatView()
                    .opacity(selection == 2 ? 1 : 0)
                    .allowsHitTesting(selection == 2)
                    
                AppEmergencyView()
                    .opacity(selection == 3 ? 1 : 0)
                    .allowsHitTesting(selection == 3)
                
                // Custom Tab Bar
                // [Keyboard Fix] 키보드가 올라오면 탭바 숨김, 내려오면 탭바 표시
                if shouldShowTabBar {
                    VStack(spacing: 0) {
                        Divider()
                            .background(Color.gray.opacity(0.1))
                        
                        HStack(spacing: 0) {
                            TabButton(index: 0, title: "캘린더", image: "tab_calendar", systemIcon: "calendar", selection: $selection)
                            TabButton(index: 1, title: "분석", image: "tab_stats", systemIcon: "chart.bar.fill", selection: $selection)
                            TabButton(index: 2, title: "한마디", image: "tab_chat", systemIcon: "message.fill", selection: $selection)
                            TabButton(index: 3, title: "긴급", image: "tab_emergency", systemIcon: "exclamationmark.triangle.fill", selection: $selection)
                        }
                        .padding(.top, 10)
                        .padding(.bottom, 20)
                        .background(Color.white)
                        .shadow(color: Color.black.opacity(0.05), radius: 10, y: -5)
                    }
                    .transition(.move(edge: .bottom).combined(with: .opacity))
                }
                
                // [New] AI Loaded Toast (Floating above TabBar)
                if showToast {
                    VStack {
                        Spacer()
                        HStack(spacing: 8) {
                            Image(systemName: "cpu.fill")
                            Text("AI가 준비되었습니다!")
                        }
                        .font(.caption)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 10)
                        .background(Color.black.opacity(0.7))
                        .foregroundColor(.white)
                        .cornerRadius(20)
                        .shadow(radius: 5)
                        .padding(.bottom, isTabBarHidden ? 40 : 100) // Adjust position
                    }
                    .transition(.opacity.combined(with: .move(edge: .bottom)))
                    .zIndex(100) // Always on top
                }
                
                // [New] Birthday Toast (More Fancy)
                if showBirthdayToast {
                     ZStack {
                         Color.black.opacity(0.4).edgesIgnoringSafeArea(.all)
                         
                         VStack(spacing: 20) {
                             Text("🎂")
                                 .font(.system(size: 80))
                                 .padding(.bottom, -10)
                             
                             Text("생일 축하해!!")
                                 .font(.largeTitle)
                                 .fontWeight(.heavy)
                                 .foregroundColor(.pink)
                             
                             Text("오늘 하루 세상에서 가장 행복한 사람이 되길 바랄게! 🎉")
                                 .font(.body)
                                 .fontWeight(.bold)
                                 .foregroundColor(.white)
                                 .multilineTextAlignment(.center)
                                 .padding(.horizontal)
                             
                             Button(action: {
                                 withAnimation { showBirthdayToast = false }
                             }) {
                                 Text("고마워! 😍")
                                     .fontWeight(.bold)
                                     .padding(.horizontal, 30)
                                     .padding(.vertical, 12)
                                     .background(Color.white)
                                     .foregroundColor(.pink)
                                     .cornerRadius(20)
                             }
                         }
                         .padding(40)
                         .background(
                            RoundedRectangle(cornerRadius: 25)
                                .fill(LinearGradient(gradient: Gradient(colors: [Color.purple, Color.blue]), startPoint: .topLeading, endPoint: .bottomTrailing))
                                .shadow(radius: 20)
                         )
                         .padding(30)
                     }
                     .zIndex(200) // Top Priority
                     .transition(.scale)
                }
                
                // [New] Friend Birthday Toast (Different Style)
                if showFriendBirthdayToast && !upcomingBirthdays.isEmpty {
                     ZStack {
                         Color.black.opacity(0.4).edgesIgnoringSafeArea(.all)
                         
                         VStack(spacing: 15) {
                             Text("🎉")
                                 .font(.system(size: 60))
                                 .padding(.bottom, -5)
                             
                             Text("챙겨주실 생일이 있어요!")
                                 .font(.title2)
                                 .fontWeight(.bold)
                                 .foregroundColor(.white)
                             
                             // List of Birthdays
                             VStack(spacing: 8) {
                                 ForEach(upcomingBirthdays) { info in
                                     HStack {
                                         Text(info.name)
                                             .font(.title3)
                                             .fontWeight(.bold)
                                             .foregroundColor(.yellow)
                                         
                                         if info.dDay == 0 {
                                             Text("오늘 생일! 🎂")
                                                 .font(.headline)
                                                 .fontWeight(.heavy)
                                                 .foregroundColor(.white)
                                                 .padding(.horizontal, 8)
                                                 .padding(.vertical, 4)
                                                 .background(Color.red)
                                                 .cornerRadius(10)
                                         } else {
                                             Text("D-\(info.dDay)")
                                                 .font(.headline)
                                                 .fontWeight(.bold)
                                                 .foregroundColor(.white)
                                                 .padding(.horizontal, 8)
                                                 .padding(.vertical, 4)
                                                 .background(Color.blue.opacity(0.8))
                                                 .cornerRadius(10)
                                         }
                                     }
                                 }
                             }
                             .padding(.vertical, 5)
                             
                             Text("따뜻한 축하 메시지 준비해볼까요?")
                                 .font(.body)
                                 .foregroundColor(.white.opacity(0.9))
                                 .multilineTextAlignment(.center)
                             
                             Button(action: {
                                 withAnimation { showFriendBirthdayToast = false }
                             }) {
                                 Text("확인했어요! 💌")
                                     .fontWeight(.bold)
                                     .padding(.horizontal, 24)
                                     .padding(.vertical, 10)
                                     .background(Color.white)
                                     .foregroundColor(.orange)
                                     .cornerRadius(15)
                             }
                         }
                         .padding(30)
                         .background(
                            RoundedRectangle(cornerRadius: 20)
                                .fill(LinearGradient(gradient: Gradient(colors: [Color.orange, Color.pink]), startPoint: .topLeading, endPoint: .bottomTrailing))
                                .shadow(radius: 15)
                         )
                         .padding(40)
                     }
                     .zIndex(190) // Slightly lower than My Birthday
                     .transition(.scale)
                }
            }
            .edgesIgnoringSafeArea(.bottom)
            #if os(iOS)
            .environmentObject(keyboardObserver) // [Keyboard Fix] 하위 뷰에 단일 인스턴스 공유
            .fullScreenCover(isPresented: $showAssessment) {
                AppAssessmentView()
                    .onDisappear {
                        UserDefaults.standard.set(true, forKey: "hasCompletedAssessment")
                    }
            }
            #else
            .sheet(isPresented: $showAssessment) {
                AppAssessmentView()
                    .onDisappear {
                        UserDefaults.standard.set(true, forKey: "hasCompletedAssessment")
                    }
            }
            #endif
            .onAppear {
                checkAssessmentStatus()
                
                if authManager.isAuthenticated {
                    LocalDataManager.shared.syncWithServer()
                    
                    // [New] Sync Friends & Check Birthdays
                    DispatchQueue.global().async {
                        let sm = ShareManager.shared
                        // Refresh both lists first
                        
                        sm.fetchList(role: "viewer") // My Patients (Sharers)
                        // fetchList is async but logic inside updates @Published on main. 
                        // Wait slightly or just assume next launch picks it up. 
                        // Actually, let's wait a bit or use completion handler if modified. 
                        // Since fetchList doesn't yield completion here easily without modification,
                        // We will just do a delayed check on Main thread.
                        
                        sm.fetchList(role: "sharer") // My Guardians (Viewers)
                        
                        // Check after a delay to allow fetch to complete
                        DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
                            let friends = sm.checkFriendBirthdays()
                            // Map Tuple to Struct
                            let infos = friends.map { BirthdayInfo(name: $0.name, dDay: $0.dDay) }
                            
                            if !infos.isEmpty {
                                self.upcomingBirthdays = infos
                                withAnimation { self.showFriendBirthdayToast = true }
                            }
                        }
                    }
                }
                
                // Tab Switching Observer
                NotificationCenter.default.addObserver(forName: NSNotification.Name("SwitchToChatTab"), object: nil, queue: .main) { _ in
                    self.selection = 2
                }
                
                // [Removed] HideTabBar/ShowTabBar Notification 방식 제거
                // KeyboardObserver가 shouldShowTabBar에서 직접 감지하므로 Notification 불필요
                
                // [New] Safe Loading (10s Delay)
                DispatchQueue.main.asyncAfter(deadline: .now() + 10.0) {
                    print("🚀 [SmartLoad] App stabilized (10s). Pre-loading Local LLM...")
                    Task {
                        await LLMService.shared.loadModel()
                    }
                }
                
                // [New] Toast Trigger
                NotificationCenter.default.addObserver(forName: NSNotification.Name("AIModelLoaded"), object: nil, queue: .main) { _ in
                    withAnimation { self.showToast = true }
                    // Auto Hide after 3s
                    DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
                        withAnimation { self.showToast = false }
                }
                }
                
                // [New] Birthday Check
                DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                    if let bString = authManager.birthDate {
                        let f = DateFormatter()
                        f.dateFormat = "yyyy-MM-dd"
                        if let date = f.date(from: bString) {
                            let cal = Calendar.current
                            let today = Date()
                            
                            let tM = cal.component(.month, from: today)
                            let tD = cal.component(.day, from: today)
                            let bM = cal.component(.month, from: date)
                            let bD = cal.component(.day, from: date)
                            
                            if tM == bM && tD == bD {
                                withAnimation { self.showBirthdayToast = true }
                            }
                        }
                    }
                }
            }
            .onChange(of: scenePhase) { newPhase in
                if newPhase == .active && authManager.isAuthenticated {
                    let uid = UserDefaults.standard.string(forKey: "userId") ?? "N/A"
                    let uname = UserDefaults.standard.string(forKey: "authUsername") ?? "N/A"
                    print("📱 [App] Scene Active. Auth Status: userId=\(uid), username=\(uname)")
                    
                    // [Step 1] Verify Login Integrity First (Single Source of Truth)
                    if let username = authManager.username, !username.isEmpty {
                        
                        // [Step 2] Valid Auth -> Proceed to Sync
                        print("✅ [App] Auth Valid (User: \(username)). Triggering Sync.")
                        LocalDataManager.shared.syncWithServer()
                        
                    } else {
                        // [Step 1-Fail] Zombie State -> Recover First, Then Sync
                        print("🚑 [App] Auth Incomplete (Zombie State). Recovering User Info...")
                        
                        APIService.shared.syncUserInfo { success in
                            if success, let name = UserDefaults.standard.string(forKey: "userId") {
                                DispatchQueue.main.async {
                                    authManager.username = name
                                    // No need to set "app_username" anymore
                                    print("✅ [App] Recovery Success! User: \(name). Now Syncing...")
                                    
                                    // [Step 2-Delayed] Now it's safe to sync
                                    LocalDataManager.shared.syncWithServer(force: true)
                                }
                            } else {
                                print("❌ [App] Recovery Failed. Please Re-login.")
                            }
                        }
                    }
                }
            }
        }
    }

    // MARK: - Tab Button Component
    struct TabButton: View {
        let index: Int
        let title: String
        let image: String // Not used anymore
        let systemIcon: String
        @Binding var selection: Int
        
        var isSelected: Bool { selection == index }
        var isEmergency: Bool { index == 3 }
        
        var body: some View {
            Button(action: {
                withAnimation(.easeInOut(duration: 0.1)) {
                    selection = index
                }
                // [Auto-Sync] 캘린더 탭 진입 시 데이터 최신화 (새로고침 부재 대응)
                if index == 0 {
                    print("🔄 [Tab] Switched to Calendar. Triggering Sync...")
                    LocalDataManager.shared.syncWithServer()
                }
            }) {
                VStack(spacing: 4) {
                    // 시스템 아이콘 사용
                    Image(systemName: systemIcon)
                        .resizable()
                        .renderingMode(.template)
                        .scaledToFit()
                        .frame(width: 24, height: 24)
                        .foregroundColor(iconColor)
                    
                    Text(title)
                        .font(.caption)
                        .fontWeight(isSelected ? .bold : .regular)
                        .foregroundColor(textColor)
                }
                // .frame(maxWidth: .infinity) // Moved to outside of Label
            }
            .frame(maxWidth: .infinity) // Button 자체가 1/N 너비를 차지하도록 설정
            .contentShape(Rectangle()) // 빈 공간도 터치 가능하도록 설정
        }
        
        // 긴급 버튼은 붉은색, 나머지는 흑백/회색
        var iconColor: Color {
            if isEmergency {
                return isSelected ? .red : .red.opacity(0.6)
            } else {
                return isSelected ? .black : Color.gray.opacity(0.5)
            }
        }
        
        var textColor: Color {
            if isEmergency {
                return isSelected ? .red : .gray
            } else {
                return isSelected ? .black : .gray
            }
        }
    }
    
    // [New] Profile Image Cache
    private var profileImageCache: [String: UIImage] = [:]
    
    // [DeepLink] Share Screen State
    @State private var showShareScreenFromDeepLink = false
    
    init() {
        let appearance = UITabBarAppearance()
        appearance.configureWithOpaqueBackground()
        appearance.backgroundColor = .white
        UITabBar.appearance().standardAppearance = appearance
        UITabBar.appearance().scrollEdgeAppearance = appearance
    }
    
    private func fetchAIStatus() {
        APIService.shared.fetchDiaries { diaries in
            DispatchQueue.main.async {
                if let diaries = diaries, !diaries.isEmpty {
                    self.showToast = true
                    DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
                        withAnimation { self.showToast = false }
                    }
                }
            }
        }
    }
    
    func checkAssessmentStatus() {
        print("🛑 [App] Automatic Assessment disabled by User Request.")
        return
    }
    
    func callNumber(_ number: String) {
        let cleanNumber = number.components(separatedBy: CharacterSet.decimalDigits.inverted).joined()
        guard let url = URL(string: "tel://\(cleanNumber)") else { return }
        #if os(iOS)
        UIApplication.shared.open(url)
        #elseif os(macOS)
        NSWorkspace.shared.open(url)
        #endif
    }
}

// [DeepLink] Modifier for AppMainTabView to keep body clean
extension AppMainTabView {
    var deepLinkHandledBody: some View {
        self
            .onReceive(DeepLinkManager.shared.$pendingDeepLink) { deepLink in
                guard let deepLink = deepLink else { return }
                switch deepLink {
                case .moodAlert(_), .kickFlagAlert(_):
                    showShareScreenFromDeepLink = true
                    DeepLinkManager.shared.pendingDeepLink = nil
                default:
                    break
                }
            }
            .fullScreenCover(isPresented: $showShareScreenFromDeepLink) {
                NavigationView {
                    AppShareView()
                        .navigationBarItems(leading: Button("닫기") { showShareScreenFromDeepLink = false })
                }
            }
    }
}

// MARK: - App Guide View (Included here to avoid file referencing issues)

struct AppGuideView: View {
    @Environment(\.presentationMode) var presentationMode
    
    var body: some View {
        // Removed NavigationView wrapper to avoid nested navigation when pushed from Settings
        ZStack {
            Color(hexString: "F5F5F7").edgesIgnoringSafeArea(.all)
            
            ScrollView {
                VStack(alignment: .leading, spacing: 30) {
                    // Header
                    VStack(alignment: .leading, spacing: 10) {
                        Text("📖 사용 설명서")
                            .font(.system(size: 28, weight: .bold))
                            .foregroundColor(Color(hexString: "1D1D1F"))
                        Text("마음온(maumON)을 100% 활용하는 방법을 알려드려요.")
                            .font(.system(size: 15))
                            .foregroundColor(Color(hexString: "86868B"))
                    }
                    .padding(.top, 20)
                    
                    // Section 1: 일기 작성하기
                    VStack(alignment: .leading, spacing: 20) {
                        GuideSectionHeader(title: "📝 일기 작성하기", desc: "하루의 감정을 4단계로 나누어 천천히 기록해보세요.")
                        
                        VStack(spacing: 16) {
                            GuideStepCard(num: "1", title: "사실 (Event)", desc: "오늘 있었던 일이나 상황을 객관적으로 적어보세요.")
                            GuideStepCard(num: "2", title: "감정 (Emotion)", desc: "그 상황에서 느낀 솔직한 감정들을 단어나 문장으로 표현해요.")
                            GuideStepCard(num: "3", title: "의미 (Meaning)", desc: "왜 그런 감정이 들었는지, 나에게 어떤 의미인지 깊이 생각해보세요.")
                            GuideStepCard(num: "4", title: "위로 (Self-Talk)", desc: "오늘 하루 고생한 나에게 따뜻한 위로와 격려의 말을 건네주세요.")
                        }
                    }
                    
                    // Section 2: AI 분석
                    VStack(alignment: .leading, spacing: 20) {
                        GuideSectionHeader(title: "🤖 AI 감정 분석 & 코멘트", desc: "AI가 당신의 마음을 따뜻하게 읽어드립니다.")
                        
                        GuideFeatureCard(icon: "🧠", title: "60가지 섬세한 감정의 언어", desc: "단순히 '좋다/나쁘다'가 아닌, **60가지의 세분화된 감정**으로 당신의 마음을 정확하게 읽어냅니다.")
                        GuideFeatureCard(icon: "💬", title: "AI 감정 분석 코멘트 (Gemma 2)", desc: "구글의 최신 모델 **Gemma 2 (2b)**가 문맥과 숨겨진 의미를 파악하여 따뜻한 위로를 건넵니다.")
                    }
                    
                    // Section 3: 프라이버시 & 심층 분석
                    VStack(alignment: .leading, spacing: 20) {
                        GuideSectionHeader(title: "📊 프라이버시 & 심층 분석", desc: "안전하고 깊이 있는 분석을 경험하세요.")
                        
                        GuideFeatureCard(icon: "🛡️", title: "🔒 철통 보안 AI 감정 분석", desc: "외부 클라우드 전송 NO! **안전한 로컬/개인 서버 AI**가 당신만의 비밀 공간에서 분석합니다.", highlight: true)
                        GuideFeatureCard(icon: "📑", title: "🧠 심층 감정 리포트", desc: "일기가 3개 이상 모이면, **나만의 감정 분석 보고서**를 발행해 드려요. (숨겨진 욕구, 스트레스 원인 분석)")
                        GuideFeatureCard(icon: "🔭", title: "🔬 과거 기록 통합 분석", desc: "과거와 현재를 비교 분석하여 감정의 흐름과 성장을 **장기적인 통찰**로 제공합니다.")
                        
                        HStack(spacing: 14) {
                            GuideSmallFeatureCard(title: "🧩 감정 패턴 통계", desc: "날씨와 기분의 상관관계 한눈에 보기")
                            GuideSmallFeatureCard(title: "🔍 키워드 검색", desc: "감정, 사건 키워드로 과거의 나 찾기")
                        }
                        .fixedSize(horizontal: false, vertical: true)
                    }
                    
                    Spacer(minLength: 50)
                }
                .padding(24)
            }
        }
    }
}

// MARK: - Components

struct GuideSectionHeader: View {
    let title: String
    let desc: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(Color(hexString: "1D1D1F"))
            Text(desc)
                .font(.subheadline)
                .foregroundColor(Color(hexString: "666666"))
        }
    }
}

struct GuideStepCard: View {
    let num: String
    let title: String
    let desc: String
    
    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            ZStack {
                Circle()
                    .fill(Color(hexString: "1D1D1F"))
                    .frame(width: 28, height: 28)
                    .shadow(color: Color.black.opacity(0.15), radius: 4, x: 0, y: 4)
                Text(num)
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white)
            }
            
            VStack(alignment: .leading, spacing: 6) {
                Text(title)
                    .font(.custom("Pretendard-Bold", size: 16)) // Fallback to system bold if custom font missing
                    .fontWeight(.bold)
                    .foregroundColor(Color(hexString: "1D1D1F"))
                Text(desc)
                    .font(.system(size: 14))
                    .foregroundColor(Color(hexString: "555555"))
                    .lineSpacing(4)
            }
            Spacer()
        }
        .padding(20)
        .background(Color(hexString: "FBFBFD"))
        .cornerRadius(16)
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(Color(hexString: "F2F2F7"), lineWidth: 1)
        )
    }
}

struct GuideFeatureCard: View {
    let icon: String
    let title: String
    let desc: String
    var highlight: Bool = false
    
    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            VStack(alignment: .leading, spacing: 8) {
                Text(title)
                    .font(.headline)
                    .fontWeight(.bold)
                    .foregroundColor(Color(hexString: "1D1D1F"))
                
                // Simple Markdown-like bold parsing manually or just Text
                Text(parseBold(desc))
                    .font(.system(size: 14))
                    .foregroundColor(Color(hexString: "555555"))
                    .lineSpacing(4)
            }
            Spacer()
            Text(icon).font(.system(size: 32))
        }
        .padding(24)
        .background(highlight ? Color.white : Color(hexString: "FBFBFD"))
        .cornerRadius(20)
        .overlay(
            RoundedRectangle(cornerRadius: 20)
                .stroke(highlight ? Color(hexString: "34C759") : Color(hexString: "F0F0F5"), lineWidth: highlight ? 2 : 1)
        )
        .shadow(color: highlight ? Color.green.opacity(0.05) : Color.clear, radius: 10, x: 0, y: 5)
    }
    
    func parseBold(_ text: String) -> AttributedString {
        if let attrStr = try? AttributedString(markdown: text) {
            return attrStr
        }
        return AttributedString(stringLiteral: text) // 파싱 실패 시 원본 문자열 반환
    }
}


struct GuideSmallFeatureCard: View {
    let title: String
    let desc: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.headline)
                .fontWeight(.bold)
                .foregroundColor(Color(hexString: "1D1D1F"))
            Text(desc)
                .font(.caption)
                .foregroundColor(Color(hexString: "555555"))
                .lineSpacing(2)
            Spacer()
        }
        .padding(16)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(Color(hexString: "FBFBFD"))
        .cornerRadius(16)
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(Color(hexString: "F0F0F5"), lineWidth: 1)
        )
    }
}

