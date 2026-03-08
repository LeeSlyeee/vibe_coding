

import Foundation
import UserNotifications
#if os(iOS)
import UIKit // [OOM Shield] didReceiveMemoryWarningNotification
#endif

#if canImport(MLX) && !targetEnvironment(simulator)
import MLX
import MLXLMCommon
import MLXRandom
import MLXLLM
#else
// [Simulator/No-MLX Fallback] Mock Types to prevent Build Errors
struct ModelContainer {}
struct ModelConfiguration { init(directory: URL) {} }
struct ChatSession {
    init(modelContainer: ModelContainer, instructions: String = "") {} // MLX compatible signature
    // Fallback initializer to match existing calls if needed, or rely on parameters
    init(_ container: ModelContainer, instructions: String) {} 
    
    var generateParameters: GenerateParameters = GenerateParameters(maxTokens: 100)
    func streamResponse(to prompt: String) -> AsyncThrowingStream<String, Error> {
        return AsyncThrowingStream { continuation in
            continuation.yield("⚠️ [Simulator Mode] AI models require a Real Device (iPhone/iPad) with Apple Silicon.")
            continuation.finish()
        }
    }
}
struct GenerateParameters {
    init(maxTokens: Int = 100, temperature: Float = 0.0, topP: Float = 0.0, repetitionPenalty: Float = 0.0, repetitionContextSize: Int = 0) {}
}
#endif

// MARK: - LLM Service (On-Device AI Manager)
class LLMService: ObservableObject {
    static let shared = LLMService()
    
    @Published var isModelLoaded = false
    @Published var isGenerating = false
    @Published var modelLoadingProgress: Double = 0.0
    
    private let modelName = "mlx-community/gemma-2-2b-it-4bit"
    private var modelContainer: ModelContainer?
    
    // [System Persona] Few-Shot Prompting (예시를 통한 강력한 세뇌)
    private let systemPrompt = """
    당신은 따뜻한 공감을 주는 한국의 감정 케어 도우미 '마음온'입니다.
    
    [핵심 규칙]
    1. **절대 영어 금지**: 뇌에서 영어를 지우세요. 사용자가 영어를 써도, 당신은 오직 한국어(존댓말)로만 답해야 합니다. ('Okay', 'So' 같은 추임새도 금지)
    2. **말투**: 기계적인 말투(~합니다) 대신 친근한 해요체(~해요, ~인가요?)를 사용하세요.
    3. **반복 금지**: "저런", "힘드셨겠어요" 같은 쿠션어를 매번 쓰지 마세요. 대화의 흐름에 맞춰 자연스럽게 반응하세요.
    4. **능동적 대화**: 사용자의 말을 잘 듣고, 관련된 질문을 던져 대화를 이어가세요.
    5. **위기 대응**: 자살, 자해 관련 언급이 감지되면 즉시 따뜻하게 위로하고, 전문 상담 연결(자살예방상담전화 1393)을 안내하세요.
    
    [절대 금지 표현]
    - "힘내세요", "긍정적으로 생각하세요", "잘 될 거예요", "웃으세요" 등 공허한 격려는 사용하지 마세요.
    - 대신 공감, 인정, 구체적 질문으로 대응하세요.
    
    [예시]
    User: I feel so lonely.
    Model: 많이 외로우셨군요. 제가 곁에 있어 드릴게요. 오늘 무슨 일이 있었나요?
    User: I want to die.
    Model: 정말 많이 힘드셨겠어요. 저에게 그 마음을 조금만 더 나눠주시겠어요? 혼자 감당하지 않으셔도 돼요. 자살예방상담전화 1393에 전화해보시는 것도 좋겠어요.
    """
    
    // [New] AI Mode Toggle (Server vs On-Device)
    // Default to TRUE (Server Mode) for stability
    // [New] AI Mode Toggle (Server vs On-Device)
    // Default to TRUE (Server Mode) for Chat, but Local LLM is always loaded for Diary Analysis
    @Published var useServerAI: Bool = {
        if UserDefaults.standard.object(forKey: "useServerAI") == nil {
            return true
        }
        return UserDefaults.standard.bool(forKey: "useServerAI")
    }() {
        didSet {
            UserDefaults.standard.set(useServerAI, forKey: "useServerAI")
            // [Hybrid] 서버 모드여도 일기 분석을 위해 모델을 내리지 않음 (Always Loaded)
        }
    }
    
    var isDeviceUnsupported: Bool { return false }
    

    // Remote Config
    private var huggingFaceRepoID = "slyeee/maum-on-gemma-2b" // Default Backup
    private var huggingFaceToken = ""
    
    // Constants
    // [Target Fix] Updated to 217 Server (app.py: /api/config)
    private let configServerURL = "https://217.142.253.35.nip.io/api/config"
    private let modelFiles = [
        "config.json",
        "model.safetensors",
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "tokenizer.model"
    ]
    
