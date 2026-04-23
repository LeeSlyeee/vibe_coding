
import SwiftUI

struct AppMainTabView: View {
    @EnvironmentObject var authManager: AuthManager
    @Environment(\.scenePhase) var scenePhase // [New] Detect App Background/Foreground
    @StateObject private var networkMonitor = NetworkMonitor()
    @State private var showAssessment = false
    @State private var selection = 0
    @State private var isTabBarHidden = false // [New] TabBar Visibility Control
    @State private var showToast = false // [New] AI Loaded Toast
    @State private var showBirthdayToast = false // [New] Birthday Toast State (Me)
    @State private var showFriendBirthdayToast = false // [New] Friend Birthday Toast (Others)
    @State private var activeFullScreen: DeepLinkManager.ActiveScreen? // [DeepLink] Route Anchor
    
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
    
    // [Keyboard Fix] shouldShowTabBar는 KeyboardAwareTabBar 내부로 이동
    // → KeyboardObserver 변경이 AppMainTabView.body 재평가를 일으키지 않음
    // → .sheet 안의 AppDiaryWriteView가 재생성되지 않아 포커스 유지됨
    
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
                // [Keyboard Fix] 별도의 View로 추출 → KeyboardObserver 변경이
                // AppMainTabView.body 재평가를 일으키지 않음
                // → .sheet 내 AppDiaryWriteView의 StableTextEditor가 재생성되지 않아 포커스 유지
                KeyboardAwareTabBar(selection: $selection)
                
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
                         
