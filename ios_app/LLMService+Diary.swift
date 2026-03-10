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
    // [Mode: 1-by-1 Strict]
    // 큐에 쌓지 않고, 분석 중이면 아예 요청을 거절함 (User Request)
    func tryEnqueueDiaryAnalysis(_ diary: Diary) -> Bool {
        if isProcessingQueue || !analysisQueue.isEmpty {
            return false
        }
        
        analysisQueue.append(diary)
        
        processQueue()
        return true
    }
    
    func processQueue() {
        if isProcessingQueue { return }
        isProcessingQueue = true
        
        Task {
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
                await performFullAnalysis(for: diary)
                
                // [Memory] Rest time expanded to 4.0s (Safety first)
                try? await Task.sleep(nanoseconds: 4_000_000_000)
                await Task.yield()
                
                // [Memory - Aggressive] Unload after every item
                await MainActor.run { self.unloadModel() }
                
                // Unload 후에도 잠시 대기
                try? await Task.sleep(nanoseconds: 1_000_000_000)
            }
            
            await MainActor.run {
                self.isProcessingQueue = false
            }
        }
    }
    
    // [OOM Shield] LLM 추론 없이 규칙 기반으로 분석 결과 생성 (메모리 부족 시 Fallback)
    func performRuleBasedFallback(for diary: Diary) async {
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
                }
            }
        }
    }
    // MARK: - [Light Analysis] 경량 2-in-1 추론 (감정분류 + 공감 한줄)
    // 2B Q4 모델에 적합한 태스크만 수행 (150토큰, ~8초)
    // 기존 7점 심층분석(700토큰, ~40초)을 대체
    func generateLightAnalysis(diaryText: String) async -> (String, String) {
        // [Auto-Recovery] 모델이 없으면 자동 로드
        if self.modelContainer == nil {
            await loadModel()
            try? await Task.sleep(nanoseconds: 2 * 1_000_000_000)
        }
        
        guard let container = self.modelContainer else {
            let empathy = getEmergencyEmpathy(for: diaryText)
            return ("Neutral (50%)", empathy)
        }
        
        let prompt = """
        당신은 따뜻한 감정 케어 도우미 '마음온'입니다.
        사용자의 일기를 읽고 두 가지만 답하세요.
        
        [사용자의 일기]:
        \(diaryText)
        
        [지시사항]
        1. 감정 분류: 아래 감정 중 하나를 골라 "감정명 (확률%)" 형식으로 답하세요.
           [행복, 슬픔, 분노, 두려움, 놀람, 평온, 불안, 우울, 스트레스, 기쁨, 사랑, 혼란, 흥분, 지침]
        2. 공감 한마디: 80자 이내 한국어 해요체로 따뜻한 공감 한 문장을 건네세요.
           - 공허한 격려("힘내세요", "잘 될 거예요") 금지
           - 구체적 감정 인정 + 작은 제안을 포함하세요
        
        [출력 형식] (반드시 이 형식을 지키세요):
        [EMOTION] 감정명 (확률%)
        [COMMENT] 공감 한마디
        """
        
        do {
            var session = ChatSession(container, instructions: "")
            session.generateParameters = GenerateParameters(
                maxTokens: 150,
                temperature: 0.6,
                topP: 0.9,
                repetitionPenalty: 1.1,
                repetitionContextSize: 5
            )
            
            var result = ""
            for try await chunk in session.streamResponse(to: prompt) {
                if Task.isCancelled { break }
                result += chunk
            }
            
            if result.isEmpty {
                let empathy = getEmergencyEmpathy(for: diaryText)
                return ("Neutral (50%)", empathy)
            }
            
            return parseLightResponse(result, originalText: diaryText)
            
        } catch {
            let empathy = getEmergencyEmpathy(for: diaryText)
            return ("Neutral (50%)", empathy)
        }
    }
    
    // MARK: - [Light Parser] 경량 분석 응답 파싱
    func parseLightResponse(_ raw: String, originalText: String) -> (String, String) {
        let clean = raw.trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: "```", with: "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
        
        var emotion = ""
        var comment = ""
        
        // Stage 1: 구조화 포맷 [EMOTION] / [COMMENT]
        if clean.contains("[EMOTION]") || clean.contains("[COMMENT]") {
            if let emotionRange = clean.range(of: "[EMOTION]") {
                let after = String(clean[emotionRange.upperBound...])
                emotion = after.components(separatedBy: "\n").first?
                    .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
                if let bracket = emotion.range(of: "[") {
                    emotion = String(emotion[..<bracket.lowerBound]).trimmingCharacters(in: .whitespacesAndNewlines)
                }
            }
            if let commentRange = clean.range(of: "[COMMENT]") {
                let after = String(clean[commentRange.upperBound...])
                comment = after.components(separatedBy: "\n").first?
                    .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
                if let bracket = comment.range(of: "[") {
                    comment = String(comment[..<bracket.lowerBound]).trimmingCharacters(in: .whitespacesAndNewlines)
                }
            }
        }
        
        // Stage 1.5: [ADVICE] 포맷도 허용 (모델이 COMMENT 대신 ADVICE로 답할 수 있음)
        if comment.isEmpty, let adviceRange = clean.range(of: "[ADVICE]") {
            let after = String(clean[adviceRange.upperBound...])
            comment = after.components(separatedBy: "\n").first?
                .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        }
        
        // Stage 2: 줄 단위 추론
        if emotion.isEmpty && comment.isEmpty {
            let lines = clean.components(separatedBy: "\n").filter { !$0.trimmingCharacters(in: .whitespaces).isEmpty }
            for line in lines {
                let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
                if emotion.isEmpty && trimmed.contains("%") && trimmed.contains("(") {
                    emotion = trimmed
                } else if comment.isEmpty && trimmed.range(of: "[가-힣]", options: .regularExpression) != nil && trimmed.count > 5 {
                    comment = trimmed
                }
            }
        }
        
        // Stage 3: Fallback
        if emotion.isEmpty { emotion = "Neutral (50%)" }
        if comment.isEmpty { comment = getEmergencyEmpathy(for: originalText) }
        
        // 한글 확인
        let hasKorean = comment.range(of: "[가-힣]", options: .regularExpression) != nil
        if !hasKorean {
            comment = getEmergencyEmpathy(for: originalText)
        }
        
        return (emotion, comment)
    }
    
    // MARK: - [Deprecated] 기존 통합 분석 (7점 심층분석 포함, 700토큰)
    // 참고: 기존 데이터 호환을 위해 함수 자체는 유지. 신규 호출은 generateLightAnalysis() 사용 권장.
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
                let empathy = getEmergencyEmpathy(for: diaryText)
                return ("Neutral (50%)", empathy, "AI 분석 결과가 비어있어 규칙 기반으로 대체했어요.")
            }
            
            // 4단계 Fallback 파싱 (Stage 1부터 시작 → 정상 응답은 Stage 1에서 완료)
            return parseUnifiedResponse(result, originalText: diaryText)
            
        } catch {
            let empathy = getEmergencyEmpathy(for: diaryText)
            return ("Neutral (50%)", empathy, "AI 분석 중 오류가 발생했어요.")
        }
    }
    
    // MARK: - [Risk Elimination] 4단계 Fallback 파싱
    // Stage 1: 구조화 포맷 [EMOTION]/[ADVICE]/[ANALYSIS]
    // Stage 2: 줄 단위 추론 (첫 줄=감정, 나머지=조언+분석)
    // Stage 3: 키워드 기반 공감 (getEmergencyEmpathy)
    // Stage 4: 최종 기본값
    func parseUnifiedResponse(_ raw: String, originalText: String) -> (String, String, String) {
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
                    }
                }
            }
        }
        
        // === Stage 2: 줄 단위 추론 (구조화 포맷 파싱이 빈 결과를 낸 경우) ===
        if emotion.isEmpty && advice.isEmpty && analysis.isEmpty {
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
            advice = getEmergencyEmpathy(for: originalText)
        }
        
        // === Stage 4: 최종 기본값 ===
        if emotion.isEmpty { emotion = "Neutral (50%)" }
        if analysis.isEmpty { analysis = "감정의 흐름을 파악하고 있어요." }
        
        // 한글 감지 실패 시 전체 Fallback
        let hasKorean = (advice + analysis).range(of: "[가-힣]", options: .regularExpression) != nil
        if !hasKorean {
            advice = getEmergencyEmpathy(for: originalText)
            analysis = "천천히 기록하며 마음을 정리해보세요."
        }
        
        return (emotion, advice, analysis)
    }

    func performFullAnalysis(for diary: Diary) async {
        // [Risk Elimination] 전체 분석 과정을 try-catch로 감싸 어떤 예외도 크래시로 이어지지 않음
        do {
            // Prepare Text
            let fullText = """
            사건: \(diary.event ?? "")
            감정: \(diary.emotion_desc ?? "")
            의미: \(diary.emotion_meaning ?? "")
            혼잣말: \(diary.self_talk ?? "")
            """
            
            // [Light Analysis] 경량 추론으로 변경 (150토큰, ~8초)
            // 기존: generateUnifiedAnalysis() → 700토큰, 7점 심층분석 포함, ~40초
            // 변경: generateLightAnalysis() → 150토큰, 감정분류+공감 한줄, ~8초
            let (emotion, comment) = await generateLightAnalysis(diaryText: fullText)
            
            // Update Diary Model (기존 필드 호환 유지)
            var updatedDiary = diary
            updatedDiary.ai_prediction = emotion
            updatedDiary.ai_advice = comment    // 공감 한줄
            updatedDiary.ai_comment = comment   // Fallback (같은 값)
            updatedDiary.ai_analysis = ""       // 경량 모드: 심층분석 생략 (기존 데이터는 보존됨)
            
            
            // Save to Local & Trigger Sync
            await MainActor.run {
                LocalDataManager.shared.saveDiary(updatedDiary) { success in
                    if success {
                    } else {
                    }
                }
            }
        } catch {
            // [Risk Elimination] 어떤 에러가 발생해도 앱 크래시를 방지
            await performRuleBasedFallback(for: diary)
        }
    }

}