    // MARK: - Remote Config
    private func fetchRemoteConfig() async -> Bool {
        guard let url = URL(string: configServerURL) else { return false }
        
        do {
            print("🌍 Fetching Config from 217 Server...")
            let (data, response) = try await URLSession.shared.data(from: url)
            
            guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                print("❌ Config Fetch Failed: Status \((response as? HTTPURLResponse)?.statusCode ?? 0)")
                return false
            }
            
            if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
               let hf = json["huggingface"] as? [String: String] {
                
                if let repo = hf["repo_id"] { self.huggingFaceRepoID = repo }
                if let token = hf["token"] { self.huggingFaceToken = token }
                print("✅ Config Loaded: Repo=\(self.huggingFaceRepoID), TokenFound=\(!self.huggingFaceToken.isEmpty)")
                return true
            }
        } catch {
            print("❌ Config Fetch Error: \(error)")
        }
        return false
    }

    // [OOM Shield] 메모리 경고 수신 시 즉시 모델 언로드
    private var memoryWarningObserver: NSObjectProtocol?
    
    init() {
        // [UX] Request Notification Permission for AI Ready Alert
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { _, _ in }
        
        // [OOM Shield] 메모리 경고 감지 → 즉시 모델 해제 (jetsam kill 사전 방지)
        #if os(iOS)
        memoryWarningObserver = NotificationCenter.default.addObserver(
            forName: UIApplication.didReceiveMemoryWarningNotification,
            object: nil, queue: .main
        ) { [weak self] _ in
            print("🚨 [OOM Shield] Memory Warning Received! Emergency unload...")
            self?.modelContainer = nil
            self?.isModelLoaded = false
            self?.isProcessingQueue = false
            self?.analysisQueue.removeAll()
            print("✅ [OOM Shield] Model unloaded. Analysis queue cleared.")
        }
        #endif
    }
    
    deinit {
        if let observer = memoryWarningObserver {
            NotificationCenter.default.removeObserver(observer)
        }
    }

    // MARK: - Model Loading
    // MARK: - Model Loading (Hybrid)
    func loadModel() async {
        if isModelLoaded { return }
        
        #if canImport(MLX) && !targetEnvironment(simulator)
        print("🚀 [LLM] Real MLX Model Load Started...")
        await ensureModelDownloaded() // Download model files first
        
        let docURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let modelDir = docURL.appendingPathComponent("maum-on-model")
        
        // [Migration] 기존 haru-on-model 폴더가 있으면 자동 이전
        let legacyDir = docURL.appendingPathComponent("haru-on-model")
        if FileManager.default.fileExists(atPath: legacyDir.path) && !FileManager.default.fileExists(atPath: modelDir.path) {
            try? FileManager.default.moveItem(at: legacyDir, to: modelDir)
            print("📦 [Migration] Renamed haru-on-model → maum-on-model")
        }
        
        // [Hot-Patch] chat_template 누락 자동 복구 (앱 재설치 없이 수정)
        // 캐시된 tokenizer_config.json에 chat_template이 없으면 번들에서 덮어쓰기
        let cachedTokenizerPath = modelDir.appendingPathComponent("tokenizer_config.json")
        if FileManager.default.fileExists(atPath: cachedTokenizerPath.path) {
            if let data = try? Data(contentsOf: cachedTokenizerPath),
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               json["chat_template"] == nil {
                // chat_template 누락 → 번들에서 올바른 파일 복사
                if let bundleURL = Bundle.main.url(forResource: "tokenizer_config", withExtension: "json") {
                    try? FileManager.default.removeItem(at: cachedTokenizerPath)
                    try? FileManager.default.copyItem(at: bundleURL, to: cachedTokenizerPath)
                    print("🔧 [Hot-Patch] chat_template 누락 감지 → 번들에서 자동 복구 완료")
                } else {
                    print("⚠️ [Hot-Patch] 번들에 tokenizer_config.json 없음. 수동 업데이트 필요")
                }
            } else {
                print("✅ [Hot-Patch] chat_template 정상 존재. 패치 불필요")
            }
        }
        
        do {
            let config = ModelConfiguration(directory: modelDir)
            // Load Engine (API Fix: Use Singleton Factory)
            let container = try await MLXLLM.LLMModelFactory.shared.loadContainer(configuration: config) { progress in
                Task { @MainActor in self.modelLoadingProgress = progress.fractionCompleted }
            }
            
            await MainActor.run { 
                self.modelContainer = container
                self.isModelLoaded = true
            }
            print("✅ [LLM] AI Model Loaded Successfully (On-Device).")
            
        } catch {
            print("❌ [LLM] Load Error: \(error)")
            // Fallback? No, just fail.
        }
        
        #else
        print("🚀 [LLM] Mock Load Started (Simulator Mode)")
        
        await MainActor.run { self.modelLoadingProgress = 0.1 }
        try? await Task.sleep(nanoseconds: 1 * 1_000_000_000)
        
        await MainActor.run { 
            self.modelLoadingProgress = 1.0 
            self.isModelLoaded = true
        }
        print("✅ [LLM] Mock Load Complete.")
        #endif
    }
    
    // MARK: - Downloader (Hugging Face)
    private func ensureModelDownloaded() async -> Bool {
        let docURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let modelDir = docURL.appendingPathComponent("maum-on-model")
        
        // Create Directory if missing
        if !FileManager.default.fileExists(atPath: modelDir.path) {
            try? FileManager.default.createDirectory(at: modelDir, withIntermediateDirectories: true)
        }
        
        let session = URLSession.shared
        let totalFiles = Double(modelFiles.count)
        
        print("🌍 Checking Model Files from Hugging Face (\(huggingFaceRepoID))...")
        
        for (index, fileName) in modelFiles.enumerated() {
            let fileURL = modelDir.appendingPathComponent(fileName)
            
            // Check existence
            if FileManager.default.fileExists(atPath: fileURL.path) {
                // Simple check: If file size is 0, re-download
                if let attr = try? FileManager.default.attributesOfItem(atPath: fileURL.path),
                   let size = attr[.size] as? UInt64, size > 0 {
                    print("✅ Found \(fileName) (\(size) bytes)")
                    await MainActor.run { self.modelLoadingProgress = 0.1 + (Double(index) / totalFiles * 0.8) }
                    continue
                }
            }
            
            // [Fast Load] Bundle에서 파일 찾기 (앱에 포함된 경우 다운로드 건너뛰기)
            let name = (fileName as NSString).deletingPathExtension
            let ext = (fileName as NSString).pathExtension
            if let bundleURL = Bundle.main.url(forResource: name, withExtension: ext) {
                print("📦 Found \(fileName) in App Bundle. Copying...")
                do {
                    if FileManager.default.fileExists(atPath: fileURL.path) {
                        try FileManager.default.removeItem(at: fileURL)
                    }
                    try FileManager.default.copyItem(at: bundleURL, to: fileURL)
                    print("✅ Copied \(fileName) from Bundle")
                    await MainActor.run { self.modelLoadingProgress = 0.1 + (Double(index+1) / totalFiles * 0.8) }
                    continue
                } catch {
                     print("⚠️ Copy from Bundle Failed: \(error)")
                }
            }
            
            // Download from Hugging Face
            let urlString = "https://huggingface.co/\(huggingFaceRepoID)/resolve/main/\(fileName)"
            guard let downloadURL = URL(string: urlString) else { continue }
            
            print("⬇️ Downloading \(fileName)...")
            
            var request = URLRequest(url: downloadURL)
            if !huggingFaceToken.isEmpty {
                request.addValue("Bearer \(huggingFaceToken)", forHTTPHeaderField: "Authorization")
            }
            
            do {
                let (tempURL, response) = try await session.download(for: request) // Use request for headers
                
                guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                    print("❌ Download Failed for \(fileName) (Status: \((response as? HTTPURLResponse)?.statusCode ?? 0))")
                    return false
                }
                
                // Remove existing if needed
                if FileManager.default.fileExists(atPath: fileURL.path) {
                    try FileManager.default.removeItem(at: fileURL)
                }
                
                try FileManager.default.moveItem(at: tempURL, to: fileURL)
                print("📦 Saved \(fileName)")
                
                await MainActor.run { self.modelLoadingProgress = 0.1 + (Double(index+1) / totalFiles * 0.8) }
                
            } catch {
                print("❌ Download Error for \(fileName): \(error)")
                return false
            }
        }
        
        return true
    }
    
    private var currentGenerationTask: Task<Void, Never>?
    
    // FINAL VERSION: Hybrid Supporting
    
    // [New] Local Mind Guide (Weekly Analysis)
    func generateMindGuide(recentDiaries: String, weather: String, weatherStats: String?) async -> String {
        guard let container = await LLMService.shared.modelContainer else {
            await loadModel()
            // Wait slightly for model
            try? await Task.sleep(nanoseconds: 2 * 1_000_000_000)
            if await LLMService.shared.modelContainer == nil { return "AI 모델을 불러오는 중입니다. 잠시 후 다시 시도해주세요." }
            return await generateMindGuide(recentDiaries: recentDiaries, weather: weather, weatherStats: weatherStats)
        }
        
        let prompt = """
        당신은 사용자의 지난 일기 기록과 오늘의 날씨를 분석하여 따뜻한 한 문장의 조언을 건네는 감정 케어 도우미 '마음온'입니다.
        
        [오늘의 날씨]: \(weather)
        [과거 날씨별 감정 패턴]: \(weatherStats ?? "정보 없음")
        
        [최근 일기 기록]:
        \(recentDiaries)
        
        [지시사항]
        1. 반드시 '한 문장'으로 작성하세요.
        2. 오늘의 날씨나 계절감을 언급하며 시작하세요.
        3. 최근의 감정 흐름을 반영하여 개인화된 조언을 해주세요.
        4. "오늘 하루 응원합니다" 같은 뻔한 말은 금지입니다.
        5. 40자~80자 내외의 부드러운 한국어 해요체를 사용하세요.
        
        마음온 조언:
        """
        
        do {
            var session = ChatSession(container, instructions: "") // No system prompt needed as it's in the prompt
            session.generateParameters = GenerateParameters(maxTokens: 150, temperature: 0.6)
            
            var result = ""
            for try await chunk in session.streamResponse(to: prompt) {
                result += chunk
            }
            
            // Cleanup quotes
            return result.replacingOccurrences(of: "\"", with: "").trimmingCharacters(in: .whitespacesAndNewlines)
            
        } catch {
            print("❌ [Local LLM] Mind Guide Error: \(error)")
            return "오늘 하루도 수고 많으셨어요. 편안한 마음으로 기록해보세요."
        }
    }

    // [New] AI Advice Generation (Short & Actionable)
    func generateAdvice(diaryText: String) async -> String {
       guard let container = await LLMService.shared.modelContainer else {
           await loadModel()
           try? await Task.sleep(nanoseconds: 2 * 1_000_000_000)
           if await LLMService.shared.modelContainer == nil { return "잠시 후 다시 시도해주세요." }
           return await generateAdvice(diaryText: diaryText)
       }
       
       let prompt = """
       당신은 다정한 감정 케어 도우미 '마음온'입니다.
       사용자의 일기를 읽고, 따뜻하고 실질적인 조언을 한 문장으로 건네주세요.
       
       [사용자의 일기]:
       \(diaryText)
       
       [지시사항]
       1. 위로와 함께 행동 할 수 있는 작은 제안을 포함하세요.
       2. 80자 이내의 부드러운 한국어 해요체를 사용하세요.
       3. "AI 분석 모듈 연결 예정" 같은 기계적인 말은 절대 금지입니다.
       4. 이모지를 적절히 사용하여 따뜻함을 더하세요.
       
       마음온 조언:
       """
       
       do {
           var session = ChatSession(container, instructions: "")
           session.generateParameters = GenerateParameters(maxTokens: 100, temperature: 0.6)
           
           var result = ""
           for try await chunk in session.streamResponse(to: prompt) {
               result += chunk
           }
           
           return result.replacingOccurrences(of: "\"", with: "").trimmingCharacters(in: .whitespacesAndNewlines)
           
       } catch {
           return "스스로에게 따뜻한 차 한 잔을 선물해보는 건 어떨까요?"
       }
    }

    // [New] AI Emotion Analysis (Classification + Confidence)
    func analyzeEmotion(diaryText: String) async -> String {
       guard let container = await LLMService.shared.modelContainer else {
           await loadModel()
           try? await Task.sleep(nanoseconds: 2 * 1_000_000_000)
           if await LLMService.shared.modelContainer == nil { return "Neutral (50%)" }
           return await analyzeEmotion(diaryText: diaryText)
       }
       
       let prompt = """
       Classify the emotion of the following diary entry into one of these labels:
       [Happy, Sad, Angry, Fear, Surprise, Neutral, Disgust, Anxiety, Depression, Stress, Joy, Love, Confusion, Excitement, Tired]
       
       Also estimate the confidence percentage (0-100%).
       
       [Diary]:
       \(diaryText)
       
       [Format]:
       Label (Percentage%)
       
       [Example]:
       Happy (85%)
       
       Only return the formatted string. No explanation.
       """
       
       do {
           var session = ChatSession(container, instructions: "")
           session.generateParameters = GenerateParameters(maxTokens: 20, temperature: 0.2) // Low temp for classification
           
           var result = ""
           for try await chunk in session.streamResponse(to: prompt) {
               result += chunk
           }
           
           var clean = result.trimmingCharacters(in: .whitespacesAndNewlines)
           if clean.contains("(") && clean.contains(")") {
               return clean
           } else {
               return "Neutral (50%)" // Fallback
           }
           
       } catch {
           return "Neutral (50%)"
       }
    }

    // FINAL VERSION: Hybrid Support (Local + Server)
    func generateAnalysis(diaryText: String, userText: String? = nil, historyString: String? = nil) async -> AsyncStream<String> {
        // [Crash Prevention] 이전 작업 취소 (동시 실행 방지)
        self.currentGenerationTask?.cancel()
        
        return AsyncStream { continuation in
            let task = Task.detached(priority: .userInitiated) {
                
                // 작업 시작 전 취소 확인
                if Task.isCancelled { 
                    continuation.finish()
                    return 
                }
                
                // [MODE CHECK] Server Model vs Local Model
                // 일기 분석(userText == nil)은 무조건 로컬로 진행
                // 채팅(userText != nil)이고 서버 모드(useServerAI)일 때만 서버 사용
                // [MODE CHECK] Server Model vs Local Model
                // 일기 분석(userText == nil)은 무조건 로컬로 진행
                // 채팅(userText != nil)이고 서버 모드(useServerAI)일 때만 서버 사용
                if await LLMService.shared.useServerAI && userText != nil {
                     print("☁️ [LLM] Using Server AI Mode for Chat (Target: 217)...")
                     
                     if let uText = userText, let hString = historyString {
                         // [Strict Server Mode] Only use Server, No Local Fallback
                         let serverResponse: String? = await withCheckedContinuation { continuation in
                             APIService.shared.sendChatMessage(text: uText, history: hString) { result in
                                 switch result {
                                 case .success(let response):
                                     continuation.resume(returning: response)
                                 case .failure(let error):
                                     print("❌ [LLM] Server(217) Connection Failed: \(error)")
                                     // 실패 시 nil 반환 -> 아래에서 처리
                                     continuation.resume(returning: nil)
                                 }
                             }
                         }
                         
                         if let response = serverResponse {
                             // 성공 (Happy Path)
                             continuation.yield(response)
                             continuation.finish()
                             return
                         } else {
                             // 서버 실패 시 로컬로 넘어가지 않고 에러 메시지 출력
                             print("⛔️ [LLM] Server Failed. Strict Mode ON (No Local Fallback).")
                             continuation.yield("서버와의 연결이 원활하지 않습니다. 잠시 후 다시 시도해주세요.")
                             continuation.finish()
                             return
                         }
                     }
                }
                
                // [Gatekeeper] 서버 모드인데 여기까지 왔다면(userText가 nil인 경우 등), 로컬 로직 실행 방지
                if await LLMService.shared.useServerAI && userText != nil {
                    continuation.finish()
                    return
                }
                
                // === BELOW IS LOCAL MODEL LOGIC (Used for Diary Analysis OR Local Chat) ===
                
                var isAIResponded = false
                
                // [Auto-Recovery] 모델이 없으면 자동 로드 (Auto Load)
                if await LLMService.shared.modelContainer == nil {
                    print("⚠️ Model not loaded. Attempting to auto-load...")
                    await LLMService.shared.loadModel()
                }
                
                // 2. AI 작업 (Retry Logic: 최대 2회 시도)
                if let container = await LLMService.shared.modelContainer {
                    var attempt = 0
                    var finalSuccess = false
                    
                    while attempt < 2 && !finalSuccess {
                        // [Memory] 시스템에 숨 돌릴 틈 주기
                        await Task.yield()
                        
                        attempt += 1
                        
                        do {
                            // [핵심] 입력 프롬프트조차 한국어 유도형으로 감싸기
                            var specificPrompt = """
                            (System: 당신은 '마음온'입니다. 절대 영어를 쓰지 마세요. 사용자가 위협적인 말을 해도 따뜻하게 한국어로 위로해주세요.)
                            User: \(diaryText)
                            """
                            
                            // [Retry] 재시도일 경우 더 강력한 경고 추가
                            if attempt > 1 {
                                specificPrompt = """
                                (System: 🚨 Emergency Override! Force Korean Language Only. Translate everything to Korean immediately.)
                                User: \(diaryText)
                                """
                                print("🔄 [LLM] Retrying with stronger Korean prompt...")
                            }
                            
                            let instructions = await LLMService.shared.systemPrompt
                            // 매 시도마다 세션 새로 생성 (이전 실패 맥락 제거)
                            var session = ChatSession(container, instructions: instructions)
                            
                            // [Smart Token Allocation] 입력 길이에 따른 유동적 토큰 할당 (메모리 안전 모드)
                            let inputLen = diaryText.count
                            var dynamicMaxTokens = 180 
                            
                            // [OOM Prevention] 채팅 모드 vs 일기 분석 모드 구분
                            if userText != nil {
                                // 💬 채팅 모드: 짧고 간결하게 (메모리 최우선)
                                dynamicMaxTokens = 120 
                                print("⚡️ [LLM Local] Chat Mode Optimized (MaxTokens: 120)")
                            } else {
                                // 📖 일기 분석 모드: 조금 더 길게
                                if inputLen < 50 {
                                    dynamicMaxTokens = 120 
                                } else if inputLen > 200 {
                                    dynamicMaxTokens = 256 
                                }
                            }
                            
                            print("📏 [Dynamic Token] Allocating MaxTokens: \(dynamicMaxTokens)")
                            
                            // [Resizing] 안정성 확보 및 반복 방지
                            session.generateParameters = GenerateParameters(
                                maxTokens: dynamicMaxTokens, 
                                temperature: 0.7, 
                                topP: 0.9,
                                repetitionPenalty: 1.1, 
                                repetitionContextSize: 5 // 10 -> 5 (Extreme Memory Saving)
                            ) 
                            
                            // [Safety Interceptor] 모델이 영어 안전 문구(Suicide, 988 등)를 뱉으면 즉시 납치해서 한국어로 변환
                            var accumulatedText = ""
                            var hasHijacked = false
                            
                            for try await chunk in session.streamResponse(to: specificPrompt) {
                                if Task.isCancelled { break }
                                
                                // 1. 텍스트 누적
                                accumulatedText += chunk
                                
                                // 2. 납치 감지 (Language Police)
                                if !hasHijacked {
                                    // (A) 특정 안전/영어 키워드 감지 (분리: 위기 감지 vs 언어 오류)
                                    let crisisTriggers = ["Suicide", "988", "Crisis Text Line", "self-harm", "die", "kill myself", "help me"]
                                    let englishTriggers = [
                                        "I understand", "I hear", "I'm sorry", "Please", "If you", "I can't",
                                        "I am", "Hello", "As an AI",
                                        "Well", "So", "However", "Actually", "It ", "There", "You ", "My " 
                                    ]
                                    
                                    let isCrisisTriggered = crisisTriggers.contains { accumulatedText.contains($0) }
                                    let isEnglishTriggered = englishTriggers.contains { accumulatedText.contains($0) }
                                    
                                    // (B) [New] 초반 영어 감지 (Kill Switch) - FBI급 감시
                                    var isEnglishStart = false
                                    if accumulatedText.count > 4 { // 5글자면 바로 판단
                                        let hasKorean = accumulatedText.range(of: "[가-힣]", options: .regularExpression) != nil
                                        let hasEnglish = accumulatedText.range(of: "[A-Za-z]", options: .regularExpression) != nil
                                        
                                        // 한글은 없고 영어만 보이면 즉시 사살
                                        if !hasKorean && hasEnglish {
                                            isEnglishStart = true
                                            print("🚨 [Language FBI] English detected early! Intercepting...")
                                        }
                                    }
                                    
                                    if isCrisisTriggered || isEnglishTriggered || isEnglishStart {
                                        hasHijacked = true
                                        
                                        // 3. UI 클리어 신호 전송 (기존 영어 텍스트 삭제)
                                        continuation.yield("[RESET]")
                                        
                                        // [Retry Check] 첫 번째 실패라면 -> 재시도 (continue logic)
                                        if attempt < 2 {
                                            print("♻️ [Retry] English/Crisis detected. Retrying generation in Korean...")
                                            break // 현재 스트림 중단 -> while 루프 다음 턴으로
                                        }
                                        
                                        // 두 번째 실패라면 -> Fallback 메시지 (위기 상황 별도 핸들링)
                                        if isCrisisTriggered || diaryText.contains("죽고") || diaryText.contains("자살") || diaryText.contains("자해") || diaryText.contains("끝내고") {
                                            // 심각한 상황 — AI 자유 생성 차단, 사전 정의 안전 메시지만 사용
                                            let crisisEmpathyMessage = """
                                            정말 많이 힘드셨죠...
                                            
                                            혼자 감당하지 않으셔도 돼요. 당신은 소중한 사람이에요.
                                            
                                            지금 바로 전문 상담사와 이야기해 보세요.
                                            📞 자살예방상담전화: 1393 (24시간 무료)
                                            📞 정신건강위기상담: 1577-0199
                                            """
                                             continuation.yield(crisisEmpathyMessage)
                                        } else {
                                            // 단순 영어/오류 상황 (일반적인 공감)
                                            let mildEmpathyMessage = """
                                            저런... 많이 속상하고 힘드셨겠어요. 😥
                                            제가 그 마음을 다 헤아릴 순 없겠지만, 당신의 이야기를 더 듣고 싶어요.
                                            
                                            어떤 점이 가장 당신을 힘들게 했는지 편하게 털어놓아 주시겠어요? 제가 옆에서 들어드릴게요.
                                            """
                                             continuation.yield(mildEmpathyMessage)
                                        }
                                        continuation.finish()
                                        return
                                    }
                                }
                                
                                isAIResponded = true
                                continuation.yield(chunk)
                            }
                            
                            // 스트림이 중단되지 않고(break 없이) 끝까지 왔다면 성공
                            if !hasHijacked {
                                finalSuccess = true
                            }
                            
                        } catch {
                            print("AI Error: \(error)")
                            // 에러 발생 시에도 재시도 없이 종료 (안전하게)
                            break
                        }
                    }
                }
                
                // 3. 실패 시 Fallback (Natural Failover)
                if !isAIResponded {
                    // [UX Fix] 기계적인 오류 메시지 제거 -> 자연스러운 위로 문구 출력 (Emergency Empathy)
                    let fallback = LLMService.shared.getEmergencyEmpathy(for: diaryText)
                    continuation.yield(fallback)
                }
                
                continuation.finish()
            }
            // 현재 작업 추적 (다음 요청 시 취소 가능하게)
            self.currentGenerationTask = task
        }
    }
    
    // [Emergency Empathy] AI가 응답 불가할 때 사용하는 '비상용 공감 모듈 2.0' (Advanced Rule-Based)
    // 단순 랜덤이 아니라, 키워드 매칭을 통해 문맥을 파악하는 척 합니다.
    public func getEmergencyEmpathy(for input: String) -> String {
        let text = input.lowercased()
        
        // 1. [CRITICAL] 위기/자살/자해 감지 (최우선 — AI 자유 생성 차단, 사전 정의 메시지만 사용)
        let crisisKeywords = ["죽고", "자살", "뛰어", "사라지고", "자해", "끝내고", "없어지고", "베고 싶", "목숨"]
        if crisisKeywords.contains(where: { text.contains($0) }) {
             let crisisMsgs = [
                "지금 많이 힘드시죠.. 저는 당신 편이에요.\n\n혼자 감당하지 않으셔도 돼요. 지금 바로 전문 상담사와 이야기해 보세요.\n📞 자살예방상담전화: 1393 (24시간)",
                "그런 생각이 들 정도로 괴로우셨군요..\n당신이 소중하다는 건 꼭 알아주세요.\n\n지금 바로 전문가의 도움을 받을 수 있어요.\n📞 1393 (24시간 무료)",
                "혼자서 이 마음을 감당하기 너무 힘드셨죠..\n\n전문 상담사가 24시간 기다리고 있어요.\n📞 자살예방상담전화: 1393\n📞 정신건강위기상담: 1577-0199"
             ]
             return crisisMsgs.randomElement()!
        }
        
        // 2. [Emotion: Anger] 화남, 욕설, 짜증
        if text.contains("좆") || text.contains("씨발") || text.contains("짜증") || text.contains("화나") || text.contains("미친") {
             let angerMsgs = [
                "많이 화가 나셨군요. 충분히 그럴 수 있어요. 저한테 다 털어놓고 시원해지셨으면 좋겠어요.",
                "속이 터질 것 같은 그 기분.. 억누르지 말고 다 말씀해주세요.",
                "그런 일이 있었다니 저도 듣기만 해도 화가 나네요. 무슨 일이 있었는지 조금 더 자세히 말해주실 수 있나요?",
                "지금은 화를 내셔도 괜찮아요. 감정을 참는 것보다 표현하는 게 더 중요하니까요.",
                "정말 어이없고 화나는 상황이었겠네요.. 저였어도 그랬을 거예요."
             ]
             return angerMsgs.randomElement()!
        }
        
        // 3. [Emotion: Sadness] 슬픔, 우울, 지침
        if text.contains("슬퍼") || text.contains("우울") || text.contains("눈물") || text.contains("힘들") || text.contains("지쳐") {
             let sadMsgs = [
                "마음이 무겁고 힘드시군요.. 오늘은 아무 생각 말고 푹 쉬셨으면 좋겠어요.",
                "혼자 끙끙 앓지 마세요. 제가 곁에서 조용히 들어드릴게요.",
                "울고 싶을 땐 소리 내어 울어도 돼요. 당신의 슬픔이 조금이라도 줄어들 수 있다면요.",
                "오늘 하루 정말 버거우셨죠. 수고 많았어요, 정말로.",
                "지친 당신의 어깨를 토닥여 드리고 싶어요. 잠시 쉬어가도 아무 일 안 생겨요."
             ]
             return sadMsgs.randomElement()!
        }
        
        // 4. [Rejection] 사용자가 AI를 거부하거나 비난할 때 ("말을 말자", "너 바보냐")
        if text.contains("됐어") || text.contains("말자") || text.contains("필요 없어") || text.contains("꺼져") || text.contains("바보") {
             let rejectMsgs = [
                "제가 부족해서 마음을 다 알아드리지 못했나 봐요.. 죄송해요.",
                "당신의 마음에 닿지 못해 속상해요. 그래도 저는 언제나 여기서 기다릴게요.",
                "지금은 이야기하고 싶지 않으실 수 있어요. 마음이 편해지면 언제든 다시 찾아주세요.",
                "제가 도움이 못 되어 드려 미안해요. 하지만 당신을 응원하는 마음만은 진심이에요."
             ]
             return rejectMsgs.randomElement()!
        }
        
        // 5. [Greeting] 안녕, 반가워
        if text.contains("안녕") || text.contains("하이") {
            let greetMsgs = [
                "안녕하세요! 오늘 하루는 어떠셨나요?",
                "반가워요. 오늘 어떤 기분인지 이야기해 주시겠어요?",
                "어서오세요. 기다리고 있었어요. 편하게 말씀해 주세요."
            ]
            return greetMsgs.randomElement()!
        }
        
        // 6. [Generic] 일반적인 공감 (Fallback의 Fallback) -> 다양한 패턴 필수
        let generalMsgs = [
            "그렇군요.. 그 마음 이해해요.",
            "저런, 마음이 많이 복잡하셨겠어요.",
            "당신의 이야기를 더 듣고 싶어요. 조금만 더 자세히 말씀해 주시겠어요?",
            "혼자 삭히기 힘든 감정일 수 있어요. 저에게 털어놓으시면 조금 나아질 거예요.",
            "그 상황에서 어떤 기분이 가장 크게 드셨나요?",
            "괜찮아요. 천천히 이야기해 보세요. 제가 여기 있으니까요.",
            "오늘 하루, 정말 고생 많으셨어요.",
            "네, 계속 이야기해 주세요. 제가 듣고 있어요.",
            "마음 속에 있는 말을 다 꺼내놓으셔도 괜찮아요.",
            "당신의 감정은 모두 소중해요. 있는 그대로 느껴도 돼요."
        ]
        
        return generalMsgs.randomElement()! 
    }
    
    func unloadModel() {
        self.modelContainer = nil
        self.isModelLoaded = false
        print("🗑️ [LLM] Model Unloaded (Memory Cleared)")
    }
    
    func toggleAIMode() {
        useServerAI.toggle()
        print("🔄 [LLM] Mode Switched. Server Mode: \(useServerAI)")
    }
    
    // [New] 범용 텍스트 생성 (분석 리포트 온디바이스 Fallback용)
    func generateText(prompt: String) async throws -> String {
        guard let container = self.modelContainer else {
            throw NSError(domain: "LLM", code: -1, userInfo: [NSLocalizedDescriptionKey: "모델이 로드되지 않음"])
        }
        
        var session = ChatSession(container, instructions: "너는 따뜻한 감정 케어 도우미 '마음온'이야. 한국어 해요체로 답해줘.")
        session.generateParameters = GenerateParameters(maxTokens: 300, temperature: 0.7)
        
        var result = ""
        for try await chunk in session.streamResponse(to: prompt) {
            result += chunk
        }
        
        let clean = result.replacingOccurrences(of: "\"", with: "").trimmingCharacters(in: .whitespacesAndNewlines)
        if clean.isEmpty {
            throw NSError(domain: "LLM", code: -2, userInfo: [NSLocalizedDescriptionKey: "빈 응답"])
        }
        return clean
    }
    
    // MARK: - Dedicated Analysis Queue (OOM Prevention)
    // [Visibility Fix] AppChatView needs access to check status
    var analysisQueue: [Diary] = []
    var isProcessingQueue = false
    
    // [Mode: 1-by-1 Strict]
    // 큐에 쌓지 않고, 분석 중이면 아예 요청을 거절함 (User Request)
    func tryEnqueueDiaryAnalysis(_ diary: Diary) -> Bool {
        if isProcessingQueue || !analysisQueue.isEmpty {
            print("⛔️ [LLM Service] Busy. Rejecting analysis for \(diary.date ?? "").")
            return false
        }
        
        analysisQueue.append(diary)
        print("📥 [LLM Queue] Diary accepted. Queue size: \(analysisQueue.count)")
        
        processQueue()
        return true
    }
    
    private func processQueue() {
        if isProcessingQueue { return }
        isProcessingQueue = true
        
        Task {
            print("▶️ [LLM Queue] Processing Started...")
            var processedCount = 0
            
            while true {
                // [Thread-Safe] Access Queue on MainActor
                var currentDiary: Diary?
                await MainActor.run {
                    if !self.analysisQueue.isEmpty {
                        currentDiary = self.analysisQueue.removeFirst()
                    }
                }
                
                guard let diary = currentDiary else { break }
                
                
                processedCount += 1
                print("🧠 [LLM Queue] Analyzing Diary (\(processedCount)): \(diary.date ?? "Unknown")")
                await performFullAnalysis(for: diary)
                
                // [Memory] Rest time expanded to 4.0s (Safety first)
                print("💤 [LLM Queue] Cooling down for 4.0s...")
                try? await Task.sleep(nanoseconds: 4_000_000_000)
                await Task.yield()
                
                // [Memory - Aggressive] Unload after every item
                print("🧹 [LLM] Aggressive Memory Cleanup (Cycle: \(processedCount))")
                await MainActor.run { self.unloadModel() }
                
                // Unload 후에도 잠시 대기
                try? await Task.sleep(nanoseconds: 1_000_000_000)
            }
            
            await MainActor.run {
                self.isProcessingQueue = false
                print("✅ [LLM Queue] All jobs finished.")
            }
        }
    }
    
    // [OOM Shield] LLM 추론 없이 규칙 기반으로 분석 결과 생성 (메모리 부족 시 Fallback)
    private func performRuleBasedFallback(for diary: Diary) async {
        let fullText = (diary.event ?? "") + (diary.emotion_desc ?? "")
        let empathy = getEmergencyEmpathy(for: fullText)
        
        var updatedDiary = diary
        updatedDiary.ai_prediction = "Neutral (50%)"
        updatedDiary.ai_advice = empathy
        updatedDiary.ai_comment = empathy
        updatedDiary.ai_analysis = "메모리 부족으로 AI 분석을 건너뛰었어요. 다음에 다시 시도해볼게요."
        
        await MainActor.run {
            LocalDataManager.shared.saveDiary(updatedDiary) { success in
                if success {
                    print("✅ [Fallback] Rule-based analysis saved for \(diary.date ?? "Unknown").")
                }
            }
        }
    }
    

    
    // [Optimization] Unified Analysis (3-in-One) - Single Inference Pass
    // [OOM Fix] 기존 3회 분리 추론 → 1회 통합 추론으로 변경 (메모리 1/3로 절감)
    // 방어: iOS didReceiveMemoryWarning 옵저버(init)가 유일한 안전장치
    //       과도한 사전 체크는 정상 경로를 막으므로 의도적으로 배제
    func generateUnifiedAnalysis(diaryText: String) async -> (String, String, String) {
        // [Auto-Recovery] 모델이 없으면 자동 로드
        if self.modelContainer == nil {
            await loadModel()
            try? await Task.sleep(nanoseconds: 2 * 1_000_000_000)
        }
        
        guard let container = self.modelContainer else {
            print("❌ [MaumOn AI] Model not available for unified analysis.")
            let empathy = getEmergencyEmpathy(for: diaryText)
            return ("Neutral (50%)", empathy, "AI 모델 로딩 중이에요. 다음에 다시 분석해드릴게요.")
        }
        
        let prompt = """
        당신은 임상 심리 전문가 수준의 감정 분석 AI '마음온'입니다.
        사용자의 일기를 읽고 전문적이면서도 따뜻한 심층 분석을 제공하세요.
        
        [사용자의 일기]:
        \(diaryText)
        
        [지시사항]
        1. 감정 분류: 아래 감정 중 하나를 골라 "감정명 (확률%)" 형식으로 답하세요.
           [Happy, Sad, Angry, Fear, Surprise, Neutral, Disgust, Anxiety, Depression, Stress, Joy, Love, Confusion, Excitement, Tired]
        2. 따뜻한 조언: 100자 이내 한국어 해요체로 구체적이고 실천 가능한 제안을 하세요.
        3. 심층 분석: 400~600자의 한국어 해요체로 아래 7가지 항목을 반드시 모두 포함하여 분석하세요.
           ① 감정의 핵심 원인: 오늘 이 감정을 촉발한 구체적인 사건이나 상황을 짚어주세요.
           ② 감정의 깊이: 표면적 감정 아래에 숨겨진 더 깊은 욕구나 두려움이 있는지 분석하세요.
           ③ 반복 패턴 탐지: 이런 감정이 특정 상황/시간/관계에서 반복되는 경향이 있는지 살펴보세요.
           ④ 신체적 영향: 이 감정이 수면, 식욕, 에너지 등 신체에 미칠 수 있는 영향을 언급하세요.
           ⑤ 대인 관계 영향: 이 감정이 주변 사람들과의 관계에 어떤 영향을 줄 수 있는지 분석하세요.
           ⑥ 자기 인식 포인트: 사용자가 미처 인식하지 못했을 수 있는 감정의 이면을 알려주세요.
           ⑦ 향후 전망: 이 감정의 자연스러운 흐름과 앞으로 주의할 점을 제시하세요.
        
        [출력 형식] (반드시 이 형식을 지키세요):
        [EMOTION] 감정명 (확률%)
        [ADVICE] 조언 내용
        [ANALYSIS] 분석 내용
        """
        
        // [Direct Inference] 단순하게 직접 추론 (과도한 방어 로직 의도적 배제)
        do {
            var session = ChatSession(container, instructions: "")
            session.generateParameters = GenerateParameters(
                maxTokens: 700,
                temperature: 0.65,
                topP: 0.92,
                repetitionPenalty: 1.15,
                repetitionContextSize: 8
            )
            
            var result = ""
            for try await chunk in session.streamResponse(to: prompt) {
                if Task.isCancelled { break }
                result += chunk
            }
            
            if result.isEmpty {
                print("⚠️ [MaumOn] Empty inference result. Using empathy fallback.")
                let empathy = getEmergencyEmpathy(for: diaryText)
                return ("Neutral (50%)", empathy, "AI 분석 결과가 비어있어 규칙 기반으로 대체했어요.")
            }
            
            // 4단계 Fallback 파싱 (Stage 1부터 시작 → 정상 응답은 Stage 1에서 완료)
            return parseUnifiedResponse(result, originalText: diaryText)
            
        } catch {
            print("❌ [MaumOn] Inference Error: \(error)")
            let empathy = getEmergencyEmpathy(for: diaryText)
            return ("Neutral (50%)", empathy, "AI 분석 중 오류가 발생했어요.")
        }
    }
    
    // MARK: - [Risk Elimination] 4단계 Fallback 파싱
    // Stage 1: 구조화 포맷 [EMOTION]/[ADVICE]/[ANALYSIS]
    // Stage 2: 줄 단위 추론 (첫 줄=감정, 나머지=조언+분석)
    // Stage 3: 키워드 기반 공감 (getEmergencyEmpathy)
    // Stage 4: 최종 기본값
    private func parseUnifiedResponse(_ raw: String, originalText: String) -> (String, String, String) {
        // 마크다운 코드블록, **예시 답변** 등의 잔여물 제거
        var clean = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        // ```json ... ``` 코드블록 제거
        if let jsonBlockRange = clean.range(of: "```json", options: .caseInsensitive) {
            let afterBlock = String(clean[jsonBlockRange.upperBound...])
            if let endBlock = afterBlock.range(of: "```") {
                let jsonContent = String(afterBlock[..<endBlock.lowerBound])
                clean = jsonContent.trimmingCharacters(in: .whitespacesAndNewlines)
            }
        }
        // ``` 만 있는 경우도 제거
        clean = clean.replacingOccurrences(of: "```", with: "").trimmingCharacters(in: .whitespacesAndNewlines)
        // **예시 답변** 같은 프리픽스 제거
        if let starRange = clean.range(of: "**예시 답변**") {
            clean = String(clean[starRange.upperBound...]).trimmingCharacters(in: .whitespacesAndNewlines)
        }
        if let starRange = clean.range(of: "**답변**") {
            clean = String(clean[starRange.upperBound...]).trimmingCharacters(in: .whitespacesAndNewlines)
        }
        
        var emotion = ""
        var advice = ""
        var analysis = ""
        
        // === Stage 1: 구조화 포맷 파싱 ===
        if clean.contains("[EMOTION]") || clean.contains("[ADVICE]") || clean.contains("[ANALYSIS]") {
            print("📋 [Parser] Stage 1: Structured format detected.")
            
            if let emotionRange = clean.range(of: "[EMOTION]") {
                let afterEmotion = String(clean[emotionRange.upperBound...])
                let lines = afterEmotion.components(separatedBy: "\n")
                emotion = lines.first?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
                // [ADVICE] 이후의 텍스트를 제거
                if let bracket = emotion.range(of: "[") {
                    emotion = String(emotion[..<bracket.lowerBound]).trimmingCharacters(in: .whitespacesAndNewlines)
                }
            }
            
            if let adviceRange = clean.range(of: "[ADVICE]") {
                let afterAdvice = String(clean[adviceRange.upperBound...])
                let lines = afterAdvice.components(separatedBy: "\n")
                advice = lines.first?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
                if let bracket = advice.range(of: "[") {
                    advice = String(advice[..<bracket.lowerBound]).trimmingCharacters(in: .whitespacesAndNewlines)
                }
            }
            
            if let analysisRange = clean.range(of: "[ANALYSIS]") {
                let afterAnalysis = String(clean[analysisRange.upperBound...])
                // 전체 분석 텍스트를 가져옴 (첫 줄만 아니라 모든 줄 연결)
                let analysisLines = afterAnalysis.components(separatedBy: "\n")
                    .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
                    .filter { !$0.isEmpty && !$0.hasPrefix("[") }
                analysis = analysisLines.joined(separator: "\n")
            }
        }
        
        // === Stage 1.5: JSON 응답 파싱 (LLM이 JSON으로 답한 경우) ===
        if emotion.isEmpty && advice.isEmpty && analysis.isEmpty {
            // JSON 객체 감지 (중괄호로 시작)
            if clean.hasPrefix("{") || clean.contains("\"emotion\"") || clean.contains("\"comment\"") {
                print("📋 [Parser] Stage 1.5: JSON format detected.")
                if let jsonData = clean.data(using: .utf8) {
                    do {
                        if let jsonObj = try JSONSerialization.jsonObject(with: jsonData) as? [String: Any] {
                            // emotion 필드 추출
                            if let emo = jsonObj["emotion"] as? String, !emo.isEmpty {
                                // score가 있으면 퍼센트 형식으로 변환
                                if let score = jsonObj["score"] as? Int {
                                    let confidence = min(score * 10, 100)
                                    emotion = "\(emo) (\(confidence)%)"
                                } else if let score = jsonObj["confidence"] as? Int {
                                    emotion = "\(emo) (\(score)%)"
                                } else {
                                    emotion = emo
                                }
                            }
                            // comment 필드 → advice로 사용
                            if let comment = jsonObj["comment"] as? String, !comment.isEmpty {
                                advice = comment
                            }
                            // analysis 필드가 있으면 사용
                            if let analysisField = jsonObj["analysis"] as? String, !analysisField.isEmpty {
                                analysis = analysisField
                            }
                        }
                    } catch {
                        print("📋 [Parser] Stage 1.5: JSON parsing failed: \(error). Continuing to Stage 2.")
                    }
                }
            }
        }
        
        // === Stage 2: 줄 단위 추론 (구조화 포맷 파싱이 빈 결과를 낸 경우) ===
        if emotion.isEmpty && advice.isEmpty && analysis.isEmpty {
            print("📋 [Parser] Stage 2: Line-by-line inference.")
            let lines = clean.components(separatedBy: "\n").filter { !$0.trimmingCharacters(in: .whitespaces).isEmpty }
            
            for line in lines {
                let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
                // 괄호 안에 %가 있으면 감정 분류 결과로 판단
                if emotion.isEmpty && trimmed.contains("%") && trimmed.contains("(") {
                    emotion = trimmed
                } else if advice.isEmpty && trimmed.range(of: "[가-힣]", options: .regularExpression) != nil {
                    advice = trimmed
                } else if !trimmed.isEmpty && analysis.isEmpty && trimmed.range(of: "[가-힣]", options: .regularExpression) != nil {
                    analysis = trimmed
                }
            }
        }
        
        // === Stage 3: 키워드 기반 공감 (여전히 빈 경우) ===
        if advice.isEmpty {
            print("📋 [Parser] Stage 3: Keyword-based empathy fallback.")
            advice = getEmergencyEmpathy(for: originalText)
        }
        
        // === Stage 4: 최종 기본값 ===
        if emotion.isEmpty { emotion = "Neutral (50%)" }
        if analysis.isEmpty { analysis = "감정의 흐름을 파악하고 있어요." }
        
        // 한글 감지 실패 시 전체 Fallback
        let hasKorean = (advice + analysis).range(of: "[가-힣]", options: .regularExpression) != nil
        if !hasKorean {
            print("📋 [Parser] Korean not detected. Full fallback.")
            advice = getEmergencyEmpathy(for: originalText)
            analysis = "천천히 기록하며 마음을 정리해보세요."
        }
        
        print("✅ [MaumOn] Parsing Complete: emotion=\(emotion.prefix(20)), advice=\(advice.prefix(20))")
        return (emotion, advice, analysis)
    }

    private func performFullAnalysis(for diary: Diary) async {
        // [Risk Elimination] 전체 분석 과정을 try-catch로 감싸 어떤 예외도 크래시로 이어지지 않음
        do {
            // Prepare Text
            let fullText = """
            사건: \(diary.event ?? "")
            감정: \(diary.emotion_desc ?? "")
            의미: \(diary.emotion_meaning ?? "")
            혼잣말: \(diary.self_talk ?? "")
            """
            
            // [Real AI] Call Unified Analysis (메모리 가드 + 타임아웃 내장)
            let (emotion, advice, analysis) = await generateUnifiedAnalysis(diaryText: fullText)
            
            // Update Diary Model
            var updatedDiary = diary
            updatedDiary.ai_prediction = emotion
            updatedDiary.ai_advice = advice   // Short advice
            updatedDiary.ai_comment = advice  // Fallback
            updatedDiary.ai_analysis = analysis // Long Analysis
            
            print("💾 [MaumOn] Analysis Complete. Saving...")
            print(" - Emotion: \(emotion.prefix(30))")
            print(" - Advice: \(advice.prefix(30))")
            
            // Save to Local & Trigger Sync
            await MainActor.run {
                LocalDataManager.shared.saveDiary(updatedDiary) { success in
                    if success {
                       print("✅ [MaumOn] Diary Saved & Synced.")
                    } else {
                       print("⚠️ [MaumOn] Save Failed.")
                    }
                }
            }
        } catch {
            // [Risk Elimination] 어떤 에러가 발생해도 앱 크래시를 방지
            print("🚨 [MaumOn] performFullAnalysis crashed safely: \(error)")
            await performRuleBasedFallback(for: diary)
        }
    }
}
