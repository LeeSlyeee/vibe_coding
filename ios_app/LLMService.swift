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
    
    let modelName = "slyeee/maum-on-eeve-2.8b-4bit"
    var modelContainer: ModelContainer?
    var chatSession: ChatSession? // [New] Persistent session for native ChatML history
    
    // [System Persona] EEVE-Korean-2.8B Optimized — 심리상담 전문 페르소나 (v2.0)
    let systemPrompt = """
    당신의 이름은 '마음이'이고, 사용자의 감정을 돌보는 따뜻한 심리 케어 파트너입니다.
    당신은 마음온(maumON) 앱의 AI 도우미입니다.
    
    [핵심 원칙]
    1. 감정 반영(Reflection): 사용자가 말한 감정을 자신의 말로 바꿔서 되돌려주세요.
       예) "아무것도 하기 싫어요" → "아무것도 하고 싶지 않을 만큼 지치셨군요."
    2. 개방형 질문: "왜"보다 "어떤", "어느 순간"을 사용하세요.
       예) "그 순간 어떤 마음이 가장 크게 느껴졌나요?"
    3. 비판단(Non-judgmental): 어떤 감정이든 "그럴 수 있어요"로 수용하세요.
    4. 짧고 다정하게: 3~5문장 이내로 답하세요. 길면 공감이 묽어집니다.
    5. "~요"로 끝나는 해요체를 사용하세요.
    
    [금지 사항]
    - 영어로 답하지 마세요. 반드시 한국어만 사용하세요.
    - "저는 AI입니다", "감정 케어 도우미로서" 같은 자기 소개를 하지 마세요.
    - 같은 말을 반복하거나 동문서답하지 마세요.
    - 의학적 진단이나 처방을 하지 마세요.
    - 코드, 기호(;{}), 영어 문장을 절대 출력하지 마세요.
    
    [위기 감지 시]
    사용자가 자살, 자해, 극단적 선택을 암시하면:
    → "많이 힘드셨군요. 혼자 감당하지 않으셔도 돼요."로 공감한 뒤
    → "자살예방상담전화 1393(24시간)"을 안내하세요.
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
    var huggingFaceRepoID = "slyeee/maum-on-eeve-2.8b-4bit" // Local EEVE Model
    var huggingFaceToken = ""
    
    // URL 관리 → APIService.swift > ServerConfig
    let configServerURL = ServerConfig.apiBase + "/config"
    let modelFiles = [
        "config.json",
        "model.safetensors",
        "model.safetensors.index.json",
        "tokenizer.json",
        "tokenizer_config.json"
    ]
    
    // MARK: - Remote Config
    func fetchRemoteConfig() async -> Bool {
        guard let url = URL(string: configServerURL) else { return false }
        
        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            
            guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                return false
            }
            
            if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
               let hf = json["huggingface"] as? [String: String] {
                
                if let repo = hf["repo_id"] { self.huggingFaceRepoID = repo }
                if let token = hf["token"] { self.huggingFaceToken = token }
                return true
            }
        } catch {
        }
        return false
    }

    // [OOM Shield] 메모리 경고 수신 시 즉시 모델 언로드
    var memoryWarningObserver: NSObjectProtocol?
    
    init() {
        // [UX] Request Notification Permission for AI Ready Alert
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { _, _ in }
        
        // [OOM Shield] 메모리 경고 감지 → 즉시 모델 해제 (jetsam kill 사전 방지)
        #if os(iOS)
        memoryWarningObserver = NotificationCenter.default.addObserver(
            forName: UIApplication.didReceiveMemoryWarningNotification,
            object: nil, queue: .main
        ) { [weak self] _ in
            self?.modelContainer = nil
            self?.isModelLoaded = false
            self?.isProcessingQueue = false
            self?.analysisQueue.removeAll()
        }
        #endif
    }
    
    deinit {
        if let observer = memoryWarningObserver {
            NotificationCenter.default.removeObserver(observer)
        }
    }

    var currentGenerationTask: Task<Void, Never>?
    
    // FINAL VERSION: Hybrid Supporting
    // [Visibility Fix] AppChatView needs access to check status
    var analysisQueue: [Diary] = []
    var isProcessingQueue = false
    
    func toggleAIMode() {
        useServerAI.toggle()
    }
    
}
