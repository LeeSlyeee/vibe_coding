
import SwiftUI

struct AppMainTabView: View {
    @EnvironmentObject var authManager: AuthManager
    @StateObject private var networkMonitor = NetworkMonitor()
    @State private var showAssessment = false
    @State private var selection = 0
    @State private var showEmergencySheet = false
    
    var body: some View {
        if !authManager.isAuthenticated {
            AppLoginView()
        } else {
            ZStack(alignment: .bottomTrailing) {
                // Main Content
                ZStack(alignment: .top) {
                    TabView(selection: $selection) {
                        MoodCalendarView()
                            .tabItem { Label("캘린더", systemImage: "calendar") }
                            .tag(0)
                        
                        // RBAC Check: If Level 1 (Mild), Show Lock or Limited View
                        // But for better UX, let AppStatsView handle the internal lock UI.
                        AppStatsView()
                            .tabItem { Label("통계", systemImage: "chart.bar.fill") }
                            .tag(1)
                        
                        AppGuideView()
                            .tabItem { Label("가이드", systemImage: "book.fill") }
                            .tag(2)
                        
                        AppChatView()
                            .tabItem { Label("상담", systemImage: "message.fill") }
                            .tag(3)
                        
                        AppSettingsView()
                            .tabItem { Label("설정", systemImage: "gearshape.fill") }
                            .tag(4)
                    }
                    .accentColor(.black)
                    .disabled(!networkMonitor.isConnected) // Disable interaction if offline? Or just show banner. Let's just show banner.
                    
                    // Network Status Banner
                    if !networkMonitor.isConnected {
                        VStack {
                            HStack {
                                Image(systemName: "wifi.slash")
                                Text("네트워크 연결이 불안정합니다.")
                                    .font(.system(size: 14, weight: .bold))
                                Spacer()
                            }
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.red)
                            .shadow(radius: 2)
                            
                            Spacer()
                        }
                        .transition(.move(edge: .top))
                        .animation(.easeInOut, value: networkMonitor.isConnected)
                        .zIndex(100) // Ensure it's on top of everything
                    }
                }
                
                // SOS Button (Only for High Risk Users)
                if authManager.riskLevel >= 3 {
                    Button(action: { showEmergencySheet = true }) {
                        HStack(spacing: 5) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .font(.system(size: 20))
                            Text("긴급 도움")
                                .fontWeight(.bold)
                        }
                        .foregroundColor(.white)
                        .padding(.vertical, 12)
                        .padding(.horizontal, 20)
                        .background(Color.red)
                        .cornerRadius(30)
                        .shadow(color: Color.red.opacity(0.4), radius: 5, x: 0, y: 5)
                    }
                    .padding(.trailing, 20)
                    .padding(.bottom, 100)
                    .confirmationDialog("긴급 연결", isPresented: $showEmergencySheet, titleVisibility: .visible) {
                        Button("자살예방 상담전화 (1393)") {
                            callNumber("1393")
                        }
                        Button("정신건강 위기상담전화 (1577-0199)") {
                            callNumber("15770199")
                        }
                        Button("경찰청 긴급신고 (112)") {
                            callNumber("112")
                        }
                        Button("취소", role: .cancel) { }
                    } message: {
                        Text("도움이 필요한 곳을 선택해주세요.")
                    }
                }
            }
            #if os(iOS)
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
                // Listen for Chat Redirection
                NotificationCenter.default.addObserver(forName: NSNotification.Name("SwitchToChatTab"), object: nil, queue: .main) { notif in
                    self.selection = 3 // Switch to Chat Tab
                }
            }
        }
    }
    
    func checkAssessmentStatus() {
        // 로그인된 상태에서만 진단 여부를 체크해야 함.
        guard authManager.isAuthenticated else { return }
        
        let hasDone = UserDefaults.standard.bool(forKey: "hasCompletedAssessment")
        if !hasDone {
            // Give a small delay for smooth transition
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                showAssessment = true
            }
        }
    }
    
    func callNumber(_ number: String) {
        guard let url = URL(string: "tel://\(number)") else { return }
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
        NavigationView {
            ZStack {
                Color(hex: "F5F5F7").edgesIgnoringSafeArea(.all)
                
                ScrollView {
                    VStack(alignment: .leading, spacing: 30) {
                        // Header
                        VStack(alignment: .leading, spacing: 10) {
                            Text("📖 사용 설명서")
                                .font(.system(size: 28, weight: .bold))
                                .foregroundColor(Color(hex: "1D1D1F"))
                            Text("마음 온(Maum-on)을 100% 활용하는 방법을 알려드려요.")
                                .font(.system(size: 15))
                                .foregroundColor(Color(hex: "86868B"))
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
                            GuideSectionHeader(title: "🤖 AI 감정 분석 & 코멘트", desc: "전문 상담사급 AI가 당신의 마음을 읽어드립니다.")
                            
                            GuideFeatureCard(icon: "🧠", title: "60가지 섬세한 감정의 언어", desc: "단순히 '좋다/나쁘다'가 아닌, **60가지의 세분화된 감정**으로 당신의 마음을 정확하게 읽어냅니다.")
                            GuideFeatureCard(icon: "💬", title: "전문 상담사급 AI 코멘트 (Gemma 2)", desc: "구글의 최신 모델 **Gemma 2 (2b)**가 문맥과 숨겨진 의미를 파악하여 따뜻한 위로를 건넵니다.")
                        }
                        
                        // Section 3: 프라이버시 & 심층 분석
                        VStack(alignment: .leading, spacing: 20) {
                            GuideSectionHeader(title: "📊 프라이버시 & 심층 분석", desc: "안전하고 깊이 있는 분석을 경험하세요.")
                            
                            GuideFeatureCard(icon: "🛡️", title: "🔒 철통 보안 AI 상담사", desc: "외부 클라우드 전송 NO! **안전한 로컬/개인 서버 AI**가 당신만의 비밀 공간에서 분석합니다.", highlight: true)
                            GuideFeatureCard(icon: "📑", title: "🧠 심층 심리 리포트", desc: "일기가 3개 이상 모이면, **나만의 심리 보고서**를 발행해 드려요. (숨겨진 욕구, 스트레스 원인 진단)")
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
            #if os(iOS)
            .navigationBarHidden(true)
            #endif
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
                .foregroundColor(Color(hex: "1D1D1F"))
            Text(desc)
                .font(.subheadline)
                .foregroundColor(Color(hex: "666666"))
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
                    .fill(Color(hex: "1D1D1F"))
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
                    .foregroundColor(Color(hex: "1D1D1F"))
                Text(desc)
                    .font(.system(size: 14))
                    .foregroundColor(Color(hex: "555555"))
                    .lineSpacing(4)
            }
            Spacer()
        }
        .padding(20)
        .background(Color(hex: "FBFBFD"))
        .cornerRadius(16)
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(Color(hex: "F2F2F7"), lineWidth: 1)
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
                    .foregroundColor(Color(hex: "1D1D1F"))
                
                // Simple Markdown-like bold parsing manually or just Text
                Text(parseBold(desc))
                    .font(.system(size: 14))
                    .foregroundColor(Color(hex: "555555"))
                    .lineSpacing(4)
            }
            Spacer()
            Text(icon).font(.system(size: 32))
        }
        .padding(24)
        .background(highlight ? Color.white : Color(hex: "FBFBFD"))
        .cornerRadius(20)
        .overlay(
            RoundedRectangle(cornerRadius: 20)
                .stroke(highlight ? Color(hex: "34C759") : Color(hex: "F0F0F5"), lineWidth: highlight ? 2 : 1)
        )
        .shadow(color: highlight ? Color.green.opacity(0.05) : Color.clear, radius: 10, x: 0, y: 5)
    }
    
    func parseBold(_ text: String) -> AttributedString {
        try! AttributedString(markdown: text)
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
                .foregroundColor(Color(hex: "1D1D1F"))
            Text(desc)
                .font(.caption)
                .foregroundColor(Color(hex: "555555"))
                .lineSpacing(2)
            Spacer()
        }
        .padding(16)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(Color(hex: "FBFBFD"))
        .cornerRadius(16)
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(Color(hex: "F0F0F5"), lineWidth: 1)
        )
    }
}
