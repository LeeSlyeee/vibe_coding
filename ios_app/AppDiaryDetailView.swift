import SwiftUI

struct AppDiaryDetailView: View {
    let diary: Diary
    var onDelete: () -> Void
    var onEdit: (() -> Void)? = nil 
    
    @Environment(\.presentationMode) var presentationMode
    @State private var isDeleting = false
    @State private var showingEditSheet = false
    @State private var showErrorAlert = false
    @State private var errorMessage = ""
    
    // [Target Fix] Updated to 217 Server
    let baseURL = "https://217.142.253.35.nip.io/api"
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // 상단 날짜 및 버튼 영역
                HStack {
                    Text(formatDate(diary.created_at ?? ""))
                        .font(.title2)
                        .fontWeight(.bold)
                    Spacer()
                    
                    // 수정 버튼
                    Button(action: { showingEditSheet = true }) {
                        Image(systemName: "pencil.circle")
                            .font(.title2)
                            .foregroundColor(.blue)
                    }
                    .padding(.trailing, 10)
                    
                    // 삭제 버튼
                    Button(action: deleteDiary) {
                        Image(systemName: "trash")
                            .foregroundColor(.red)
                    }
                }
                .padding(.top)
                
                Divider()
                
                // 감정 및 내용
                HStack {
                    Text("오늘의 기분")
                        .font(.headline)
                    Spacer()
                    let mood = getMoodAsset(level: diary.mood_level)
                    VStack {
                        Image(mood.image)
                            .resizable()
                            .scaledToFit()
                            .frame(width: 50, height: 50)
                        Text(mood.title)
                            .font(.subheadline)
                            .foregroundColor(mood.color)
                    }
                }
                .padding(.vertical)
                
                Group {
                    if let sleep = getSleepContent(), !sleep.trimmingCharacters(in: .whitespaces).isEmpty {
                        label("잠은 잘 주무셨나요?")
                        Text(sleep)
                            .padding(.bottom)
                    }
                    
                    label("무슨 일이 있었나요?")
                    Text(diary.event ?? "")
                        .padding(.bottom)
                    
                    label("어떤 감정이 들었나요?")
                    Text(diary.emotion_desc ?? "")
                        .padding(.bottom)
                    
                    if let meaning = diary.emotion_meaning, !meaning.isEmpty {
                        label("감정의 의미")
                        Text(meaning)
                            .padding(.bottom)
                    }
                    
                    if let talk = diary.self_talk, !talk.isEmpty {
                        label("나에게 하는 말")
                        Text(talk)
                            .padding(.bottom)
                    }
                }
                
                // AI 분석 영역
                if let prediction = diary.ai_prediction, !prediction.isEmpty {
                   let (label, percent) = parseAIPrediction(prediction)
                   
                   VStack(alignment: .leading, spacing: 10) {
                       HStack {
                           Text("AI 감정 분석")
                               .font(.headline)
                               .foregroundColor(.blue)
                           Spacer()
                           if !percent.isEmpty {
                               Text(percent)
                                   .font(.caption)
                                   .fontWeight(.bold)
                                   .padding(.horizontal, 8)
                                   .padding(.vertical, 4)
                                   .background(Color.blue)
                                   .foregroundColor(.white)
                                   .cornerRadius(8)
                           }
                       }
                       
                       // 감정 분석 결과 (Label)
                       if !label.isEmpty {
                           Text("오늘의 주요 감정: \(label)")
                               .font(.subheadline)
                               .fontWeight(.semibold)
                               .foregroundColor(.primary)
                               .padding(.bottom, 2)
                       }
                       
                       // 상세 분석 (ai_analysis or fallback)
                       if let detail = diary.ai_analysis, !detail.isEmpty {
                           Text(detail)
                               .font(.body)
                               .padding()
                               .frame(maxWidth: .infinity, alignment: .leading) // 왼쪽 정렬
                               .background(Color.blue.opacity(0.1))
                               .cornerRadius(10)
                       }
                   }
                   .padding(.top)
                } else if let aiAnalysisOnly = diary.ai_analysis, !aiAnalysisOnly.isEmpty {
                     // Fallback for old data without prediction
                    VStack(alignment: .leading, spacing: 10) {
                        Text("AI 감정 분석")
                            .font(.headline)
                            .foregroundColor(.blue)
                        Text(aiAnalysisOnly)
                            .padding()
                            .background(Color.blue.opacity(0.1))
                            .cornerRadius(10)
                    }
                    .padding(.top)
                }
                
