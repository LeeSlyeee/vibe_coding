
import SwiftUI

struct AppChatView: View {
    @EnvironmentObject var authManager: AuthManager
    @ObservedObject var llmService = LLMService.shared // [New] LLM 상태 관찰
    @State private var messages: [ChatMessage] = []
    @State private var inputText: String = ""
    @State private var isTyping: Bool = false
    @State private var scrollViewProxy: ScrollViewProxy? = nil
    
    // Phase 2: Report Modal State
    @State private var showReport = false
    
    // [UX] Cold Start Hint
    @State private var loadingHint: String? = nil
    
    // [New] SOS Crisis State
    @State private var isCrisis: Bool = false
    @State private var showSOSModal: Bool = false
    
    // [Gatekeeper] Mode Selection State
    @State private var showModeSelection: Bool = true
    
    // [New] Settings Modal State
    @State private var showSettings = false
    
    // [New] Focus State based Keyboard Handling
    @FocusState private var isInputFocused: Bool
    
    // Server Configuration
    let baseURL = "http://150.230.7.76"
    
    var body: some View {
        ZStack {
            // Main Chat UI
            NavigationView {
                VStack(spacing: 0) {
                    // [New] Model Loading Indicator
                    if !llmService.isModelLoaded && llmService.modelLoadingProgress > 0 {
                        VStack(spacing: 8) {
                            Text(llmService.modelLoadingProgress > 0 ? "AI 모델 준비 중 (\(Int(llmService.modelLoadingProgress * 100))%)" : "AI 모델 다운로드 대기 중...")
                                .font(.caption)
                                .foregroundColor(.blue)
                            ProgressView(value: llmService.modelLoadingProgress)
                                .progressViewStyle(LinearProgressViewStyle())
                                .frame(height: 2)
                        }
                        .padding(.horizontal)
                        .padding(.top, 8)
                        .transition(.move(edge: .top))
                    }

                    // Chat List
                    ScrollViewReader { proxy in
                        ScrollView {
                            LazyVStack(spacing: 12) {
                                // Intro Message
                                if messages.isEmpty {
                                    VStack(spacing: 10) {
                                        Text("👋")
                                            .font(.system(size: 40))
                                        Text(llmService.useServerAI ? "안녕하세요!\n(서버 AI 모드 동작 중)" : "안녕하세요!\n마음 속 이야기를 자유롭게 들려주세요.\n제가 경청하고 공감해드릴게요.")
                                            .multilineTextAlignment(.center)
                                            .font(.body)
                                            .foregroundColor(.gray)
                                    }
                                    .padding(.top, 40)
                                }
                                
                                ForEach(messages) { message in
                                    ChatBubble(message: message)
                                        .id(message.id)
                                }
                                
                                if isTyping {
                                    HStack(spacing: 12) {
                                        TypingIndicator()
                                        
                                        if let hint = loadingHint {
                                            Text(hint)
                                                .font(.caption)
                                                .foregroundColor(.gray)
                                                .transition(.opacity)
                                                .multilineTextAlignment(.leading)
                                        }
                                        Spacer()
                                    }
                                    .padding(.leading, 16)
                                    .id("typingIndicator")
                                }
                            }
                            .padding(.vertical, 16)
                        }
                        .onAppear {
                            self.scrollViewProxy = proxy
                            
                            // [Sync & Greeting] 서버에서 최신 실명 가져온 뒤 인사
                            APIService.shared.syncUserInfo { success in
                                DispatchQueue.main.async {
                                    // [Name Fix] 실명 우선 사용
                                    var userName = UserDefaults.standard.string(forKey: "realName") 
                                                ?? UserDefaults.standard.string(forKey: "userNickname") 
                                                ?? "회원"
                                    
                                    if userName.hasPrefix("User ") || userName.hasPrefix("user_") {
                                        userName = "회원"
                                    }
                                    
                                    // 이미 메시지가 있으면 인사 생략 (단, 텅 빈 경우에만 인사)
                                    if messages.isEmpty {
                                        let welcomeText = "안녕하세요, \(userName)님! 👋\n\n오늘 하루는 어떠셨나요?\n기억에 남는 사건이나 감정을 편하게 이야기해 주세요.\n\n제가 꼼꼼히 듣고 마음을 분석해 드릴게요."
                                        
                                        // 약간의 딜레이 후 등장
                                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                                            if messages.isEmpty { 
                                                withAnimation {
                                                    messages.append(ChatMessage(text: welcomeText, isUser: false))
                                                }
                                            }
                                        }
                                    }
                                }
                            }

                            // [New] Trigger Model Load ONLY if Local Mode is confirmed
                            if !showModeSelection && !llmService.useServerAI && !llmService.isModelLoaded {
                                Task { await llmService.loadModel() }
                            }
                        }
                        .onChangeCompat(of: messages.count) { _ in
                            scrollToBottom(proxy: proxy)
                        }
                        .onChangeCompat(of: isTyping) { _ in
                            scrollToBottom(proxy: proxy)
                        }
                        // [UX] Dismiss Keyboard on Drag/Tap
                        .onTapGesture {
                            isInputFocused = false
                        }
                    }
                    
                    // [New] Crisis Banner (위기 감지 시 노출)
                    if isCrisis {
                        Button(action: { showSOSModal = true }) {
                            HStack {
                                Image(systemName: "exclamationmark.triangle.fill")
                                    .foregroundColor(.white)
                                Text("전문가의 도움이 필요하신가요? (긴급 연락처)")
                                    .fontWeight(.bold)
                                    .foregroundColor(.white)
                                Spacer()
                                Image(systemName: "chevron.right")
                                    .foregroundColor(.white)
                            }
                            .padding()
                            .background(Color.red.opacity(0.9))
                            .cornerRadius(12)
                            .padding(.horizontal)
                            .padding(.bottom, 4)
                            .transition(.move(edge: .bottom).combined(with: .opacity))
                        }
                    }
                    
                    // Input Area
                    HStack(spacing: 10) {
                        // [New] Mode Selection Button (Previous Top-Right Feature)
                        Button(action: {
                            withAnimation { showModeSelection = true }
                        }) {
                            Image(systemName: "plus")
                                .font(.system(size: 20, weight: .bold))
                                .foregroundColor(.gray)
                                .padding(8)
                                .background(Color.gray.opacity(0.1))
                                .clipShape(Circle())
                        }
                        .disabled(isTyping || showModeSelection)
                        
                        TextField("메시지 보내기...", text: $inputText)
                            .focused($isInputFocused) // [New] Focus Binding
                            .padding(12)
                            .background(Color.gray.opacity(0.1))
                            .cornerRadius(20)
                            .disabled(isTyping || showModeSelection)
                            .onChange(of: isInputFocused) { focused in
                                // Notify MainTabView to hide/show TabBar
                                NotificationCenter.default.post(
                                    name: NSNotification.Name(focused ? "HideTabBar" : "ShowTabBar"),
                                    object: nil
                                )
                            }
                        
                        Button(action: sendMessage) {
                            Image(systemName: "paperplane.fill")
                                .font(.system(size: 20))
                                .foregroundColor(inputText.isEmpty ? .gray : .blue)
                                .padding(10)
                                .background(Color.blue.opacity(0.1))
                                .clipShape(Circle())
                        }
                        .disabled(inputText.isEmpty || isTyping || showModeSelection)
                    }
                    .padding()
                    // [UI Fix] Dynamic Padding: Keyboard Up (0) vs Keyboard Down (60 for TabBar)
                    // 평소엔 탭바 공간(60) 확보, 키보드 올라오면 0으로 붙임
                    .padding(.bottom, isInputFocused ? 0 : 60)
                    .background(Color.white)
                    .shadow(color: Color.black.opacity(0.05), radius: 5, x: 0, y: -5)
                }
                #if os(iOS)
                .navigationBarTitle("마음 톡(Talk)", displayMode: .inline)
                .navigationBarItems(
                    leading: Button(action: { showReport = true }) {
                        Image(systemName: "chart.pie.fill")
                            .foregroundColor(.black)
                    },
                    trailing: Button(action: { showSettings = true }) {
                        Image(systemName: "gearshape.fill")
                            .foregroundColor(.black)
                    }
                )
                #endif
                .background(Color.white.edgesIgnoringSafeArea(.all))
                .sheet(isPresented: $showReport) {
                    ChatReportView(authManager: authManager)
                        .screenshotProtected(isProtected: true) // 스크린샷 방지
                }
                .sheet(isPresented: $showSOSModal) {
                    SOSView()
                        .screenshotProtected(isProtected: true) // 스크린샷 방지
                }
                .sheet(isPresented: $showSettings) {
                    NavigationView {
                        AppSettingsView()
                            .navigationBarItems(trailing: Button("닫기") {
                                showSettings = false
                            })
                    }
                    .screenshotProtected(isProtected: true) // 스크린샷 방지
                }
            }
            .blur(radius: showModeSelection ? 5 : 0) // Blur background
            
            // [Gatekeeper] AI Mode Selection Overlay
            if showModeSelection {
                Color.black.opacity(0.4)
                    .edgesIgnoringSafeArea(.all)
                    .onTapGesture {
                        // Prevent dismissal by tapping background (Force selection)
                    }
                    
                VStack(spacing: 24) {
                    // Header
                    VStack(spacing: 8) {
                        Text("🤖 AI 모드 선택")
                            .font(.title2)
                            .fontWeight(.bold)
                        Text("원활한 상담을 위해 실행 방식을 선택해주세요.")
                            .font(.caption)
                            .foregroundColor(.gray)
                    }
                    
                    // Option 1: Server (Recommended)
                    Button(action: {
                        llmService.useServerAI = true
                        withAnimation { showModeSelection = false }
                    }) {
                        HStack(spacing: 16) {
                            ZStack {
                                Circle().fill(Color.blue.opacity(0.1)).frame(width: 50, height: 50)
                                Image(systemName: "cloud.fill").foregroundColor(.blue).font(.title2)
                            }
                            
                            VStack(alignment: .leading, spacing: 4) {
                                Text("서버 연결 (권장)")
                                    .font(.headline)
                                    .foregroundColor(.black)
                                Text("데이터를 사용하여 빠르고 쾌적합니다.\n모든 기기에서 원활하게 작동합니다.")
                                    .font(.caption)
                                    .foregroundColor(.gray)
                            }
                            Spacer()
                            Image(systemName: "checkmark.circle.fill").foregroundColor(.blue)
                        }
                        .padding()
                        .background(Color.white)
                        .cornerRadius(16)
                        .shadow(color: Color.black.opacity(0.1), radius: 5, x: 0, y: 2)
                    }
                    
                    // Option 2: Local (Pro)
                    Button(action: {
                        llmService.useServerAI = false
                        withAnimation { showModeSelection = false }
                        // Trigger Load
                        Task { await llmService.loadModel() }
                    }) {
                        HStack(spacing: 16) {
                            ZStack {
                                Circle().fill(Color.purple.opacity(0.1)).frame(width: 50, height: 50)
                                Image(systemName: "iphone.gen3").foregroundColor(.purple).font(.title2)
                            }
                            
                            VStack(alignment: .leading, spacing: 4) {
                                Text("내 기기에서 실행 (Pro)")
                                    .font(.headline)
                                    .foregroundColor(.black)
                                Text("데이터 없이 오프라인에서 작동합니다.\n*최신 고성능 아이폰 필요 (발열 주의)")
                                    .font(.caption)
                                    .foregroundColor(.gray)
                            }
                            Spacer()
                        }
                        .padding()
                        .background(Color.white)
                        .cornerRadius(16)
                        .shadow(color: Color.black.opacity(0.1), radius: 5, x: 0, y: 2)
                    }
                    
                }
                .padding(24)
                .background(Color.white)
                .cornerRadius(24)
                .padding(.horizontal, 20)
                .shadow(radius: 20)
                .transition(.scale.combined(with: .opacity))
            }
        }
    }
    
    private func sendMessage() {
        // [Critical Fix] 중복 실행 방지 가드는 맨 처음에!
        // 1. 입력값 및 상태 체크
        guard !isTyping else { return }
        guard !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        
        // 2. 상태 체크 (LLM Busy check)
        // [Gatekeeper] 분석 중이면 채팅 불가 (1-by-1 정책)
        if !llmService.useServerAI && (llmService.isProcessingQueue || !llmService.analysisQueue.isEmpty) {
            // Alert logic (SwiftUI Alert State binding needed, but for now simple print or shake)
            print("⛔️ [Chat] LLM Busy. Cannot start chat.")
            // 임시로 채팅창에 시스템 메시지 추가
            let sysMsg = ChatMessage(text: "⚠️ 현재 일기 분석 중입니다. 잠시 후 다시 시도해주세요.", isUser: false)
            messages.append(sysMsg)
            return
        }
        
        let userText = inputText
        inputText = ""
        isTyping = true 
        self.loadingHint = "답변을 생각하는 중..."
        
        // [UX] Cold Start Timer (서버 깨어날 때 지루하지 않게 멘트 변경)
        Task {
            try? await Task.sleep(nanoseconds: 4 * 1_000_000_000)
            // 아직도 타이핑 중이고, AI 메시지가 없거나 비어있다면 (대기 중)
            if isTyping && (messages.last?.isUser == true || messages.last?.text.isEmpty == true) {
                withAnimation { self.loadingHint = "AI가 마음의 준비를 하고 있어요... 🌿\n(서버가 깨어나는 중입니다)" }
            }
            
            try? await Task.sleep(nanoseconds: 6 * 1_000_000_000) // +6초 (총 10초)
            if isTyping && (messages.last?.isUser == true || messages.last?.text.isEmpty == true) {
                withAnimation { self.loadingHint = "거의 다 되었습니다! 잠시만요... 🏃🏻" }
            }
        } 
        
        // 3. 사용자 메시지 추가
        let userMsg = ChatMessage(text: userText, isUser: true)
        messages.append(userMsg)
        
        // Haptic Feedback
        #if os(iOS)
        let generator = UIImpactFeedbackGenerator(style: .medium)
        generator.impactOccurred()
        #endif
        
        // 4. AI 작업 시작 (MainActor Task)
        Task {
            // 대화 내역 조합
            var historyContext = ""
            
            // [Memory & Logic Fix] 상황별 컨텍스트 길이 조절 (Dynamic Context Window)
            let triggers = ["반복", "그만", "똑같", "뭐하", "장난", "tq", "시발", "답답", "멍충", "바보"] 
            let isComplaint = (triggers.contains { userText.contains($0) }) && (userText.count < 30)
            
            // [Memory & Performance] 대화가 길어지면 서버가 힘들어하므로 최근 4개(2번의 티키타카)만 기억
            // 불만 토로 시에는 빠른 전환을 위해 기억을 지움
            let historyLimit = isComplaint ? 0 : 4 
            
            if isComplaint {
                print("🚨 [Dynamic Context] Complaint detected (Short Anger). Clearing history to break loop.")
            } else {
                print("🧠 [Context] Sending last \(historyLimit) messages for context.")
            }
            
            // [New] Crisis Detection (위기 키워드 감지)
            let crisisKeywords = ["죽고", "자살", "뛰어내", "사라지고", "보건소", "정신과", "상담센터", "약", "수면제"]
            if crisisKeywords.contains(where: { userText.contains($0) }) {
                withAnimation {
                    self.isCrisis = true
                }
            }
            
            let recentMessages = messages.suffix(historyLimit)
            for msg in recentMessages {
                let role = msg.isUser ? "User" : "Model"
                // 메시지 길이 제한 (너무 긴 메시지는 잘라서 전달)
                let safeText = String(msg.text.prefix(300)) 
                historyContext += "\(role): \(safeText)\n"
            }
            
            let prompt = """
            [대화 내역]
            \(historyContext)
            
            User: \(userText)
            """
            
            // 빈 말풍선 추가 (이제 곧 채워질 공간)
            messages.append(ChatMessage(text: "", isUser: false))
            
            var fullResponse = ""
            
            // 스트림 구독 (LLMService.generateAnalysis는 이미 백그라운드에서 동작)
            for await token in await LLMService.shared.generateAnalysis(
                diaryText: prompt, 
                userText: userText,        // Server Mode용
                historyString: historyContext // Server Mode용
            ) {
                // 첫 토큰 도착 시 힌트 삭제 (타이핑 시작)
                if loadingHint != nil { 
                    withAnimation { loadingHint = nil } 
                }
                // [RESET] 명령 감지 시 텍스트 초기화 (안전 장치 발동 시 기존 영어 텍스트 날리기)
                if token.contains("[RESET]") {
                    fullResponse = ""
                    continue
                }
                
                fullResponse += token
                
                // 화면 갱신
                if let lastIdx = messages.indices.last {
                    messages[lastIdx] = ChatMessage(text: fullResponse, isUser: false)
                }
            }
            
            // 완료
            isTyping = false
        }
    }
    
    private func scrollToBottom(proxy: ScrollViewProxy) {
        withAnimation {
            if isTyping {
                proxy.scrollTo("typingIndicator", anchor: .bottom)
            } else if let last = messages.last {
                proxy.scrollTo(last.id, anchor: .bottom)
            }
        }
    }
}

