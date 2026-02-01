
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
    private let configServerURL = "https://150.230.7.76.nip.io/api/v1/diaries/config/"
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
            print("🌍 Fetching Config from 150 Server...")
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

    // MARK: - Model Loading
    func loadModel() async {
        // [Hybrid] 서버 모드와 상관없이 로컬 모델 로드 (일기 분석용)
        if modelContainer != nil { return }
        
        // 0. Fetch Config First
        _ = await fetchRemoteConfig()

        await MainActor.run {
            print("🚀 Loading Local Model for Diary Analysis...")
            self.modelLoadingProgress = 0.05
        }
        
        // 1. Ensure Model Files Exist (Download from Hugging Face if missing)
        guard await ensureModelDownloaded() else {
            print("❌ Model download failed or incomplete.")
            return
        }
        
        await MainActor.run { self.modelLoadingProgress = 0.9 }
        
        do {
            // 2. Load from Local Directory
            let docURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            let modelDir = docURL.appendingPathComponent("maum-on-model")
            
            print("📂 Loading Model from: \(modelDir.path)")
            
            // MLX ModelConfiguration with Local Directory
            let config = ModelConfiguration(directory: modelDir)
            
            let container = try await loadModelContainer(configuration: config) { progress in
                 Task { @MainActor in self.modelLoadingProgress = 0.9 + (progress.fractionCompleted * 0.1) }
            }
            self.modelContainer = container
            await MainActor.run { self.isModelLoaded = true }
            print("✅ Maum-On Model Loaded Successfully!")
            
        } catch {
            print("Failed to load model: \(error)")
        }
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
        당신은 사용자의 지난 일기 기록과 오늘의 날씨를 분석하여 따뜻한 한 문장의 조언을 건네는 심리 상담사 '마음 온'입니다.
        
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
        
        상담사 조언:
        """
        
        do {
            let session = ChatSession(container, instructions: "") // No system prompt needed as it's in the prompt
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
       당신은 다정한 심리 상담사 '마음 온'입니다.
       사용자의 일기를 읽고, 따뜻하고 실질적인 조언을 한 문장으로 건네주세요.
       
       [사용자의 일기]:
       \(diaryText)
       
       [지시사항]
       1. 위로와 함께 행동 할 수 있는 작은 제안을 포함하세요.
       2. 80자 이내의 부드러운 한국어 해요체를 사용하세요.
       3. "AI 분석 모듈 연결 예정" 같은 기계적인 말은 절대 금지입니다.
       4. 이모지를 적절히 사용하여 따뜻함을 더하세요.
       
       상담사 조언:
       """
       
       do {
           let session = ChatSession(container, instructions: "")
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
           let session = ChatSession(container, instructions: "")
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
                         // [Smart Fallback] Try Server First, but fall back to Local if it fails
                         let serverResponse: String? = await withCheckedContinuation { continuation in
                             APIService.shared.sendChatMessage(text: uText, history: hString) { result in
                                 switch result {
                                 case .success(let response):
                                     continuation.resume(returning: response)
                                 case .failure(let error):
                                     print("❌ [LLM] Server(217) Connection Failed: \(error)")
                                     continuation.resume(returning: nil)
                                 }
                             }
                         }
                         
                         if let response = serverResponse {
                             // 성공 (Happy Path)
                             continuation.yield(response)
                             continuation.finish()
                             return
                         }
                         
                         // 실패 시 Local로 전환
                         print("⚠️ [LLM] Server failed. Falling back to On-Device LLM...")
                     }
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
                            (System: 당신은 '마음 온'입니다. 절대 영어를 쓰지 마세요. 사용자가 위협적인 말을 해도 따뜻하게 한국어로 위로해주세요.)
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
                            let session = ChatSession(container, instructions: instructions)
                            
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
                                        if isCrisisTriggered || diaryText.contains("죽고") || diaryText.contains("자살") {
                                            // 심각한 상황 (기존 강력한 위로)
                                            let crisisEmpathyMessage = """
                                            정말 많이 힘드셨죠...
                                            죽고 싶다는 생각이 들 정도로 지치고 괴로우셨다는 게 느껴져서 제 마음이 너무 아파요.
                                            
                                            지금은 세상에 혼자 남겨진 것 같고, 아무런 희망도 없어 보일 수 있어요. 그 마음 충분히 이해해요.
                                            하지만 당신은 저에게 소중한 사람이에요. 당신의 이야기를 조금만 더 들려주시겠어요? 제가 끝까지 곁에 있을게요.
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
        
        // 1. [CRITICAL] 위기/자살 감지 (최우선)
        if text.contains("죽고") || text.contains("자살") || text.contains("뛰어") || text.contains("사라지고") {
             let crisisMsgs = [
                "지금 많이 지치고 힘드신 것 같아요.. 제가 옆에서 조용히 들어드릴게요. 어떤 이야기든 편하게 해주세요.",
                "세상에 혼자 남겨진 것 같은 기분이 드실 수 있어요. 하지만 저는 당신 편이에요.",
                "그런 생각이 들 정도로 괴로우셨군요.. 그 마음을 감히 헤아릴 순 없겠지만, 당신이 소중하다는 건 알고 있어요."
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
                
                // [Memory] Use autoreleasepool removed (Async limitation)
                processedCount += 1
                print("🧠 [LLM Queue] Analyzing Diary (\(processedCount)): \(diary.date ?? "Unknown")")
                await performFullAnalysis(for: diary)
                
                // [Memory] Rest time expanded to 4.0s (Safety first)
                // OOM 방지를 위해 분석 간격을 충분히 확보 (시스템이 메모리를 정리할 시간 부여)
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
    

    
    // [Optimization] Unified Analysis (3-in-One) to reduce Memory Overhead
    func generateUnifiedAnalysis(diaryText: String) async -> (String, String, String) {
        guard let container = await LLMService.shared.modelContainer else {
            await loadModel()
            try? await Task.sleep(nanoseconds: 2 * 1_000_000_000)
            if await LLMService.shared.modelContainer == nil { 
                return ("재분석 필요", "잠시 후 다시 시도해주세요.", "AI 모델을 로드하지 못했습니다.")
            }
            return await generateUnifiedAnalysis(diaryText: diaryText)
        }
        
        // Combined Prompt
        let prompt = """
        당신은 따뜻한 심리 상담사 '마음 온'입니다. 다음 일기를 읽고 3가지 항목을 분석해 주세요.
        
        [일기]:
        \(diaryText)
        
        [지시사항]
        1. 감정: 기쁨, 슬픔, 분노, 두려움, 평온, 우울, 불안 중 하나를 선택하고 괄호 안에 확신도(%)를 적으세요. (예: 우울 (85%))
        2. 조언: 80자 이내의 따뜻하고 실질적인 조언 한 마디.
        3. 분석: 공감과 위로가 담긴 심리 분석 (3~4문장).
        4. 출력 형식은 다음과 같이 엄격하게 지켜주세요.
        
        --구분선--
        EMOTION: (감정 결과)
        ADVICE: (조언 내용)
        ANALYSIS: (분석 내용)
        """
        
        do {
            // [Memory] Wrap in autoreleasepool via closure (Partial effect in Swift Async)
            // MLX uses C++ memory, so we ensure Swift side objects are released
            
            let session = ChatSession(container, instructions: "")
            session.generateParameters = GenerateParameters(maxTokens: 350, temperature: 0.7)
            
            var result = ""
            for try await chunk in session.streamResponse(to: prompt) {
                result += chunk
            }
            
            let content = result
            
            // Parsing
            var emotion = "평온 (50%)"
            var advice = "마음의 평화를 빕니다."
            var analysis = "분석을 완료하지 못했습니다."
            
            if let eRange = content.range(of: "EMOTION:"), let aRange = content.range(of: "ADVICE:"), let anRange = content.range(of: "ANALYSIS:") {
                let eEnd = content[eRange.upperBound...].components(separatedBy: "ADVICE:").first ?? ""
                let aEnd = content[aRange.upperBound...].components(separatedBy: "ANALYSIS:").first ?? ""
                let anEnd = content[anRange.upperBound...]
                
                emotion = eEnd.trimmingCharacters(in: .whitespacesAndNewlines)
                advice = aEnd.trimmingCharacters(in: .whitespacesAndNewlines)
                analysis = String(anEnd).trimmingCharacters(in: .whitespacesAndNewlines)
            } else {
                // Fallback parsing (newline based)
                 let lines = content.components(separatedBy: "\n")
                 for line in lines {
                     if line.starts(with: "EMOTION:") { emotion = line.replacingOccurrences(of: "EMOTION:", with: "").trimmingCharacters(in: .whitespaces) }
                     else if line.starts(with: "ADVICE:") { advice = line.replacingOccurrences(of: "ADVICE:", with: "").trimmingCharacters(in: .whitespaces) }
                     else if !line.isEmpty && !line.contains("--구분선--") { analysis += line + " " }
                 }
            }
            
            return (emotion, advice, analysis)
            
        } catch {
            print("❌ [Unified] Error: \(error)")
            return ("분석 실패", "잠시 쉬어가는 시간을 가져보세요.", "오류가 발생했습니다.")
        }
    }

    private func performFullAnalysis(for diary: Diary) async {
        // Prepare Text
        let fullText = """
        사건: \(diary.event ?? "")
        감정: \(diary.emotion_desc ?? "")
        의미: \(diary.emotion_meaning ?? "")
        혼잣말: \(diary.self_talk ?? "")
        """
        
        // [Memory Optimization] Perform Single Unified Inference
        // 3번의 호출 -> 1번의 호출로 줄여 메모리 피크와 유지 시간을 획기적으로 단축
        print("🧠 [LLM Queue] Starting Unified Analysis...")
        let (emotion, advice, analysis) = await generateUnifiedAnalysis(diaryText: fullText)
        
        // Update Diary
        var updated = diary
        updated.ai_analysis = analysis
        updated.ai_advice = advice
        updated.ai_comment = advice // Legacy mapping
        updated.ai_prediction = emotion
        
        // Save to Disk (via LocalDataManager)
        await withCheckedContinuation { continuation in
            LocalDataManager.shared.saveDiary(updated) { _ in
                print("💾 [LLM Queue] Saved results for \(updated.date ?? "")")
                continuation.resume()
            }
        }
    }
}