                // AI 조언 영역
                if let advice = (diary.ai_advice?.isEmpty == false ? diary.ai_advice : diary.ai_comment), !advice.isEmpty {
                    let cleanedAdvice = cleanAIText(advice)
                    if !cleanedAdvice.isEmpty {
                        VStack(alignment: .leading, spacing: 10) {
                            Text("AI 조언")
                                .font(.headline)
                                .foregroundColor(.green)
                            Text(cleanedAdvice)
                                .padding()
                                .background(Color.green.opacity(0.1))
                                .cornerRadius(10)
                        }
                        .padding(.top)
                    }
                }
                
                // AI 면책 고지
                if diary.ai_prediction != nil || diary.ai_analysis != nil || diary.ai_advice != nil || diary.ai_comment != nil {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("AI 분석은 참고용이며, 전문 의료 서비스를 대체하지 않습니다.")
                            .font(.caption2)
                            .foregroundColor(.gray)
                        Text("⚠️ 위기 감지는 보조적 수단이며, 100% 정확성을 보장하지 않습니다.")
                            .font(.caption2)
                            .foregroundColor(.orange)
                    }
                    .padding(.top, 4)
                }
                
                Spacer()
            }
            .padding()
        }
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .preferredColorScheme(.light)
        .screenshotProtected() // [보안] 스크린샷 방지 (설정에 따라 동작)
        // 수정 시트 연결 (+수정 완료 시 닫기 & 새로고침)
        .sheet(isPresented: $showingEditSheet) {
            // 날짜 파싱 (임시, WriteView 내부에서 다시 계산함)
            let parsedDate = parseDateString(diary.created_at ?? "") ?? Date()
            
            AppDiaryWriteView(
                isPresented: $showingEditSheet,
                date: parsedDate,
                onSave: {
                    onDelete() // 목록 갱신
                    presentationMode.wrappedValue.dismiss() // 상세 뷰 닫기
                },
                diaryToEdit: diary
            )
        }
        .alert(isPresented: $showErrorAlert) {
            Alert(title: Text("삭제 실패"), message: Text(errorMessage), dismissButton: .default(Text("확인")))
        }
    }
    
    func label(_ text: String) -> some View {
        Text(text)
            .font(.headline)
            .foregroundColor(.gray)
    }
    
    /// AI 응답에서 JSON 원문, 마크다운 코드블록, **예시 답변** 등의 잔여물을 제거
    func cleanAIText(_ text: String) -> String {
        var result = text.trimmingCharacters(in: .whitespacesAndNewlines)
        
        // 1. **예시 답변** 같은 프리픽스 제거
        let prefixes = ["**예시 답변**", "**답변**", "예시 답변"]
        for prefix in prefixes {
            if let range = result.range(of: prefix) {
                result = String(result[range.upperBound...]).trimmingCharacters(in: .whitespacesAndNewlines)
            }
        }
        
        // 2. ```json ... ``` 코드블록 내부 추출
        if result.contains("```json") || result.contains("```") {
            if let jsonBlockRange = result.range(of: "```json", options: .caseInsensitive) {
                let afterBlock = String(result[jsonBlockRange.upperBound...])
                if let endBlock = afterBlock.range(of: "```") {
                    result = String(afterBlock[..<endBlock.lowerBound]).trimmingCharacters(in: .whitespacesAndNewlines)
                }
            }
            result = result.replacingOccurrences(of: "```", with: "").trimmingCharacters(in: .whitespacesAndNewlines)
        }
        
        // 3. JSON 객체인 경우 comment 필드만 추출
        if result.hasPrefix("{") {
            if let jsonData = result.data(using: .utf8),
               let jsonObj = try? JSONSerialization.jsonObject(with: jsonData) as? [String: Any] {
                // comment 필드 우선, 없으면 advice 필드
                if let comment = jsonObj["comment"] as? String, !comment.isEmpty {
                    return comment
                }
                if let advice = jsonObj["advice"] as? String, !advice.isEmpty {
                    return advice
                }
            }
        }
        
        return result
    }
    
    func deleteDiary() {
        guard let id = diary.realId else { return }
        
        isDeleting = true
        
        LocalDataManager.shared.deleteDiary(id: id) { success in
            DispatchQueue.main.async {
                self.isDeleting = false
                if success {
                    onDelete()
                    presentationMode.wrappedValue.dismiss()
                } else {
                    self.errorMessage = "삭제할 데이터를 찾을 수 없습니다."
                    self.showErrorAlert = true
                }
            }
        }
    }
    
    // UTC 시간을 한국 시간으로 정확히 변환하여 표시
    // UTC 시간을 한국 시간으로 정확히 변환하여 표시
    func formatDate(_ dateStr: String) -> String {
        guard let validDate = parseDateString(dateStr) else { return dateStr }
        
        // 화면 표시용 Formatter (현재 기기 로컬 타임존 반영)
        let displayFormatter = DateFormatter()
        displayFormatter.timeZone = TimeZone.current
        displayFormatter.dateFormat = "yy년 MM월 dd일 / a h시 mm분"
        displayFormatter.amSymbol = "오전"
        displayFormatter.pmSymbol = "오후"
        
        return displayFormatter.string(from: validDate)
    }
    
    // 강력한 날짜 파싱 헬퍼 (마이크로세컨드 지원 포함)
    func parseDateString(_ dateStr: String) -> Date? {
        let isoFormatter = ISO8601DateFormatter()
        isoFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = isoFormatter.date(from: dateStr) { return date }
        
        isoFormatter.formatOptions = [.withInternetDateTime]
        if let date = isoFormatter.date(from: dateStr) { return date }
        
        let parser = DateFormatter()
        parser.calendar = Calendar(identifier: .gregorian)
        parser.timeZone = TimeZone(secondsFromGMT: 0) // UTC
        
        // Python default isoformat() often has 6 digits for microseconds (iOS default is 3)
        parser.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
        if let date = parser.date(from: dateStr) { return date }
        
        parser.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSS"
        if let date = parser.date(from: dateStr) { return date }
        
        parser.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
        if let date = parser.date(from: dateStr) { return date }
        
        parser.dateFormat = "yyyy-MM-dd HH:mm:ss"
        if let date = parser.date(from: dateStr) { return date }
        
        return nil
    }
    
    func getSleepContent() -> String? {
        // 우선순위: sleep_desc (구체적) > sleep_condition (레거시/간단)
        if let desc = diary.sleep_desc, !desc.isEmpty {
            return desc
        }
        return diary.sleep_condition
    }
    
    // AI 예측 문자열 파싱 헬퍼 (예: 'Happy (80%)' -> ("행복", "80%"))
    func parseAIPrediction(_ text: String?) -> (String, String) {
        guard var raw = text, !raw.isEmpty else { return ("", "") }
        
        // 1. 작은따옴표 제거
        if let start = raw.firstIndex(of: "'"), let end = raw.lastIndex(of: "'"), start != end {
            raw = String(raw[raw.index(after: start)..<end])
        }
        
        var label = ""
        var percent = ""
        
        // 2. 괄호 기준으로 분리
        if raw.hasSuffix(")"), let openParen = raw.lastIndex(of: "(") {
            label = String(raw[..<openParen]).trimmingCharacters(in: .whitespaces)
            percent = String(raw[openParen...])
        } else {
            label = raw // 괄호가 없는 경우 전체를 라벨로 취급
        }
        
        // 3. 한글 번역 매핑
        let emotionTranslation: [String: String] = [
            "Happy": "행복",
            "Sad": "슬픔",
            "Angry": "분노",
            "Fear": "두려움",
            "Surprise": "놀람",
            "Neutral": "평온",
            "Disgust": "혐오",
            "Anxiety": "불안",
            "Depression": "우울",
            "Stress": "스트레스",
            "Joy": "기쁨",
            "Love": "사랑",
            "Confusion": "혼란",
            "Excitement": "흥분",
            "Tired": "지침"
        ]
        
        let translatedLabel = emotionTranslation[label] ?? label // 번역 없으면 원문 사용
        
        if !percent.isEmpty && !percent.contains("%") {
             // 퍼센트 기호가 없으면 빈 문자열 처리 (안전장치)
             percent = ""
        }
        
        return (translatedLabel, percent)
    }
}