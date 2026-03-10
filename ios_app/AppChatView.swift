
import SwiftUI

struct AppChatView: View {
    @EnvironmentObject var authManager: AuthManager
    @ObservedObject var llmService = LLMService.shared // [New] LLM 상태 관찰
    @State private var messages: [ChatMessage] = []
    @State private var inputText: String = ""
    @State private var isTyping: Bool = false
    @State private var scrollViewProxy: ScrollViewProxy? = nil
    
    
    // [UX] Cold Start Hint
    @State private var loadingHint: String? = nil
    
    // [New] SOS Crisis State
    @State private var isCrisis: Bool = false
    @State private var showSOSModal: Bool = false
    
    // [Gatekeeper] Mode Selection — 기본값 서버 AI, 네비게이션바 버튼으로 로컬 전환 가능
    @State private var showModeSelection: Bool = false
    
    // [New] Settings Modal State
    @State private var showSettings = false
    
    // [New] Focus State based Keyboard Handling
    @FocusState private var isInputFocused: Bool
    
    // [Keyboard Fix] Real keyboard height observer (AppMainTabView에서 주입)
    #if os(iOS)
    @EnvironmentObject var keyboardObserver: KeyboardObserver
    
    // 하단 Safe Area 높이 (Home Indicator 영역)
    // [Keyboard Fix] keyWindow 기준으로 안전하게 safeArea 읽기
    private var safeAreaBottom: CGFloat {
        UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap { $0.windows }
            .first(where: { $0.isKeyWindow })?.safeAreaInsets.bottom ?? 0
    }
    #endif
    
    // Server Configuration
    // [Target Fix] Updated to 217 Server
    let baseURL = "https://217.142.253.35.nip.io/api"
    