// MARK: - Models

struct ChatMessage: Identifiable {
    let id = UUID()
    let text: String
    let isUser: Bool
    let timestamp = Date()
}

struct ChatBubble: View {
    let message: ChatMessage
    
    var body: some View {
        HStack(alignment: .bottom, spacing: 8) {
            if !message.isUser {
                Image(systemName: "face.smiling.fill")
                .resizable()
                .scaledToFit()
                .frame(width: 30, height: 30)
                .foregroundColor(.purple)
                .background(Color.white)
                .clipShape(Circle())
                .shadow(radius: 1)
            } else {
                Spacer()
            }
            
            Text(message.text)
                .font(.system(size: 16))
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .background(message.isUser ? Color.blue : Color.gray.opacity(0.1))
                .foregroundColor(message.isUser ? .white : .black)
                .cornerRadius(20)
                .frame(maxWidth: 250, alignment: message.isUser ? .trailing : .leading)
            
            if message.isUser {
                // Avatar place holder if needed
            } else {
                Spacer()
            }
        }
        .padding(.horizontal, 16)
    }
}

struct TypingIndicator: View {
    @State private var offset: CGFloat = 0
    
    var body: some View {
        HStack(spacing: 4) {
            Circle().frame(width: 6, height: 6).offset(y: offset)
            Circle().frame(width: 6, height: 6).offset(y: -offset)
            Circle().frame(width: 6, height: 6).offset(y: offset)
        }
        .foregroundColor(.gray)
        .padding(12)
        .background(Color.gray.opacity(0.1))
        .cornerRadius(20)
        .onAppear {
            withAnimation(Animation.easeInOut(duration: 0.5).repeatForever(autoreverses: true)) {
                offset = 3
            }
        }
    }
}