                         VStack(spacing: 24) {
                             ZStack {
                                 Circle()
                                     .fill(Color.gray50)
                                     .frame(width: 100, height: 100)
                                 
                                 Text("🎂")
                                     .font(.system(size: 60))
                                     .offset(y: -4)
                             }
                             
                             VStack(spacing: 8) {
                                 Text("생일 축하해요! 🎉")
                                     .font(.geistTitle)
                                     .foregroundColor(Color.gray900)
                                 
                                 Text("세상에서 가장 특별하고\n따뜻한 하루가 되기를 바랄게요!")
                                     .font(.geistBody)
                                     .foregroundColor(Color.gray500)
                                     .multilineTextAlignment(.center)
                                     .lineSpacing(4)
                             }
                             
                             Button(action: {
                                 withAnimation { showBirthdayToast = false }
                             }) {
                                 Text("고마워요")
                                     .font(.system(size: 15, weight: .medium))
                                     .foregroundColor(.white)
                                     .frame(maxWidth: .infinity)
                                     .padding(.vertical, 14)
                                     .background(
                                         RoundedRectangle(cornerRadius: 8)
                                             .fill(Color.gray900)
                                     )
                             }
                             .padding(.top, 10)
                             .padding(.horizontal, 20)
                         }
                         .padding(.vertical, 40)
                         .padding(.horizontal, 20)
                         .background(
                            RoundedRectangle(cornerRadius: 16)
                                .fill(Color.white)
                         )
                         .overlay(
                            RoundedRectangle(cornerRadius: 16)
                                .stroke(Color.black.opacity(0.08), lineWidth: 1)
                         )
                         .shadow(color: Color.black.opacity(0.12), radius: 20, x: 0, y: 10)
                         .padding(30)
                     }
                     .zIndex(200)
                     .transition(.scale.combined(with: .opacity))
                }
                
                // [New] Friend Birthday Toast (Different Style)
                if showFriendBirthdayToast && !upcomingBirthdays.isEmpty {
                     ZStack {
                         Color.black.opacity(0.4).edgesIgnoringSafeArea(.all)
                         
                         VStack(spacing: 24) {
                             ZStack {
                                 Circle()
                                     .fill(Color.gray50)
                                     .frame(width: 80, height: 80)
                                 
                                 Text("🎉")
                                     .font(.system(size: 45))
                             }
                             
                             VStack(spacing: 8) {
                                 Text("다가오는 생일이 있어요!")
                                     .font(.system(size: 20, weight: .semibold))
                                     .foregroundColor(Color.gray900)
                                 
                                 Text("소중한 사람에게 따뜻한 축하를 전해보세요.")
                                     .font(.system(size: 14))
                                     .foregroundColor(Color.gray500)
                                     .multilineTextAlignment(.center)
                             }
                             
                             VStack(spacing: 10) {
                                 ForEach(upcomingBirthdays) { info in
                                     HStack {
                                         Text(info.name)
                                             .font(.system(size: 15, weight: .medium))
                                             .foregroundColor(Color.gray900)
                                         
                                         Spacer()
                                         
                                         if info.dDay == 0 {
                                             HStack(spacing: 4) { 
                                                 Text("🎂")
                                                 Text("오늘 생일!") 
                                             }
                                             .font(.geistCaption)
                                             .fontWeight(.medium)
                                             .foregroundColor(.white)
                                             .padding(.horizontal, 10)
                                             .padding(.vertical, 5)
                                             .background(
                                                 Capsule().fill(Color.gray900)
                                             )
                                         } else {
                                             Text("D-\(info.dDay)")
                                                 .font(.geistCaption)
                                                 .fontWeight(.medium)
                                                 .foregroundColor(Color.gray900)
                                                 .padding(.horizontal, 10)
                                                 .padding(.vertical, 5)
                                                 .background(
                                                     Capsule()
                                                         .fill(Color.gray50)
                                                 )
                                         }
                                     }
                                     .padding(.horizontal, 16)
                                     .padding(.vertical, 12)
                                     .background(Color.gray50)
                                     .cornerRadius(8)
                                 }
                             }
                             .padding(.horizontal, 8)
                             
                             Button(action: {
                                 withAnimation { showFriendBirthdayToast = false }
                             }) {
                                 Text("확인했어요")
                                     .font(.system(size: 15, weight: .medium))
                                     .foregroundColor(.white)
                                     .frame(maxWidth: .infinity)
                                     .padding(.vertical, 14)
                                     .background(
                                         RoundedRectangle(cornerRadius: 8)
                                             .fill(Color.gray900)
                                     )
                             }
                             .padding(.top, 10)
                         }
                         .padding(24)
                         .background(
                            RoundedRectangle(cornerRadius: 16)
                                .fill(Color.white)
                         )
                         .overlay(
                            RoundedRectangle(cornerRadius: 16)
                                .stroke(Color.black.opacity(0.08), lineWidth: 1)
                         )
                         .shadow(color: Color.black.opacity(0.12), radius: 20, x: 0, y: 10)
                         .padding(30)
                     }
                     .zIndex(190)
                     .transition(.scale.combined(with: .opacity))
                }
            }
            .edgesIgnoringSafeArea(.bottom)

            #if os(iOS)
            .fullScreenCover(isPresented: $showAssessment) {
                AppAssessmentView()
                    .onDisappear {
                        UserDefaults.standard.set(true, forKey: "hasCompletedAssessment")
                    }
            }
            .sheet(item: $activeFullScreen) { item in
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
                                }.foregroundColor(.accent)
                            })
                    }
                case .safetyCheck(let username):
                    SafetyCheckView(username: username)
                }
            } // Close sheet block
            .onChange(of: activeFullScreen) { newValue in
                if newValue == nil {
                    DeepLinkManager.shared.activeScreen = nil
                }
            }
            #else
            .sheet(isPresented: $showAssessment) {
                AppAssessmentView()
                    .onDisappear {
                        UserDefaults.standard.set(true, forKey: "hasCompletedAssessment")
                    }
            }
            .sheet(item: $activeFullScreen) { item in
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
                                }.foregroundColor(.accent)
                            })
                    }
                case .safetyCheck(let username):
                    SafetyCheckView(username: username)
                }
            }
            #endif
            .onReceive(DeepLinkManager.shared.$activeScreen) { screen in
                // 화면이 전환된 상태에서 바로 반영
                if screen != nil {
                    // 강제로 떠있을 수 있는 Assessment 모달을 먼저 해제하여 View Hierarchy 충돌 방지
                    self.showAssessment = false
                    
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                        self.activeFullScreen = screen
                    }
                } else {
                    self.activeFullScreen = nil
                }
            }
            .onAppear {
                // [DeepLink] 앱 실행 후 (Splash 이후) 쌓여있는 초기 딥링크 라우팅 실행
                if let pending = DeepLinkManager.shared.activeScreen {
                    
                    // 콜드 스타트 시에도 안전하게 이전 상태 청소 후 라우팅
                    self.showAssessment = false
                    
                    DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                        self.activeFullScreen = pending
                    }
                }
                
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
                    
                    // [Step 1] Verify Login Integrity First (Single Source of Truth)
                    if let username = authManager.username, !username.isEmpty {
                        
                        // [Step 2] Valid Auth -> Proceed to Sync
                        LocalDataManager.shared.syncWithServer()
                        
                    } else {
                        // [Step 1-Fail] Zombie State -> Recover First, Then Sync
                        
                        APIService.shared.syncUserInfo { success in
                            if success, let name = UserDefaults.standard.string(forKey: "userId") {
                                DispatchQueue.main.async {
                                    authManager.username = name
                                    // No need to set "app_username" anymore
                                    
                                    // [Step 2-Delayed] Now it's safe to sync
                                    LocalDataManager.shared.syncWithServer(force: true)
                                }
                            } else {
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
                return isSelected ? .primaryText : Color.hintText
            }
        }
        
        var textColor: Color {
            if isEmergency {
                return isSelected ? .red : .hintText
            } else {
                return isSelected ? .primaryText : .hintText
            }
        }
    }
    
    // [New] Profile Image Cache
    private var profileImageCache: [String: UIImage] = [:]
    
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
// MARK: - App Guide View (Included here to avoid file referencing issues)

