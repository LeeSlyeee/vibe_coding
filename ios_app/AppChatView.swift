
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
    
    // [Gatekeeper] Mode Selection
    @State private var showModeSelection: Bool = false
    
    // [New] Settings Modal State
    @State private var showSettings = false
    
    // [New] Focus State based Keyboard Handling
    @FocusState private var isInputFocused: Bool
    
    // [Guided Diary Flow]
    @State private var currentStepIndex: Int = 0
    @State private var collectedAnswers: [String] = ["", "", "", "", "", ""]
    @State private var isFreeChatMode: Bool = false // 자유 대화 모드 (일기 완료 후 활성화)
    // [P1-1 Fix] 질문 풀(Pool) — 동일 구조 유지하면서 매일 다른 표현
    private let stepQuestionPool: [[String]] = [
        [ // 1 (수면)
            "어젯밤 잠은 어떻게 주무셨나요? 푹 쉬셨기를 바라요.",
            "어젯밤 수면은 어떠셨어요? 충분히 쉬셨는지 궁금해요.",
            "잠은 잘 주무셨나요? 꿈도 꾸셨는지 궁금하네요.",
            "어제 밤 잠자리는 편안했나요? 마음이가 궁금해해요 😊"
        ],
        [ // 2 (사건)
            "그렇군요. 그럼 오늘 하루 어떤 일들이 있었는지 편하게 말씀해주세요.",
            "오늘 하루는 어떻게 보내셨어요? 기억에 남는 일이 있다면 들려주세요.",
            "오늘 어떤 일들이 있었나요? 크든 작든 상관없이 편하게 얘기해주세요.",
            "그렇군요! 그럼 오늘 하루 중 마음에 남은 장면이 있다면 말씀해주세요."
        ],
        [ // 3 (감정)
            "그 경험을 하면서 어떤 감정이 들었는지 말씀해주시겠어요?",
            "그때 어떤 기분이 들었나요? 솔직하게 표현해주시면 좋겠어요.",
            "그 순간 어떤 마음이었는지 떠올려볼까요?",
            "그런 일이 있었군요. 그때 느꼈던 감정을 자유롭게 적어주세요."
        ],
        [ // 4 (의미)
            "왜 그런 감정이 들었는지, 나에게 어떤 의미였는지 조금 더 깊이 생각해 볼까요?",
            "그 감정이 왜 올라왔을까요? 나에게 어떤 의미가 있는지 살펴볼까요?",
            "조금 더 들어가볼게요. 그 감정이 어디서 왔는지 탐색해볼까요?",
            "그 감정이 나에게 무엇을 말해주고 있을까요? 천천히 생각해봐요."
        ],
        [ // 5 (독백/위로)
            "오늘 하루도 정말 고생 많으셨어요. 힘든 나에게 따뜻한 위로의 한마디를 남겨주세요.",
            "수고한 오늘의 나에게 한마디 해준다면 뭐라고 말해주고 싶나요?",
            "오늘 하루 고생한 자신에게 따뜻한 말 한마디 건네볼까요?",
            "마지막으로, 오늘 힘들었던 나 자신을 토닥여주는 말을 남겨주세요 💛"
        ]
    ]
    
    /// 질문 풀에서 랜덤으로 하나 선택 (인덱스 기반)
    private func getStepQuestion(for index: Int) -> String {
        guard index >= 0 && index < stepQuestionPool.count else { return "" }
        let pool = stepQuestionPool[index]
        return pool.randomElement() ?? pool[0]
    }
    
    // [Keyboard Fix] Real keyboard height observer
    #if os(iOS)
    @StateObject private var keyboardObserver = KeyboardObserver()
    
    // 하단 Safe Area 높이
    private var safeAreaBottom: CGFloat {
        UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap { $0.windows }
            .first(where: { $0.isKeyWindow })?.safeAreaInsets.bottom ?? 0
    }
    #endif
    
    // Server Configuration - APIService.swift > ServerConfig 에서 관리
    let baseURL = ServerConfig.apiBase
    
    var body: some View {
        ZStack {
            // Main Chat UI
            NavigationView {
                VStack(spacing: 0) {
                    if !llmService.useServerAI && !llmService.isModelLoaded && llmService.modelLoadingProgress > 0 {
                        VStack(spacing: 8) {
                            Text(llmService.modelLoadingProgress > 0 ? "🔒 보안 캡슐 활성화 및 가중치 전송 완료! (준비 중...)" : "🔒 로컬 AI 엔진 기동 대기 중...")
                                .font(.caption)
                                .foregroundColor(.mood4)
                            ProgressView(value: llmService.modelLoadingProgress)
                                .progressViewStyle(LinearProgressViewStyle())
                                .accentColor(.mood4)
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
                                .foregroundColor(.mood4)
                            Text("완벽히 단절된 안전지대 (데이터는 폰 안에만 머뭅니다)")
                                .font(.system(size: 11))
                                .foregroundColor(.hintText)
                            Spacer()
                            Text("Off-Grid")
                                .font(.system(size: 9, weight: .bold))
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.mood4)
                                .foregroundColor(.white)
                                .cornerRadius(4)
                        }
                        .padding(.vertical, 6)
                        .padding(.horizontal, 12)
                        .background(Color.mood4.opacity(0.08))
                        .cornerRadius(12)
                        .padding(.top, 4)
                        .padding(.horizontal, 16)
                    } else {
                        // 서버 모드 배지 (Opt-In & Anonymization)
                        HStack(spacing: 4) {
                            Image(systemName: "shield.righthalf.filled")
                                .font(.system(size: 10))
                                .foregroundColor(.accent)
                            Text("전문가 심층 분석 (개인정보는 익명화되어 전송됩니다)")
                                .font(.system(size: 11))
                                .foregroundColor(.hintText)
                            Spacer()
                            Text("Opt-In")
                                .font(.system(size: 9, weight: .bold))
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.accent)
                                .foregroundColor(.white)
                                .cornerRadius(4)
                        }
                        .padding(.vertical, 6)
                        .padding(.horizontal, 12)
                        .background(Color.accent.opacity(0.08))
                        .cornerRadius(12)
                        .padding(.top, 4)
                        .padding(.horizontal, 16)
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
                                        Text(llmService.useServerAI ? "마음이가 오늘 하루를 함께 돌아봐드릴게요.\n안내에 따라 답하다 보면 일기가 완성됩니다." : "마음이에게 어떤 감정이든 쏟아내세요.\n안전지대에서 함께 정리해볼까요?")
                                            .multilineTextAlignment(.center)
                                            .font(.body)
                                            .foregroundColor(.hintText)
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
                                                .foregroundColor(hint.contains("🔒") ? .mood4 : (hint.contains("🛡️") ? .accent : .hintText))
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
                            
                            // [Sync & Greeting + 오늘 일기 체크]
                            APIService.shared.syncUserInfo { success in
                                DispatchQueue.main.async {
                                    var userName = UserDefaults.standard.string(forKey: "realName") 
                                                ?? UserDefaults.standard.string(forKey: "userNickname") 
                                                ?? "회원"
                                    
                                    if userName.hasPrefix("User ") || userName.hasPrefix("user_") {
                                        userName = "회원"
                                    }
                                    
                                    // 이미 메시지가 있으면 인사 생략
                                    guard messages.isEmpty else { return }
                                    
                                    // 오늘 날짜 계산
                                    let f = DateFormatter()
                                    f.dateFormat = "yyyy-MM-dd"
                                    f.timeZone = TimeZone.current
                                    let todayStr = f.string(from: Date())
                                    
                                    // 오늘 일기가 이미 존재하는지 확인
                                    let todayDiary = LocalDataManager.shared.diaries.first(where: { $0.date == todayStr })
                                    
                                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                                        guard messages.isEmpty else { return }
                                        
                                        if let diary = todayDiary {
                                            // ━━━ 오늘 일기 존재 → 자유 대화 모드로 시작 ━━━
                                            var contextMsg = "안녕하세요, \(userName)님! 👋 마음이예요.\n\n오늘 이미 일기를 작성해주셨네요 ✨\n"
                                            if let event = diary.event, !event.isEmpty {
                                                contextMsg += "오늘 있었던 일: \(String(event.prefix(80)))\n"
                                            }
                                            if let emotion = diary.emotion_desc, !emotion.isEmpty {
                                                contextMsg += "느낀 감정: \(String(emotion.prefix(80)))\n"
                                            }
                                            contextMsg += "\n더 이야기하고 싶은 게 있으시면 편하게 말씀해주세요. 💬"
                                            
                                            withAnimation {
                                                messages.append(ChatMessage(text: contextMsg, isUser: false))
                                                currentStepIndex = 6
                                                isFreeChatMode = true
                                            }
                                        } else {
                                            // ━━━ 오늘 일기 없음 → 기존 6단계 가이드 플로우 시작 ━━━
                                            let welcomeText = "안녕하세요, \(userName)님! 마음이예요 💛\n오늘 하루를 편안하게 돌아보는 시간을 가져볼까요?\n\n가장 먼저, 혹시 챙겨 드시는 약이 있다면 오늘 잘 복용하셨나요?\n(없다면 '없다'고 말씀해주셔도 좋아요)"
                                            
                                            withAnimation {
                                                messages.append(ChatMessage(text: welcomeText, isUser: false))
                                            }
                                        }
                                    }
                                }
                            }

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
                        #if os(iOS)
                        // [Cursor Fix] UIKit 기반: 메시지 영역 탭 시 키보드 닫기 (입력 필드 포커스 방해 없음)
                        .dismissKeyboardOnTap()
                        #endif
                    }
                    
                    // Crisis Banner
                    if isCrisis {
                        Button(action: { showSOSModal = true }) {
                            HStack {
                                Image(systemName: "exclamationmark.triangle.fill")
                                    .foregroundColor(.white)
                                    .padding(.trailing, 4)
                                Text("도움이 필요하신가요? (긴급 연락처)")
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
                        TextField(isFreeChatMode ? "마음이에게 자유롭게 이야기해보세요..." : "메시지 보내기...", text: $inputText)
                            .focused($isInputFocused)
                            .keyboardType(.default)
                            .autocorrectionDisabled(false)
                            .tint(.accent)
                            .padding(12)
                            .background(Color.softTan.opacity(0.3))
                            .cornerRadius(20)
                            .disabled(showModeSelection || (currentStepIndex >= 6 && !isFreeChatMode))
                        
                        Button(action: sendMessage) {
                            Image(systemName: "paperplane.fill")
                                .font(.system(size: 20))
                                .foregroundColor(inputText.isEmpty ? .hintText : .accent)
                                .padding(10)
                                .background(Color.accent.opacity(0.10))
                                .clipShape(Circle())
                        }
                        .disabled(inputText.isEmpty || showModeSelection || (currentStepIndex >= 6 && !isFreeChatMode) || (!isFreeChatMode && isTyping))
                    }
                    .padding()
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
                #if os(iOS)
                .ignoresSafeArea(.keyboard, edges: .bottom)
                .onChangeCompat(of: keyboardObserver.isKeyboardVisible) { visible in
                    if !visible {
                        isInputFocused = false
                    } else if visible && !isInputFocused {
                        isInputFocused = true
                    }
                }
                .navigationBarTitle("한마디", displayMode: .inline)
                .navigationBarItems(
                    leading: Button(action: {
                        llmService.toggleAIMode()
                        if !llmService.useServerAI && !llmService.isModelLoaded {
                            Task { await llmService.loadModel() }
                        }
                    }) {
                        Text(llmService.useServerAI ? "서버 AI" : "로컬 AI")
                            .font(.system(size: 12, weight: .bold))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(llmService.useServerAI ? Color.accent.opacity(0.15) : Color.mood4.opacity(0.15))
                            .foregroundColor(llmService.useServerAI ? .accent : .mood4)
                            .cornerRadius(8)
                    }
                    .disabled(isTyping),
                    trailing: Button(action: { showSettings = true }) {
                        Image(systemName: "gearshape.fill")
                            .foregroundColor(.primaryText)
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
            .screenshotProtected() // [보안] 스크린샷 방지 (설정에 따라 동작)
        }
    }
    
    private func sendMessage() {
        guard !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        
        // 자유 대화 모드이면 별도 처리 (AI 응답 중에도 메시지 전송 가능)
        if isFreeChatMode {
            sendFreeChat()
            return
        }
        
        // 가이드 플로우에서는 AI 응답 중 입력 차단
        guard !isTyping else { return }
        
        guard currentStepIndex < 6 else { return } // 평가 6단계(0~5 인덱스)
        
        let userText = inputText
        inputText = ""
        isTyping = true 
        
        // Haptic Feedback
        #if os(iOS)
        let generator = UIImpactFeedbackGenerator(style: .medium)
        generator.impactOccurred()
        #endif
        
        // 사용자 메시지 추가
        messages.append(ChatMessage(text: userText, isUser: true))
        
        // 데이터 보관
        collectedAnswers[currentStepIndex] = userText
        currentStepIndex += 1
        
        Task {
            // [P0-2 Fix] 위기 감지 — 확장 키워드 + 우회 표현 + 문맥 판별
            if Self.detectCrisis(in: userText) {
                await MainActor.run {
                    self.isCrisis = true
                    self.showSOSModal = true
                }
            }
            
            // 타이핑 딜레이 약간
            try? await Task.sleep(nanoseconds: 1_200_000_000)
            
            await MainActor.run {
                if self.currentStepIndex < 6 {
                    self.isTyping = false
                    messages.append(ChatMessage(text: self.getStepQuestion(for: self.currentStepIndex - 1), isUser: false))
                } else if self.currentStepIndex == 6 {
                    messages.append(ChatMessage(text: "소중한 이야기들을 나눠주셔서 감사해요.\n다이어리를 기록하고 감정을 분석해 드릴게요. 잠시만 기다려주세요.", isUser: false))
                    self.startFinalAnalysis()
                }
            }
        }
    }
    
    private func startFinalAnalysis() {
        self.loadingHint = "📝 일기장에 기록을 옮기는 중..."
        self.isTyping = true
        
        let qMed = collectedAnswers[0] // medication
        let qs = collectedAnswers[1] // sleep
        let q1 = collectedAnswers[2] // event
        let q2 = collectedAnswers[3] // emotion
        let q3 = collectedAnswers[4] // meaning
        let q4 = collectedAnswers[5] // selftalk
        
        // [P0-1 Fix] 약물 섭취 여부 유추 — 부정어 필터링 추가
        let hasTakenMed = Self.parseMedicationTaken(from: qMed)
        
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        f.timeZone = TimeZone.current 
        let dateString = f.string(from: Date())
        
        // [P0 Fix] WeatherKit 실시간 날씨 조회 (하드코딩 "맑음" 제거)
        Task {
            let weatherData = await WeatherService.shared.fetchTodayWeather()
            
            await MainActor.run {
                self.continueAnalysis(
                    dateString: dateString, qMed: qMed, qs: qs, q1: q1, q2: q2, q3: q3, q4: q4,
                    hasTakenMed: hasTakenMed,
                    weather: weatherData.weather,
                    temperature: weatherData.temperature
                )
            }
        }
    }
    
    /// startFinalAnalysis()의 후속 처리 — 날씨 조회 완료 후 Diary 생성 및 AI 분석 시작
    private func continueAnalysis(
        dateString: String, qMed: String, qs: String, q1: String, q2: String, q3: String, q4: String,
        hasTakenMed: Bool,
        weather: String,
        temperature: Double
    ) {
        var newDiary = Diary(
            id: UUID().uuidString,
            _id: nil,
            date: dateString,
            mood_level: 3, // 기본값
            event: q1,
            emotion_desc: q2,
            emotion_meaning: q3,
            self_talk: q4,
            sleep_desc: qs,
            weather: weather,
            temperature: temperature,
            created_at: nil,
            medication: hasTakenMed,
            medication_desc: qMed
        )
        
        newDiary.ai_prediction = "분석 대기 중..."
        
        // 1. 다이어리 로컬 저장
        LocalDataManager.shared.saveDiary(newDiary) { success in
            // 서버/로컬 AI 추론
            Task {
                let combinedText = "투약여부: \(qMed)\n사건: \(q1)\n감정: \(q2)\n의미: \(q3)\n혼잣말: \(q4)\n수면: \(qs)"
                let analyzeSystemInstruction = "[일기 전체를 요약하고, 사용자의 감정에 공감하며 한 문단의 따뜻한 조언을 제공하세요. 반드시 한국어를 사용하세요.]\n\n\(combinedText)"
                
                await MainActor.run {
                    self.loadingHint = !llmService.useServerAI ? "🔒 AI 마음 가이드 생성 중... (데이터는 보호됩니다)" : "🛡️ 마음 가이드 생성 중..."
                    messages.append(ChatMessage(text: "", isUser: false)) 
                }
                
                var fullResponse = ""
                
                for await token in await LLMService.shared.generateAnalysis(
                    diaryText: combinedText, 
                    userText: analyzeSystemInstruction, // Server mode triggers chat endpoint
                    historyString: "사용자가 방금 남긴 일기 기록입니다."
                ) {
                    await MainActor.run {
                        if self.loadingHint != nil { self.loadingHint = nil }
                        
                        if token.contains("[RESET]") {
                            fullResponse = ""
                            if let lastIdx = self.messages.indices.last {
                                self.messages[lastIdx] = ChatMessage(text: fullResponse, isUser: false)
                            }
                        } else {
                            fullResponse += token
                            if let lastIdx = self.messages.indices.last {
                                self.messages[lastIdx] = ChatMessage(text: fullResponse, isUser: false)
                            }
                        }
                    }
                }
                
                // 추론 완료 후 다이어리 필드 업데이트
                await MainActor.run {
                    self.isTyping = false
                    if let index = LocalDataManager.shared.diaries.firstIndex(where: { $0.id == newDiary.id }) {
                        LocalDataManager.shared.diaries[index].ai_analysis = fullResponse
                        LocalDataManager.shared.saveDiary(LocalDataManager.shared.diaries[index]) { _ in }
                    }
                    
                    // 채팅 종료 멘트 + 자유 대화 전환
                    DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                        self.messages.append(ChatMessage(text: "분석을 마치고 일기장에 보관해두었어요.\n오늘 하루도 수고 많으셨습니다. 😊", isUser: false))
                        
                        // 자유 대화 전환 안내
                        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                            self.messages.append(ChatMessage(text: "더 이야기하고 싶은 게 있으시면 편하게 말씀해주세요.\n오늘 있었던 일, 지금 느끼는 감정 등 자유롭게 대화할 수 있어요. 💬", isUser: false))
                            self.isFreeChatMode = true
                        }
                    }
                }
            }
        }
    }
    
    /// 자유 대화 모드 — 6단계 일기 작성 완료 후 활성화
    /// 이전 대화 기록을 history에 포함시켜 서버 AI에 전달
    private func sendFreeChat() {
        let userText = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        inputText = ""
        isTyping = true
        
        // Haptic Feedback
        #if os(iOS)
        let generator = UIImpactFeedbackGenerator(style: .medium)
        generator.impactOccurred()
        #endif
        
        // 사용자 메시지 추가
        messages.append(ChatMessage(text: userText, isUser: true))
        
        // [P0-2 Fix] 위기 감지 (자유 대화 중에도 동작) — 확장 버전
        if Self.detectCrisis(in: userText) {
            self.isCrisis = true
            self.showSOSModal = true
        }
        
        Task {
            // 이전 대화 기록을 history 문자열로 조합 (최근 10턴 = 20개 메시지)
            let recentMessages = Array(messages.suffix(20))
            let historyStr = recentMessages.dropLast() // 방금 추가한 userMsg 제외
                .map { msg in
                    if msg.isUser {
                        return "User: \(String(msg.text.prefix(100)))"
                    } else {
                        return "AI: \(String(msg.text.prefix(100)))"
                    }
                }
                .joined(separator: "\n")
            
            if llmService.useServerAI {
                // 서버 AI 모드: APIService 직접 호출
                let serverResponse: String? = await withCheckedContinuation { continuation in
                    APIService.shared.sendChatMessage(text: userText, history: historyStr) { result in
                        switch result {
                        case .success(let response):
                            continuation.resume(returning: response)
                        case .failure:
                            continuation.resume(returning: nil)
                        }
                    }
                }
                
                await MainActor.run {
                    let responseText = serverResponse ?? LLMService.shared.getEmergencyEmpathy(for: userText)
                    self.messages.append(ChatMessage(text: responseText, isUser: false))
                    self.isTyping = false
                }
            } else {
                // 로컬 AI 모드: LLMService 스트리밍
                await MainActor.run {
                    self.messages.append(ChatMessage(text: "", isUser: false))
                }
                
                var fullResponse = ""
                for await token in await LLMService.shared.generateAnalysis(
                    diaryText: userText,
                    userText: userText,
                    historyString: historyStr
                ) {
                    await MainActor.run {
                        if token.contains("[RESET]") {
                            fullResponse = ""
                        } else {
                            fullResponse += token
                        }
                        if let lastIdx = self.messages.indices.last {
                            self.messages[lastIdx] = ChatMessage(text: fullResponse, isUser: false)
                        }
                    }
                }
                
                // 로컬 AI 응답이 비었으면 fallback
                if fullResponse.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    await MainActor.run {
                        let fallback = LLMService.shared.getEmergencyEmpathy(for: userText)
                        if let lastIdx = self.messages.indices.last {
                            self.messages[lastIdx] = ChatMessage(text: fallback, isUser: false)
                        }
                    }
                }
                
                await MainActor.run {
                    self.isTyping = false
                }
            }
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
    
    // MARK: - [P0-1] 약물 복용 파싱 (부정어 필터링)
    /// "안 먹었어", "못 먹었어", "없어" 등 부정 표현을 먼저 검사하여 오판 방지
    static func parseMedicationTaken(from text: String) -> Bool {
        let t = text.trimmingCharacters(in: .whitespacesAndNewlines)
        
        // 1) 명시적 부정 표현 → false
        let negativePatterns = [
            "안 먹", "안먹", "못 먹", "못먹", "안 챙", "안챙",
            "까먹", "깜빡", "놓쳤", "빠뜨", "빼먹",
            "없어", "없다", "없습", "없음",
            "안 했", "안했", "하지 않", "아니", "아닌", "아뇨", "아니요", "아니오",
            "ㄴㄴ", "ㄴ", "노", "no", "No", "NO", "nope", "x", "X"
        ]
        if negativePatterns.contains(where: { t.contains($0) }) {
            return false
        }
        
        // 2) 명시적 긍정 표현 → true
        let positivePatterns = [
            "먹었", "먹음", "챙겼", "챙김", "복용", "먹고",
            "네", "응", "ㅇㅇ", "ㅇ", "Y", "y", "yes", "Yes",
            "했어", "했습", "완료"
        ]
        if positivePatterns.contains(where: { t.contains($0) }) {
            return true
        }
        
        // 3) 판별 불가 → false (안전 기본값)
        return false
    }
    
    // MARK: - [P0-2] 위기 감지 (확장 키워드 + 우회 표현)
    /// 직접적 위기 표현 + 우회적 위기 표현을 모두 감지
    /// "마지막" 등 오탐 가능 키워드는 문맥 필터 적용
    static func detectCrisis(in text: String) -> Bool {
        // 1) 직접적 위기 표현 (높은 확신)
        let directCrisis = [
            "죽고", "죽을", "죽겠", "죽자", "죽어",
            "자살", "자해",
            "뛰어내", "뛰어 내",
            "목을 매", "목매", "목을매",
            "손목을 긋", "손목 긋", "손목긋", "손목을",
            "유서",
            "끝내고", "끝내자", "끝내려", "끝낼",
            "목숨",
            "살고 싶지", "살기 싫"
        ]
        if directCrisis.contains(where: { text.contains($0) }) {
            return true
        }
        
        // 2) 우회적 위기 표현 (간접적이지만 위험)
        let indirectCrisis = [
            "없어지고 싶", "없어지면", "없어졌으면",
            "사라지고 싶", "사라져버", "사라졌으면",
            "더 이상 못", "더이상 못",
            "세상에 있고 싶지",
            "다 필요 없", "다 필요없",
            "다 끝났", "다 끝나",
            "이 세상을 떠", "세상을 떠나",
            "태어나지 말", "태어나지 않",
            "짐이 되", "짐만 되",
            "나만 없으면", "내가 없으면",
            "모든 게 끝", "모든게 끝",
            "아무 의미", "무의미",
            "살아있는 게", "살아있는게"
        ]
        if indirectCrisis.contains(where: { text.contains($0) }) {
            return true
        }
        
        // 3) "마지막" — 문맥 판별 (시험, 주 마지막 등 일상적 사용 제외)
        if text.contains("마지막") {
            let safeContexts = ["시험", "학기", "수업", "회의", "날", "주", "여행", "영화", "선물", "식사", "저녁", "버스", "전화", "인사"]
            let hasSafeContext = safeContexts.contains(where: { text.contains($0) })
            if !hasSafeContext {
                return true
            }
        }
        
        return false
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
                // [P1-2] "마음이" 캐릭터 아바타
                VStack(spacing: 2) {
                    Image(systemName: "heart.circle.fill")
                        .resizable()
                        .scaledToFit()
                        .frame(width: 32, height: 32)
                        .foregroundColor(.accent)
                        .background(Color.white)
                        .clipShape(Circle())
                        .shadow(color: Color.accent.opacity(0.3), radius: 3)
                    Text("마음이")
                        .font(.system(size: 9, weight: .medium))
                        .foregroundColor(.secondaryText)
                }
            } else {
                Spacer()
            }
            
            Text(message.text)
                .font(.system(size: 16))
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .background(message.isUser ? Color.accent : Color.softTan.opacity(0.3))
                .foregroundColor(message.isUser ? .white : .primaryText)
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
        .foregroundColor(.hintText)
        .padding(12)
        .background(Color.softTan.opacity(0.3))
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
                        .foregroundColor(.hintText)
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
                        .foregroundColor(.hintText)
                        
                        Link("센터 찾기 (보건복지부)", destination: URL(string: "https://www.ncmh.go.kr")!)
                        .font(.body)
                        .foregroundColor(.accent)
                    }
                    .padding()
                    .background(Color.softTan.opacity(0.3))
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