// MARK: - Chat Report View
struct ChatReportView: View {
    @ObservedObject var authManager: AuthManager
    @Environment(\.presentationMode) var presentationMode
    
    @State private var reportData: ChatSummary?
    @State private var isLoading = true
    
    let baseURL = "http://150.230.7.76"
    
    var body: some View {
        NavigationView {
            VStack {
                if isLoading {
                    ProgressView("감정 분석 데이터 불러오는 중...")
                } else if let report = reportData {
                    if report.has_data {
                        ScrollView {
                            VStack(spacing: 24) {
                                // 1. Summary
                                VStack(spacing: 10) {
                                    Text("💬 최근 7일 대화 분석")
                                        .font(.headline)
                                        .foregroundColor(.gray)
                                    Text("\(report.total_chats ?? 0)건")
                                        .font(.system(size: 40, weight: .bold))
                                        .foregroundColor(.purple)
                                    Text("의 대화가 기록되었습니다.")
                                }
                                .padding()
                                
                                // 2. Emotions
                                VStack(alignment: .leading, spacing: 16) {
                                    Text("❤️ 주요 감정")
                                        .font(.headline)
                                    
                                    if let emotions = report.top_emotions {
                                        ForEach(emotions, id: \.emotion) { item in
                                            HStack {
                                                Text(item.emotion)
                                                    .fontWeight(.bold)
                                                    .frame(width: 80, alignment: .leading)
                                                
                                                GeometryReader { geo in
                                                    RoundedRectangle(cornerRadius: 10)
                                                        .fill(Color.purple.opacity(0.8))
                                                        .frame(width: max(geo.size.width * (CGFloat(item.count) / CGFloat(report.total_chats ?? 1)), 10))
                                                }
                                                .frame(height: 20)
                                                
                                                Text("\(item.count)")
                                                    .font(.caption)
                                                    .foregroundColor(.gray)
                                            }
                                        }
                                    }
                                }
                                .padding()
                                .background(Color.gray.opacity(0.1))
                                .cornerRadius(16)
                                .padding(.horizontal)
                                
                                // 3. Stress
                                VStack(alignment: .leading, spacing: 10) {
                                    Text("⚡️ 스트레스 지수")
                                        .font(.headline)
                                    
                                    HStack {
                                        Text("평온").font(.caption)
                                        Spacer()
                                        Text("높음").font(.caption)
                                    }
                                    
                                    GeometryReader { geo in
                                        ZStack(alignment: .leading) {
                                            RoundedRectangle(cornerRadius: 10)
                                                .fill(Color.gray.opacity(0.2))
                                                .frame(height: 20)
                                            
                                            RoundedRectangle(cornerRadius: 10)
                                                .fill(
                                                    LinearGradient(gradient: Gradient(colors: [.green, .yellow, .red]), startPoint: .leading, endPoint: .trailing)
                                                )
                                                .frame(width: geo.size.width * (CGFloat(report.avg_stress ?? 0) / 10.0), height: 20)
                                        }
                                    }
                                    .frame(height: 20)
                                    
                                    Text("평균: \(String(format: "%.1f", report.avg_stress ?? 0))점")
                                        .font(.caption).fontWeight(.bold).padding(.top, 4)
                                }
                                .padding()
                                .background(Color.gray.opacity(0.1))
                                .cornerRadius(16)
                                .padding(.horizontal)
                            }
                            .padding(.vertical)
                        }
                    } else {
                        VStack(spacing: 20) {
                            Text("📊").font(.largeTitle)
                            Text("데이터가 충분하지 않습니다.").font(.headline)
                            Text("채팅을 더 많이 하시면 분석해드려요!").foregroundColor(.gray)
                        }
                    }
                } else {
                    Text("데이터를 불러올 수 없습니다.")
                }
            }
            #if os(iOS)
            .navigationBarTitle("분석 리포트", displayMode: .inline)
            .navigationBarItems(trailing: Button("닫기") {
                presentationMode.wrappedValue.dismiss()
            })
            #endif
            .onAppear(perform: fetchReport)
        }
    }
    
