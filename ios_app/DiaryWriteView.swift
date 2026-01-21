
import SwiftUI

struct DiaryWriteView: View {
    @Environment(\.presentationMode) var presentationMode
    @Binding var isPresented: Bool
    var date: Date
    var onSave: () -> Void
    
    // ✅ Base URL
    let baseURL = "https://217.142.253.35.nip.io"
    
    @State private var mood: Int = 3
    @State private var q1: String = ""
    @State private var q2: String = ""
    @State private var q3: String = ""
    @State private var q4: String = "" // Self talk
    @State private var isSaving = false
    @State private var weatherDesc: String = "맑음" // Default or fetch
    @State private var temp: Double = 20.0
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("오늘의 기분")) {
                    Picker("기분", selection: $mood) {
                        Text("😠 화남").tag(1)
                        Text("😢 우울").tag(2)
                        Text("😐 보통").tag(3)
                        Text("😌 편안").tag(4)
                        Text("😊 행복").tag(5)
                    }
                    .pickerStyle(SegmentedPickerStyle())
                    .padding(.vertical)
                }
                
                Section(header: Text("질문 1: 오늘 무슨일이 있었나요?")) {
                    TextEditor(text: $q1)
                        .frame(height: 100)
                }
                
                Section(header: Text("질문 2: 어떤 감정이 들었나요?")) {
                    TextEditor(text: $q2)
                        .frame(height: 100)
                }
                
                Section(header: Text("질문 3: 감정의 의미 (선택)")) {
                    TextEditor(text: $q3)
                        .frame(height: 80)
                }
                
                Section(header: Text("질문 4: 나에게 보내는 위로 (선택)")) {
                    TextEditor(text: $q4)
                        .frame(height: 80)
                }
            }
            .navigationTitle(dateString(date))
            .navigationBarItems(
                leading: Button("취소") { isPresented = false },
                trailing: Button(action: saveDiary) {
                    if isSaving { ProgressView() } else { Text("저장") }
                }
                .disabled(q1.isEmpty || q2.isEmpty || isSaving)
            )
        }
    }
    
    func saveDiary() {
        guard let token = UserDefaults.standard.string(forKey: "authToken") else { return }
        guard let url = URL(string: "\(baseURL)/api/diaries") else { return }
        
        isSaving = true
        
        // Date format: YYYY-MM-DD
        let dateStr = dateString(date) // We might need full datetime or just date
        // Backend expects 'created_at' in ISO format or it defaults, but for calendar consistency we should pass the date.
        // Actually backend logic uses `created_at` from payload.
        // Let's create a combined datetime string with current time.
        
        // Combine date with current time
        let now = Date()
        let calendar = Calendar.current
        var components = calendar.dateComponents([.hour, .minute, .second], from: now)
        components.year = calendar.component(.year, from: date)
        components.month = calendar.component(.month, from: date)
        components.day = calendar.component(.day, from: date)
        let finalDate = calendar.date(from: components) ?? date
        
        let isoDate = ISO8601DateFormatter().string(from: finalDate)
        
        let body: [String: Any] = [
            "created_at": isoDate,
            "mood_level": mood,
            "event": q1,
            "emotion_desc": q2,
            "emotion_meaning": q3,
            "self_talk": q4,
            "weather": weatherDesc,
            "temperature": temp
        ]
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        URLSession.shared.dataTask(with: request) { data, _, error in
            DispatchQueue.main.async { isSaving = false }
            
            if let error = error {
                print("Save Error: \(error)")
                return
            }
            
            // Success
            DispatchQueue.main.async {
                onSave()
                isPresented = false
            }
        }.resume()
    }
    
    func dateString(_ d: Date) -> String {
        let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"; return f.string(from: d)
    }
}
