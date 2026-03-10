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
    
    let modelName = "mlx-community/gemma-2-2b-it-4bit"
    var modelContainer: ModelContainer?
    
    // [System Persona] Few-Shot Prompting (예시를 통한 강력한 세뇌)
    let systemPrompt = """
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
    var huggingFaceRepoID = "slyeee/maum-on-gemma-2b" // Default Backup
    var huggingFaceToken = ""
    
    // Constants
    // [Target Fix] Updated to 217 Server (app.py: /api/config)
    let configServerURL = "https://217.142.253.35.nip.io/api/config"
    let modelFiles = [
        "config.json",
        "model.safetensors",
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "tokenizer.model"
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
