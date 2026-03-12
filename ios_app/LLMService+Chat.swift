import Foundation
import UserNotifications
#if os(iOS)
import UIKit
#endif
#if canImport(MLX) && !targetEnvironment(simulator)
import MLX
import MLXLMCommon
import MLXRandom
import MLXLLM
#endif

extension LLMService {
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
                     
                     if let uText = userText, let hString = historyString {
                         // [Strict Server Mode] Only use Server, No Local Fallback
                         let serverResponse: String? = await withCheckedContinuation { continuation in
                             APIService.shared.sendChatMessage(text: uText, history: hString) { result in
                                 switch result {
                                 case .success(let response):
                                     continuation.resume(returning: response)
                                 case .failure(let error):
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
                            // 프롬프트 오염 제거 (System 지시문은 ChatSession 초기화 시에만 전달)
                            var specificPrompt = diaryText
                            
                            // [Retry] 재시도일 경우에만 강력한 강제 조건 추가
                            if attempt > 1 {
                                specificPrompt = """
                                [규칙: 반드시 한국어로, 동문서답 없이 대답할 것]
                                \(diaryText)
                                """
                            }
                            let isChatMode = (userText != nil)
                            let instructions = await LLMService.shared.systemPrompt
                            
                            // [Architecture Revert] 하드코딩 우회로 전면 폐기 및 정석적 ChatSession 복구
                            // MLX 자체의 ChatSession 내부 기록(history) 메커니즘을 통한 컨텍스트 유지 보장
                            var session: ChatSession
                            if isChatMode, let persistentSession = await LLMService.shared.chatSession {
                                session = persistentSession
                            } else {
                                session = ChatSession(container, instructions: instructions)
                            }
                            
                            // [Smart Token Allocation] 입력 길이에 따른 유동적 토큰 할당
                            let inputLen = diaryText.count
                            var dynamicMaxTokens = 180 
                            
                            if isChatMode {
                                dynamicMaxTokens = 120 
                            } else {
                                if inputLen < 50 {
                                    dynamicMaxTokens = 120 
                                } else if inputLen > 200 {
                                    dynamicMaxTokens = 256 
                                }
                            }
                            
                            // [LLM Tuning] 앵무새 무한 반복(OOM 유사 증상)과 환각을 동시에 억제하는 균형점 (Balance)
                            session.generateParameters = GenerateParameters(
                                maxTokens: dynamicMaxTokens, 
                                temperature: 0.5,        // 너무 낮으면(0.3) 이전에 했던 뻔한 말(로컬 미니마)로 빠지므로 0.5로 변주를 줌
                                topP: 0.9,
                                repetitionPenalty: 1.25, // 한국어 기본 조사 연속 패턴을 파손시키지 않는 안정된 페널티 적용 (조금 강화)
                                repetitionContextSize: 256 // [CRITICAL FIX] 20은 고작 한 문장 길이라 자기가 옛날에 한 말을 까먹고 다시 앵무새처럼 반복함. 256으로 늘려서 이전 턴 대화까지 겹치는지 검사!
                            ) 
                            
                            var accumulatedText = ""
                            var hasHijacked = false
                            
                            // 프레임워크가 알아서 ChatML 템플릿에 맞추어 히스토리와 함께 토크나이징 하도록 순수 입력 전달
                            let rawInput = isChatMode ? (userText ?? diaryText) : diaryText
                            
                            for try await chunk in session.streamResponse(to: rawInput) {
                                if Task.isCancelled { break }
                                
                                // [Hallucination Kill-Switch] 청크 단위가 아닌 누적 텍스트로 패턴 검사 (단어가 잘려 들어와도 감지)
                                let tempAccumulated = accumulatedText + chunk
                                
                                let hasHallucination = tempAccumulated.contains(";") || tempAccumulated.contains("{") || tempAccumulated.contains("}") || tempAccumulated.contains("`") || tempAccumulated.range(of: "[a-zA-Z]{5,}", options: .regularExpression) != nil
                                
                                // 텍스트 실제 누적
                                accumulatedText = tempAccumulated
                                
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
                                        }
                                    }
                                    
                                    if isCrisisTriggered || isEnglishTriggered || isEnglishStart || hasHallucination {
                                        hasHijacked = true
                                        
                                        // 3. UI 클리어 신호 전송 (기존 영어 텍스트 삭제)
                                        continuation.yield("[RESET]")
                                        
                                        // [Retry Check] 첫 번째 실패라면 -> 재시도 (continue logic)
                                        if attempt < 2 {
                                            break // 현재 스트림 중단 -> while 루프 다음 턴으로
                                        }
                                        
                                        // 두 번째 실패라면 -> Fallback 메시지 (위기 상황 별도 핸들링)
                                        if isCrisisTriggered || diaryText.contains("죽고") || diaryText.contains("자살") || diaryText.contains("자해") || diaryText.contains("끝내고") {
                                            // 심각한 상황 — AI 자유 생성 차단, 사전 정의 안전 메시지만 사용
                                            let crisisEmpathyMessage = """
                                            정말 많이 힘드셨죠...
                                            
                                            혼자 감당하지 않으셔도 돼요. 당신은 소중한 사람이에요.
                                            
                                            지금 바로 전문 상담사와 이야기해 보세요.
                                             자살예방상담전화: 1393 (24시간 무료)
                                             정신건강위기상담: 1577-0199
                                            """
                                             continuation.yield(crisisEmpathyMessage)
                                        } else {
                                            // 단순 영어/오류 상황 (일반적인 공감)
                                            let mildEmpathyMessage = """
                                            저런... 많이 속상하고 힘드셨겠어요. 
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
                "지금 많이 힘드시죠.. 저는 당신 편이에요.\n\n혼자 감당하지 않으셔도 돼요. 지금 바로 전문 상담사와 이야기해 보세요.\n 자살예방상담전화: 1393 (24시간)",
                "그런 생각이 들 정도로 괴로우셨군요..\n당신이 소중하다는 건 꼭 알아주세요.\n\n지금 바로 전문가의 도움을 받을 수 있어요.\n 1393 (24시간 무료)",
                "혼자서 이 마음을 감당하기 너무 힘드셨죠..\n\n전문 상담사가 24시간 기다리고 있어요.\n 자살예방상담전화: 1393\n 정신건강위기상담: 1577-0199"
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
    // [New] 범용 텍스트 생성 (분석 리포트 온디바이스 Fallback용)
    func generateText(prompt: String) async throws -> String {
        guard let container = self.modelContainer else {
            throw NSError(domain: "LLM", code: -1, userInfo: [NSLocalizedDescriptionKey: "모델이 로드되지 않음"])
        }
        
        var session = ChatSession(container, instructions: "당신의 이름은 '마음온'입니다. 당신은 따뜻한 감정 케어 도우미 '마음온'입니다. 한국어 해요체로 답해주세요.")
        session.generateParameters = GenerateParameters(
            maxTokens: 300, 
            temperature: 0.65,
            topP: 0.9,
            repetitionPenalty: 1.3,
            repetitionContextSize: 20
        )
        
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

}
