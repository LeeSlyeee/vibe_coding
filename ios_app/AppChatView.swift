
import SwiftUI

struct AppChatView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var messages: [ChatMessage] = []
    @State private var inputText: String = ""
    @State private var isTyping: Bool = false
    @State private var scrollViewProxy: ScrollViewProxy? = nil
    
    // Phase 2: Report Modal State
    @State private var showReport = false
    
    // Server Configuration
    let baseURL = "https://217.142.253.35.nip.io"
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
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
                    }
                    .onChange(of: messages.count) { _ in
                        scrollToBottom(proxy: proxy)
                    }
                    .onChange(of: isTyping) { _ in
                        scrollToBottom(proxy: proxy)
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
            .navigationBarItems(trailing: Button(action: { showReport = true }) {
                Image(systemName: "chart.pie.fill")
                    .foregroundColor(.black)
            })
            #endif
            .background(Color.white.edgesIgnoringSafeArea(.all))
            .sheet(isPresented: $showReport) {
                ChatReportView(authManager: authManager)
            }
        }
    }
    
    private func sendMessage() {
        guard !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        
        let userText = inputText
        let userMsg = ChatMessage(text: userText, isUser: true)
        messages.append(userMsg)
        inputText = ""
        isTyping = true
        
        // Haptic Feedback
        #if os(iOS)
        let generator = UIImpactFeedbackGenerator(style: .medium)
        generator.impactOccurred()
        #endif
        
        // Local AI Chat
        guard !isTyping else { return }
        isTyping = true
        
        Task {
            // Combine history
            // (Simple history combining - just last few messages)
            let historyCount = min(messages.count, 6)
            let recentMessages = messages.suffix(historyCount)
            var historyContext = ""
            for msg in recentMessages {
                let role = msg.isUser ? "User" : "Model"
                historyContext += "\(role): \(msg.text)\n"
            }
            
            // System Prompt is now handled in LLMService
            let prompt = """
            [대화 내역]
            \(historyContext)
            
            User: \(userText)
            """
            
            // Streaming Response
            var fullResponse = ""
            var responseMsgId = UUID()
            
            // Add placeholder message first
            await MainActor.run {
                messages.append(ChatMessage(text: "", isUser: false)) // Placeholder
            }
            
            for await token in await LLMService.shared.generateAnalysis(diaryText: prompt) {
                fullResponse += token
                // Update last message in real-time
                await MainActor.run {
                    if let lastIdx = messages.indices.last {
                        // Create new object to force refresh (SwiftUI limitation with array update)
                        let lastMsg = messages[lastIdx]
                        messages[lastIdx] = ChatMessage(text: fullResponse, isUser: false) 
                    }
                }
            }
            
            await MainActor.run {
                isTyping = false
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
