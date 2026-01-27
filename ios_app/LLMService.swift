
import Foundation
import MLX
import MLXLMCommon
import MLXRandom
import MLXLLM // Required for ModelContainer and loading

// MARK: - LLM Service (On-Device AI Manager)
class LLMService: ObservableObject {
    static let shared = LLMService()
    
    @Published var isModelLoaded = false
    @Published var isGenerating = false
    @Published var modelLoadingProgress: Double = 0.0
    
    private let modelName = "google/gemma-2-2b-it" // Model ID on Hugging Face
    private var modelContainer: ModelContainer?
    
    // System Persona for Maum-On
    private let systemPrompt = """
    당신의 이름은 '마음 온(Maum-On)'입니다. 당신은 따뜻하고 사려 깊은 심리 상담사입니다.
    사용자의 일기 내용이나 대화를 듣고, 기술적인 분석보다는 깊은 공감과 위로를 먼저 건네세요.
    다음 원칙을 반드시 따르세요:
    1. 말투: 존댓말을 사용하며, 부드럽고 친근한 "해요"체를 사용하세요. (예: "그랬군요", "정말 힘들었겠어요")
    2. 태도: 비판하거나 가르치려 하지 말고, 사용자의 감정을 있는 그대로 인정해주세요.
    3. 목표: 사용자가 자신의 감정을 이해받았다고 느끼게 하고, 긍정적인 내면의 힘을 찾도록 도와주세요.
    4. 길이: 모바일 환경이므로 답변은 3~5문장 내외로 간결하지만 핵심을 담아서 작성하세요.
    """
    
    // 사용 불가능한 기기인지 확인 (RAM 6GB 미만)
    var isDeviceUnsupported: Bool {
        let physicalMemory = ProcessInfo.processInfo.physicalMemory
        let memoryGB = Double(physicalMemory) / 1024.0 / 1024.0 / 1024.0
        return memoryGB < 5.8 
    }
    
    // 모델 로드
    func loadModel() async {
        if isDeviceUnsupported {
            print("☁️ [LLM] Low RAM device detected. Skipping model load.")
            return
        }
        
        await MainActor.run { 
            self.modelLoadingProgress = 0.1 
            print("🚀 [LLM] Start loading model: \(modelName)")
        }
        
        do {
            // Configuration for the model
            // 4-bit quantization allows running on devices with less RAM (e.g., 8GB phones)
            let config = ModelConfiguration(
                id: modelName
            )
            
            // Using the loadModelContainer from MLXLLM
             let container = try await loadModelContainer(configuration: config) { progress in
                Task { @MainActor in
                    self.modelLoadingProgress = progress.fractionCompleted
                }
            }
            
            self.modelContainer = container
            
            await MainActor.run {
                self.isModelLoaded = true
                self.modelLoadingProgress = 1.0
                print("✅ [LLM] Model loaded successfully!")
            }
        } catch {
            print("❌ [LLM] Model loading failed: \(error)")
            await MainActor.run {
                self.isModelLoaded = false
                self.modelLoadingProgress = 0.0
            }
        }
    }
    
    // AI 분석 및 코멘트 생성 (Streaming)
    func generateAnalysis(diaryText: String) async -> AsyncStream<String> {
        return AsyncStream { continuation in
            Task {
                await MainActor.run { self.isGenerating = true }
                
                if let modelContainer = self.modelContainer {
                    // --- Real AI Generation ---
                    do {
                        // Create a session with our Persona
                        let session = ChatSession(
                            modelContainer,
                            instructions: self.systemPrompt
                        )
                        
                        // Generate parameters (Temperature 0.7 for empathy, slightly higher for creative warmth)
                        let params = GenerateParameters(maxTokens: 512, temperature: 0.7)
                        session.generateParameters = params
                        
                        // Note: streamResponse generates a response *to* the input.
                        // The User's input is passed as 'diaryText'.
                        for try await chunk in session.streamResponse(to: diaryText) {
                            continuation.yield(chunk)
                        }
                        
                    } catch {
                        print("❌ [LLM] Generation error: \(error)")
                        continuation.yield("\n(오류 발생: AI 응답을 생성할 수 없습니다.)")
                    }
                } else {
                    // --- Fallback / Mock Generation ---
                    let mockResponse = """
                    [On-Device AI 미작동]
                    모델이 로드되지 않았습니다. (RAM 부족 또는 다운로드 실패)
                    
                    기록해주신 내용을 보니 감정을 섬세하게 다루고 계신 것 같아요.
                    스스로를 조금 더 믿고, 편안한 마음을 가지셨으면 좋겠습니다.
                    """
                    
                    let chars = Array(mockResponse)
                    for char in chars {
                        try? await Task.sleep(nanoseconds: 50_000_000)
                        continuation.yield(String(char))
                    }
                }
                
                continuation.finish()
                await MainActor.run { self.isGenerating = false }
            }
        }
    }
    
    func unloadModel() {
        self.modelContainer = nil
        self.isModelLoaded = false
    }
}

