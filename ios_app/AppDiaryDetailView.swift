import SwiftUI

struct AppDiaryDetailView: View {
    let diary: Diary
    var onDelete: () -> Void
    var onEdit: (() -> Void)? = nil 
    
    @Environment(\.presentationMode) var presentationMode
    @State private var isDeleting = false
    @State private var showingEditSheet = false
    
    let baseURL = "https://217.142.253.35.nip.io"
    
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
                if let ai = (diary.ai_analysis?.isEmpty == false ? diary.ai_analysis : diary.ai_prediction), !ai.isEmpty {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("🤖 AI 심리 분석")
                            .font(.headline)
                            .foregroundColor(.blue)
                        Text(ai)
                            .padding()
                            .background(Color.blue.opacity(0.1))
                            .cornerRadius(10)
                    }
                    .padding(.top)
                }
                
                // AI 조언 영역
                if let advice = (diary.ai_advice?.isEmpty == false ? diary.ai_advice : diary.ai_comment), !advice.isEmpty {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("💡 AI 조언")
                            .font(.headline)
                            .foregroundColor(.green)
                        Text(advice)
                            .padding()
                            .background(Color.green.opacity(0.1))
                            .cornerRadius(10)
                    }
                    .padding(.top)
                }
                
                Spacer()
            }
            .padding()
        }
        .navigationBarTitleDisplayMode(.inline)
        .preferredColorScheme(.light)
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
    }
    
    func label(_ text: String) -> some View {
        Text(text)
            .font(.headline)
            .foregroundColor(.gray)
    }
    
    func deleteDiary() {
        guard let id = diary.realId else { return }
        guard let token = UserDefaults.standard.string(forKey: "authToken") else { return }
        guard let url = URL(string: "\(baseURL)/api/diaries/\(id)") else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        isDeleting = true
        URLSession.shared.dataTask(with: request) { _, _, _ in
            DispatchQueue.main.async {
                isDeleting = false
                onDelete()
                presentationMode.wrappedValue.dismiss()
            }
        }.resume()
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
}