struct AppGuideView: View {
    @Environment(\.presentationMode) var presentationMode
    
    var body: some View {
        ZStack {
            Color.white.edgesIgnoringSafeArea(.all)
            
            ScrollView {
                VStack(alignment: .leading, spacing: 30) {
                    // Header
                    VStack(alignment: .leading, spacing: 10) {
                        Text("사용 설명서")
                            .font(.system(size: 28, weight: .semibold))
                            .tracking(-0.5)
                            .foregroundColor(Color.gray900)
                        Text("마음온(maumON)을 100% 활용하는 방법을 알려드려요.")
                            .font(.system(size: 15))
                            .foregroundColor(Color.gray400)
                    }
                    .padding(.top, 20)
                    
                    // Section 1: 일기 작성하기
                    VStack(alignment: .leading, spacing: 20) {
                        GuideSectionHeader(title: "일기 작성하기", desc: "하루의 감정을 4단계로 나누어 천천히 기록해보세요.")
                        
                        VStack(spacing: 16) {
                            GuideStepCard(num: "1", title: "사실 (Event)", desc: "오늘 있었던 일이나 상황을 객관적으로 적어보세요.")
                            GuideStepCard(num: "2", title: "감정 (Emotion)", desc: "그 상황에서 느낀 솔직한 감정들을 단어나 문장으로 표현해요.")
                            GuideStepCard(num: "3", title: "의미 (Meaning)", desc: "왜 그런 감정이 들었는지, 나에게 어떤 의미인지 깊이 생각해보세요.")
                            GuideStepCard(num: "4", title: "위로 (Self-Talk)", desc: "오늘 하루 고생한 나에게 따뜻한 위로와 격려의 말을 건네주세요.")
                        }
                    }
                    
                    // Section 2: AI 분석
                    VStack(alignment: .leading, spacing: 20) {
                        GuideSectionHeader(title: "AI 감정 분석 & 코멘트", desc: "AI가 당신의 마음을 따뜻하게 읽어드립니다.")
                        
                        GuideFeatureCard(systemIcon: "brain.head.profile", title: "60가지 섬세한 감정의 언어", desc: "단순히 '좋다/나쁘다'가 아닌, **60가지의 세분화된 감정**으로 당신의 마음을 정확하게 읽어냅니다.")
                        GuideFeatureCard(systemIcon: "bubble.left.and.bubble.right.fill", title: "AI 감정 분석 코멘트 (Gemma 4)", desc: "구글의 최신 모델 **Gemma 4 (2b)**가 문맥과 숨겨진 의미를 파악하여 따뜻한 위로를 건넵니다.")
                    }
                    
                    // Section 3: 프라이버시 & 심층 분석
                    VStack(alignment: .leading, spacing: 20) {
                        GuideSectionHeader(title: "프라이버시 & 심층 분석", desc: "안전하고 깊이 있는 분석을 경험하세요.")
                        
                        GuideFeatureCard(systemIcon: "checkmark.shield.fill", title: "철통 보안 AI 감정 분석", desc: "외부 클라우드 전송 NO! **안전한 로컬/개인 서버 AI**가 당신만의 비밀 공간에서 분석합니다.", highlight: true)
                        GuideFeatureCard(systemIcon: "doc.text.below.ecg.fill", title: "심층 감정 리포트", desc: "일기가 3개 이상 모이면, **나만의 감정 분석 보고서**를 발행해 드려요. (숨겨진 욕구, 스트레스 원인 분석)")
                        GuideFeatureCard(systemIcon: "chart.xyaxis.line", title: "과거 기록 통합 분석", desc: "과거와 현재를 비교 분석하여 감정의 흐름과 성장을 **장기적인 통찰**로 제공합니다.")
                        
                        HStack(spacing: 14) {
                            GuideSmallFeatureCard(title: "감정 패턴 통계", desc: "날씨와 기분의 상관관계 한눈에 보기")
                            GuideSmallFeatureCard(title: "키워드 검색", desc: "감정, 사건 키워드로 과거의 나 찾기")
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
                .font(.system(size: 22, weight: .semibold))
                .foregroundColor(Color.gray900)
            Text(desc)
                .font(.system(size: 14))
                .foregroundColor(Color.gray500)
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
                    .fill(Color.gray900)
                    .frame(width: 28, height: 28)
                Text(num)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.white)
            }
            
            VStack(alignment: .leading, spacing: 6) {
                Text(title)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Color.gray900)
                Text(desc)
                    .font(.system(size: 14))
                    .foregroundColor(Color.gray500)
                    .lineSpacing(4)
            }
            Spacer()
        }
        .padding(20)
        .background(Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.black.opacity(0.08), lineWidth: 1)
        )
    }
}