    var body: some View {
        ZStack {
            // Main Chat UI
            NavigationView {
                VStack(spacing: 0) {
                    // [Keyboard Fix] SwiftUI 자동 키보드 회피를 차단하고 수동으로만 처리
                    // [New] Model Loading Indicator (로컬 AI 모드에서만 표시)
                    if !llmService.useServerAI && !llmService.isModelLoaded && llmService.modelLoadingProgress > 0 {
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

                    // On-Device 보안 배지
                    if !llmService.useServerAI {
                        HStack(spacing: 4) {
                            Image(systemName: "lock.shield.fill")
                                .font(.system(size: 10))
                                .foregroundColor(.green)
                            Text("이 대화는 폰 안에서만 처리됩니다")
                                .font(.system(size: 11))
                                .foregroundColor(.gray)
                        }
                        .padding(.vertical, 4)
                        .padding(.horizontal, 12)
                        .background(Color.green.opacity(0.08))
                        .cornerRadius(12)
                        .padding(.top, 4)
                    }

                    // Chat List
                    ScrollViewReader { proxy in
                        ScrollView {
                            LazyVStack(spacing: 12) {
                                // Intro Message
                                if messages.isEmpty {
                                    VStack(spacing: 10) {
                                        Image(systemName: "hand.wave.fill").foregroundColor(.yellow)
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
                                        let welcomeText = "안녕하세요, \(userName)님!\n\n저는 AI 감정 케어 도우미 '마음온'이에요.\n전문 상담사는 아니지만, 당신의 이야기를 조용히 들을 준비가 되어 있어요.\n\n오늘 하루 중 기억에 남는 순간이 있었나요?"
                                        
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
                        // [Keyboard Fix] simultaneousGesture로 변경하여 scrollDismissesKeyboard와 충돌 방지
                        .simultaneousGesture(
                            TapGesture().onEnded {
                                #if os(iOS)
                                dismissKeyboard()
                                #endif
                            }
                        )
                        #if os(iOS)
                        .scrollDismissesKeyboard(.interactively)
                        #endif
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
                        TextField("메시지 보내기...", text: $inputText)
                            .focused($isInputFocused)
                            .keyboardType(.default)
                            .autocorrectionDisabled(false)
                            .tint(.blue) // [Fix] 커서 색상 명시적 설정 (입력 상태 시각적 피드백)
                            .padding(12)
                            .background(Color.gray.opacity(0.1))
                            .cornerRadius(20)
                            .disabled(showModeSelection)
                        
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
                    // [Keyboard Fix] 키보드가 올라오면 탭바 패딩(60)을 제거하고,
                    // 키보드 높이만큼 패딩 적용 (SwiftUI 자동 회피는 .ignoresSafeArea로 차단됨)
                    #if os(iOS)
                    .padding(.bottom, keyboardObserver.isKeyboardVisible
                        ? max(keyboardObserver.keyboardHeight - safeAreaBottom, 0)
                        : 60)
                    .animation(.easeOut(duration: 0.16), value: keyboardObserver.isKeyboardVisible)
                    #else
                    .padding(.bottom, 60)
                    #endif
                    .background(Color.white)
                    .shadow(color: Color.black.opacity(0.05), radius: 5, x: 0, y: -5)
                }
                // [Keyboard Fix] SwiftUI 자동 키보드 회피 비활성화 (수동 패딩으로 대체)
                #if os(iOS)
                .ignoresSafeArea(.keyboard, edges: .bottom)
                // [Keyboard Fix] 키보드가 내려가면 FocusState 동기화 (다시 터치 시 키보드 올라오도록)
                .onChangeCompat(of: keyboardObserver.isKeyboardVisible) { visible in
                    if !visible {
                        isInputFocused = false
                    } else if visible && !isInputFocused {
                        // [Keyboard Fix] 양방향 동기화: 키보드가 올라왔는데 Focus가 풀린 경우 복원
                        // (키보드 언어 전환 시 Hide→Show 사이클에서 Focus 유실 방지)
                        isInputFocused = true
                    }
                }
                .navigationBarTitle("한마디", displayMode: .inline)
                .navigationBarItems(
                    leading: Button(action: {
                        llmService.toggleAIMode()
                        // 로컬 모드 전환 시 모델 로드
                        if !llmService.useServerAI && !llmService.isModelLoaded {
                            Task { await llmService.loadModel() }
                        }
                    }) {
                        Text(llmService.useServerAI ? "서버 AI" : "로컬 AI")
                            .font(.system(size: 12, weight: .bold))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(llmService.useServerAI ? Color.blue.opacity(0.15) : Color.green.opacity(0.15))
                            .foregroundColor(llmService.useServerAI ? .blue : .green)
                            .cornerRadius(8)
                    }
                    .disabled(isTyping),
                    trailing: Button(action: { showSettings = true }) {
                        Image(systemName: "gearshape.fill")
                            .foregroundColor(.black)
                    }
                )
                #endif
                .background(Color.white.edgesIgnoringSafeArea(.all))
                .sheet(isPresented: $showSOSModal) {
                    SOSView()
                }
                .sheet(isPresented: $showSettings) {
                    NavigationView {
                        AppSettingsView()
                            .environmentObject(authManager)
                            .navigationBarItems(trailing: Button("닫기") {
                                showSettings = false
                            })
                    }
                }
            }
            .blur(radius: showModeSelection ? 5 : 0) // Blur background
            .screenshotProtected(isProtected: true) // [보안 Fix] 민감한 상담 로그 보호
            
            // [Gatekeeper] AI Mode Selection Overlay
            // [Gatekeeper] 서버 AI 전용 — 모드 선택 오버레이 비활성
            // 로컬 LLM은 일기 분석 전용으로만 사용 (채팅에서는 서버 AI 강제)
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
                withAnimation { self.loadingHint = "AI가 마음의 준비를 하고 있어요...\n(서버가 깨어나는 중입니다)" }
            }
            
            try? await Task.sleep(nanoseconds: 6 * 1_000_000_000) // +6초 (총 10초)
            if isTyping && (messages.last?.isUser == true || messages.last?.text.isEmpty == true) {
                withAnimation { self.loadingHint = "거의 다 되었습니다! 잠시만요..." }
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
            } else {
            }
            
            // [Phase 4] 3단계 위기 분류 시스템
            let crisisLevel3 = ["죽고", "자살", "뛰어내", "목을", "손목", "유서", "마지막", "끝내고", "자해", "목숨"]
            let crisisLevel2 = ["사라지고", "없어지고", "살기 싫", "의미 없", "끝내", "망했", "수면제", "칼", "약 먹", "다 끝"]
            let crisisLevel1 = ["힘들", "지치", "우울", "불안", "두렵", "외로", "무서", "포기", "눈물"]
            
            if crisisLevel3.contains(where: { userText.contains($0) }) {
                withAnimation {
                    self.isCrisis = true
                    self.showSOSModal = true // Level 3: 즉시 모달 팝업
                }
            } else if crisisLevel2.contains(where: { userText.contains($0) }) {
                withAnimation {
                    self.isCrisis = true // Level 2: SOS 배너 표시
                }
            } else if crisisLevel1.contains(where: { userText.contains($0) }) {
                // Level 1: 기본 공감 모드 (배너 미노출, AI가 공감 대응)
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
                        HStack { Image(systemName: "cross.case.fill"); Text("가까운 정신건강복지센터 찾기") }
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
