
import SwiftUI

struct AppDiaryDetailView: View {
    let diary: Diary
    var onDelete: () -> Void
    @Environment(\.presentationMode) var presentationMode
    @State private var isDeleting = false
    
    let baseURL = "https://217.142.253.35.nip.io"
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // 상단 날짜 및 삭제 버튼
                HStack {
                    Text(formatDate(diary.created_at ?? ""))
                        .font(.title2)
                        .fontWeight(.bold)
                    Spacer()
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
                
                // AI 분석 영역 (Fallback Logic 적용)
                // ai_analysis가 없으면 ai_prediction을 사용
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
                
                // ai_advice가 없으면 ai_comment를 사용
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
    
    func formatDate(_ dateStr: String) -> String {
        let iso = ISO8601DateFormatter()
        if let date = iso.date(from: dateStr) {
            let f = DateFormatter()
            f.dateFormat = "yyyy년 M월 d일"
            return f.string(from: date)
        }
        return dateStr
    }
    

}
