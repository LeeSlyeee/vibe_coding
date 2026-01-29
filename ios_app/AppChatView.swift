
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
    
    // [New] SOS Crisis State
    @State private var isCrisis: Bool = false
    @State private var showSOSModal: Bool = false
    
    // Server Configuration
    let baseURL = "https://217.142.253.35.nip.io"
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // [New] Model Loading Indicator
                if !llmService.isModelLoaded {
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
                                    Text("안녕하세요!\n마음 속 이야기를 자유롭게 들려주세요.\n제가 경청하고 공감해드릴게요.")
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
                                HStack {
                                    TypingIndicator()
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
                        // [New] Trigger Model Load
                        if !llmService.isModelLoaded {
                            Task {
                                await llmService.loadModel()
                            }
                        }
                    }
                    .onChange(of: messages.count) { _ in
                        scrollToBottom(proxy: proxy)
                    }
                    .onChange(of: isTyping) { _ in
                        scrollToBottom(proxy: proxy)
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
                    TextField("메시지 보내기...", text: $inputText)
                        .padding(12)
                        .background(Color.gray.opacity(0.1))
                        .cornerRadius(20)
                        .disabled(isTyping)
                    
                    Button(action: sendMessage) {
                        Image(systemName: "paperplane.fill")
                            .font(.system(size: 20))
                            .foregroundColor(inputText.isEmpty ? .gray : .blue)
                            .padding(10)
                            .background(Color.blue.opacity(0.1))
                            .clipShape(Circle())
                    }
                    .disabled(inputText.isEmpty || isTyping)
                }
                .padding()
                .background(Color.white)
                .shadow(color: Color.black.opacity(0.05), radius: 5, x: 0, y: -5)
            }
            #if os(iOS)
            .navigationBarTitle("마음 톡(Talk)", displayMode: .inline)
            .navigationBarItems(leading: Button(action: { showReport = true }) {
                Image(systemName: "chart.pie.fill")
                    .foregroundColor(.black)
            })
            #endif
            .background(Color.white.edgesIgnoringSafeArea(.all))
            .sheet(isPresented: $showReport) {
                ChatReportView(authManager: authManager)
            }
            .sheet(isPresented: $showSOSModal) {
                SOSView()
            }
        }
    }
    
    private func sendMessage() {
        // [Critical Fix] 중복 실행 방지 가드는 맨 처음에!
        // 1. 입력값 및 상태 체크
        guard !isTyping else { return }
        guard !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        
        // 2. 상태 업데이트 (UI 즉시 반영)
        let userText = inputText
        inputText = ""
        isTyping = true 
        
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
            // 사용자가 "반복"을 지적하거나 짧게 따질 때, 과거 기억을 지워버려야(Cut-off) 고장난 루프에서 탈출 가능함.
            // 또한 메모리도 획기적으로 절약됨.
            // [Memory & Logic Fix] 상황별 컨텍스트 길이 조절 (Dynamic Context Window)
            // 사용자가 "반복"을 지적하거나 짧게 따질 때(30자 미만), 과거 기억을 지워버려야(Cut-off) 고장난 루프에서 탈출 가능함.
            // 하지만 "매일 똑같은 일을 해서 힘들어" 같은 긴 문장은 오탐지하면 안 되므로 길이 제한 추가!
            let triggers = ["반복", "그만", "똑같", "뭐하", "장난", "tq", "시발", "답답", "멍충", "바보"] 
            // 조건: (트리거 단어 포함) AND (문장이 30자보다 짧음) -> 화난 상태로 간주
            let isComplaint = (triggers.contains { userText.contains($0) }) && (userText.count < 30)
            
            // [Memory Fix] 10개는 OOM 발생함. 5개로 타협 (안정성 우선)
            let historyLimit = isComplaint ? 0 : 5 
            
            if isComplaint {
                print("🚨 [Dynamic Context] Complaint detected (Short Anger). Clearing history to break loop.")
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
            for await token in await LLMService.shared.generateAnalysis(diaryText: prompt) {
                // [RESET] 명령 감지 시 텍스트 초기화 (안전 장치 발동 시 기존 영어 텍스트 날리기)
                if token.contains("[RESET]") {
                    fullResponse = ""
                    // [RESET] 이후 문구는 새로고침됨.
                    // 만약 [RESET]과 텍스트가 섞여오면 분리해야 하지만, 
                    // LLMService에서 [RESET]을 단독 yield 하도록 설계하면 됨.
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
    
    let baseURL = "https://217.142.253.35.nip.io"
    
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