    func fetchReport() {
        // [Local Mode] Report Mock
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            self.isLoading = false
            self.reportData = ChatSummary(has_data: true, total_chats: 42, avg_stress: 4.5, top_emotions: [
                ChatSummary.EmotionCount(emotion: "행복", count: 15),
                ChatSummary.EmotionCount(emotion: "불안", count: 10),
                ChatSummary.EmotionCount(emotion: "평온", count: 17)
            ])
        }
    }
}

struct ChatSummary: Codable {
    let has_data: Bool
    let total_chats: Int?
    let avg_stress: Double?
    let top_emotions: [EmotionCount]?
    
    struct EmotionCount: Codable {
        let emotion: String
        let count: Int
    }
}

// MARK: - SOS View (Emergency Contacts)
struct SOSView: View {
    @Environment(\.presentationMode) var presentationMode
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 24) {
                    // Header
                    VStack(spacing: 10) {
                        Image(systemName: "heart.circle.fill")
                        .font(.system(size: 60))
                        .foregroundColor(.red)
                        Text("당신은 혼자가 아닙니다")
                        .font(.title2)
                        .fontWeight(.bold)
                        Text("언제든 도움을 요청할 수 있어요.\n전문가와 이야기해보세요.")
                        .multilineTextAlignment(.center)
                        .foregroundColor(.gray)
                    }
                    .padding(.top, 20)
                    
                    // Contact Buttons
                    VStack(spacing: 16) {
                        ContactButton(title: "자살예방 상담전화", number: "1393", color: .blue)
                        ContactButton(title: "정신건강 위기상담", number: "1577-0199", color: .green)
                        ContactButton(title: "생명의 전화", number: "1588-9191", color: .orange)
                        ContactButton(title: "청소년 전화", number: "1388", color: .purple)
                    }
                    .padding()
                    
                    // Near Center Info
                    VStack(alignment: .leading, spacing: 10) {
                        Text("🏥 가까운 정신건강복지센터 찾기")
                        .font(.headline)
                        
                        Text("거주하시는 지역의 보건소나 정신건강복지센터에서 무료로 상담을 받으실 수 있습니다.")
                        .font(.caption)
                        .foregroundColor(.gray)
                        
                        Link("센터 찾기 (보건복지부)", destination: URL(string: "https://www.ncmh.go.kr")!)
                        .font(.body)
                        .foregroundColor(.blue)
                    }
                    .padding()
                    .background(Color.gray.opacity(0.1))
                    .cornerRadius(12)
                    .padding(.horizontal)
                    
                }
                .padding(.bottom)
            }
            #if os(iOS)
            .navigationBarTitle("긴급 도움 요청", displayMode: .inline)
            .navigationBarItems(trailing: Button("닫기") {
                presentationMode.wrappedValue.dismiss()
            })
            #endif
        }
    }
}

struct ContactButton: View {
    let title: String
    let number: String
    let color: Color
    
    var body: some View {
        Button(action: {
            if let url = URL(string: "tel://\(number.replacingOccurrences(of: "-", with: ""))") {
                #if os(iOS)
                UIApplication.shared.open(url)
                #endif
            }
        }) {
            HStack {
                VStack(alignment: .leading) {
                    Text(title).fontWeight(.bold)
                    Text(number).font(.title3)
                }
                Spacer()
                Image(systemName: "phone.fill")
                .font(.title2)
            }
            .padding()
            .foregroundColor(.white)
            .background(color)
            .cornerRadius(12)
            .shadow(radius: 2)
        }
    }
}