struct GuideFeatureCard: View {
    let systemIcon: String
    let title: String
    let desc: String
    var highlight: Bool = false
    
    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            VStack(alignment: .leading, spacing: 8) {
                Text(title)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Color.gray900)
                
                Text(parseBold(desc))
                    .font(.system(size: 14))
                    .foregroundColor(Color.gray500)
                    .lineSpacing(4)
            }
            Spacer()
            Image(systemName: systemIcon)
                .font(.system(size: 28, weight: .thin))
                .foregroundColor(Color.gray900)
        }
        .padding(24)
        .background(Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(highlight ? Color.gray900 : Color.black.opacity(0.08), lineWidth: 1)
        )
    }
    
    func parseBold(_ text: String) -> AttributedString {
        if let attrStr = try? AttributedString(markdown: text) {
            return attrStr
        }
        return AttributedString(stringLiteral: text)
    }
}


// MARK: - [Keyboard Fix] 키보드 인식 탭바
// KeyboardObserver를 자체적으로 소유하여, 키보드 상태 변경이
// AppMainTabView.body 재평가를 일으키지 않음
// → .sheet 안의 AppDiaryWriteView가 재생성되지 않아 포커스 유지
#if os(iOS)
struct KeyboardAwareTabBar: View {
    @Binding var selection: Int
    @StateObject private var keyboardObserver = KeyboardObserver()
    
    private var shouldShow: Bool {
        !keyboardObserver.isKeyboardVisible
    }
    
    var body: some View {
        if shouldShow {
            VStack(spacing: 0) {
                // Geist: shadow-as-border for top edge
                Rectangle()
                    .fill(Color.black.opacity(0.08))
                    .frame(height: 1)
                
                HStack(spacing: 0) {
                    tabButton(index: 0, title: "캘린더", systemIcon: "calendar")
                    tabButton(index: 1, title: "분석", systemIcon: "chart.bar.fill")
                    tabButton(index: 2, title: "한마디", systemIcon: "message.fill")
                    tabButton(index: 3, title: "긴급", systemIcon: "exclamationmark.triangle.fill")
                }
                .padding(.top, 10)
                .padding(.bottom, 20)
                .background(Color.white)
            }
            .transition(.move(edge: .bottom).combined(with: .opacity))
        }
    }
    
    private func tabButton(index: Int, title: String, systemIcon: String) -> some View {
        let isSelected = selection == index
        let isEmergency = index == 3
        
        return Button(action: {
            withAnimation(.easeInOut(duration: 0.1)) {
                selection = index
            }
            if index == 0 {
                LocalDataManager.shared.syncWithServer()
            }
        }) {
            VStack(spacing: 4) {
                Image(systemName: systemIcon)
                    .resizable()
                    .renderingMode(.template)
                    .scaledToFit()
                    .frame(width: 24, height: 24)
                    .foregroundColor(isEmergency
                        ? (isSelected ? .red : .red.opacity(0.6))
                        : (isSelected ? .primaryText : Color.hintText))
                
                Text(title)
                    .font(.caption)
                    .fontWeight(isSelected ? .bold : .regular)
                    .foregroundColor(isEmergency
                        ? (isSelected ? .red : .hintText)
                        : (isSelected ? .primaryText : .hintText))
            }
        }
        .frame(maxWidth: .infinity)
        .contentShape(Rectangle())
    }
}
#else
struct KeyboardAwareTabBar: View {
    @Binding var selection: Int
    
    var body: some View {
        VStack(spacing: 0) {
            Divider()
                .background(Color.hintText.opacity(0.1))
            
            HStack(spacing: 0) {
                // macOS용 간단 탭바 (필요시 구현)
            }
        }
    }
}
#endif
struct GuideSmallFeatureCard: View {
    let title: String
    let desc: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.system(size: 15, weight: .semibold))
                .foregroundColor(Color.gray900)
            Text(desc)
                .font(.geistCaption)
                .foregroundColor(Color.gray500)
                .lineSpacing(2)
            Spacer()
        }
        .padding(16)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.black.opacity(0.08), lineWidth: 1)
        )
    }
}

