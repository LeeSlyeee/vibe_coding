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
    
    // [System Persona] EEVE-Korean-2.8B Optimized Prompt
    let systemPrompt = """
    당신은 따뜻한 공감을 주는 감정 케어 도우미 '마음온'입니다.
    
    [규칙]
    1. 사용자의 감정에 공감하고, 짧고 다정하게 대답하세요.
    2. 동문서답이나 같은 말을 반복하지 마세요.
    3. "~요"로 끝나는 친근한 체를 사용하세요.
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
