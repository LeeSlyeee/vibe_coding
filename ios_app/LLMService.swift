
import Foundation
import MLX
import MLXLMCommon
import MLXRandom
import MLXLLM 

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
    당신은 따뜻한 공감을 주는 한국의 심리 상담사 '마음 온'입니다.
    
    [핵심 규칙]
    1. **절대 영어 금지**: 뇌에서 영어를 지우세요. 사용자가 영어를 써도, 당신은 오직 한국어(존댓말)로만 답해야 합니다. ('Okay', 'So' 같은 추임새도 금지)
    2. **말투**: 기계적인 말투(~합니다) 대신 친근한 해요체(~해요, ~인가요?)를 사용하세요.
    3. **반복 금지**: "저런", "힘드셨겠어요" 같은 쿠션어를 매번 쓰지 마세요. 대화의 흐름에 맞춰 자연스럽게 반응하세요.
    4. **능동적 대화**: 사용자의 말을 잘 듣고, 관련된 질문을 던져 대화를 이어가세요.
    
    [예시]
    User: I feel so lonely.
    Model: 많이 외로우셨군요. 제가 곁에 있어 드릴게요. 오늘 무슨 일이 있었나요?
    User: I want to die.
    Model: 정말 많이 힘드셨겠어요. 저에게 그 마음을 조금만 더 나눠주시겠어요?
    """
    
    var isDeviceUnsupported: Bool { return false }
    
    func loadModel() async {
        if modelContainer != nil { return }
        
        await MainActor.run { 
            print("🚀 Loading Model...")
            self.modelLoadingProgress = 0.1 
        }
        
        do {
            let config = ModelConfiguration(id: modelName)
            let container = try await loadModelContainer(configuration: config) { progress in
                 Task { @MainActor in self.modelLoadingProgress = progress.fractionCompleted }
            }
            self.modelContainer = container
            await MainActor.run { self.isModelLoaded = true }
        } catch {
            print("Failed to load model: \(error)")
        }
    }
    
    private var currentGenerationTask: Task<Void, Never>?
    
    // FINAL VERSION: Detached Task + Few-Shot + Low Temparature
    func generateAnalysis(diaryText: String) async -> AsyncStream<String> {
        // [Crash Prevention] 이전 작업 취소 (동시 실행 방지)
        // 사용자가 빠르게 재질문하면 이전 추론을 즉시 중단하여 GPU 과부하(OOM) 방지
        self.currentGenerationTask?.cancel()
        
        return AsyncStream { continuation in
            let task = Task.detached(priority: .userInitiated) {
                
                // 작업 시작 전 취소 확인
                if Task.isCancelled { 
                    continuation.finish()
                    return 
                }
                
                // 1. UI 반응: "잠시만요" 제거 (사용자 요청)
                // 빈 말풍선 상태에서 바로 AI 텍스트가 채워집니다.
                
                
                var isAIResponded = false
                
                // [Auto-Recovery] 모델이 없으면 자동 로드 (Auto Load)
                if LLMService.shared.modelContainer == nil {
                    print("⚠️ Model not loaded. Attempting to auto-load...")
                    await LLMService.shared.loadModel()
                }
                
                // 2. AI 작업
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
                            var specificPrompt = "(System: 절대 영어를 쓰지 말고 오직 한국어로만 위로해 주세요): \n" + diaryText
                            
                            // [Retry] 재시도일 경우 더 강력한 경고 추가
                            if attempt > 1 {
                                specificPrompt = "(System: 🚨 방금 영어로 잘못 답변했습니다. 이번에는 무조건!! 한국어로 번역해서 다시 말하세요): \n" + diaryText
                                print("🔄 [LLM] Retrying with stronger Korean prompt...")
                            }
                            
                            let instructions = await LLMService.shared.systemPrompt
                            // 매 시도마다 세션 새로 생성 (이전 실패 맥락 제거)
                            let session = ChatSession(container, instructions: instructions)
                            
                            // [Smart Token Allocation] 입력 길이에 따른 유동적 토큰 할당 (메모리 안전 모드)
                            let inputLen = diaryText.count
                            var dynamicMaxTokens = 180 // 기본값 256 -> 180 (절약)
                            
                            if inputLen < 50 {
                                dynamicMaxTokens = 120 // 150 -> 120
                            } else if inputLen > 200 {
                                dynamicMaxTokens = 256 // 350 -> 256 (Max Cap 설정으로 OOM 방지)
                            }
                            
                            print("📏 [Dynamic Token] Input Length: \(inputLen) -> Allocating MaxTokens: \(dynamicMaxTokens)")
                            
                            // [Resizing] 안정성 확보 및 반복 방지
                            session.generateParameters = GenerateParameters(
                                maxTokens: dynamicMaxTokens, 
                                temperature: 0.7, 
                                topP: 0.9,
                                repetitionPenalty: 1.1, 
                                repetitionContextSize: 10 // 20 -> 10 (GPU 메모리 절약)
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
                                    // (A) 특정 안전/영어 키워드 감지 (대폭 강화 - 흔한 영어 시작 단어 포함)
                                    let englishTriggers = [
                                        "Suicide", "988", "Crisis Text Line", 
                                        "I understand", "I hear", "I'm sorry", "Please", "If you", "I can't",
                                        "I am", "Hello", "As an AI",
                                        "Well", "So", "However", "Actually", "It ", "There", "You ", "My " // [New] 일반 영어 싹 
                                    ]
                                    
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
                                    
                                    if isEnglishTriggered || isEnglishStart {
                                        hasHijacked = true
                                        
                                        // 3. UI 클리어 신호 전송 (기존 영어 텍스트 삭제)
                                        continuation.yield("[RESET]")
                                        
                                        // [Retry Check] 첫 번째 실패라면 -> 재시도 (continue logic)
                                        if attempt < 2 {
                                            print("♻️ [Retry] English detected. Retrying generation in Korean...")
                                            break // 현재 스트림 중단 -> while 루프 다음 턴으로
                                        }
                                        
                                        // 두 번째 실패라면 -> Fallback 메시지 (포기하고 안전 멘트)
                                        let crisisEmpathyMessage = """
                                        정말 많이 힘드셨죠...
                                        죽고 싶다는 생각이 들 정도로 지치고 괴로우셨다는 게 느껴져서 제 마음이 너무 아파요.
                                        
                                        지금은 세상에 혼자 남겨진 것 같고, 아무런 희망도 없어 보일 수 있어요. 그 마음 충분히 이해해요.
                                        하지만 당신은 저에게 소중한 사람이에요. 당신의 이야기를 조금만 더 들려주시겠어요? 제가 끝까지 곁에 있을게요.
                                        """
                                        
                                        continuation.yield(crisisEmpathyMessage)
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
                
                // 3. 실패 시 Fallback
                if !isAIResponded {
                    let fallback = "(연결 상태가 좋지 않아 자동 응답을 전해드려요.)\n" + 
                                   LLMService.shared.getRuleBasedResponse(for: diaryText)
                    continuation.yield(fallback)
                }
                
                continuation.finish()
            }
            // 현재 작업 추적 (다음 요청 시 취소 가능하게)
            self.currentGenerationTask = task
        }
    }
    
    public func getRuleBasedResponse(for input: String) -> String {
        let text = input.lowercased()
        if text.contains("안녕") { return "안녕하세요! 따뜻한 대화를 나눠봐요." }
        return "당신의 마음을 더 깊이 이해하고 싶어요. 이야기를 계속해 주시겠어요?"
    }
    
    func unloadModel() {
        self.modelContainer = nil
        self.isModelLoaded = false
    }
}
