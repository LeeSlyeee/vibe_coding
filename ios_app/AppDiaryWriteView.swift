
import SwiftUI

struct AppDiaryWriteView: View {
    @Environment(\.presentationMode) var presentationMode
    @Binding var isPresented: Bool
    var date: Date
    var onSave: () -> Void
    
    // ✅ Base URL
    let baseURL = "https://217.142.253.35.nip.io"
    
    // Voice Recorder
    @StateObject private var voiceRecorder = VoiceRecorder()
    @State private var activeRecordingField: Int? = nil // 1: q1, 2: q2, 3: q3, 4: q4
    @State private var baseTextBeforeRecording: String = ""
    
    @State private var mood: Int = 3
    @State private var showForm = false
    @State private var insightMessage: String = ""
    @State private var isLoadingInsight = true
    
    // Form State
    @State private var q1: String = "" // Event
    @State private var q2: String = "" // Emotion
    @State private var q3: String = "" // Meaning
    @State private var q4: String = "" // Self talk
    @State private var qs: String = "" // Sleep
    @State private var isSaving = false
    
    // Weather State
    @State private var weatherDesc: String = "맑음"
    @State private var temp: Double = 20.0
    
    var body: some View {
        NavigationView {
            ZStack {
                // 기본 배경
                Color(UIColor.systemGroupedBackground).edgesIgnoringSafeArea(.all)
                
                if showForm {
                    // 일기 작성 폼 (디자인 개선 & 음성 녹음 추가)
                    VStack(spacing: 0) {
                        // 커스텀 헤더
                        HStack {
                            Button("취소") { isPresented = false }
                                .foregroundColor(.gray)
                            Spacer()
                            Text(dateString(date)).font(.headline)
                            Spacer()
                            Button(action: saveDiary) {
                                if isSaving { ProgressView() } else { Text("저장").fontWeight(.bold) }
                            }
                            .disabled(q1.isEmpty || q2.isEmpty || qs.isEmpty || isSaving)
                            .foregroundColor((q1.isEmpty || q2.isEmpty || qs.isEmpty) ? .gray : .blue)
                        }
                        .padding()
                        .background(Color.white)
                        .shadow(color: Color.black.opacity(0.05), radius: 5, x: 0, y: 5)
                        .zIndex(1)
                        
                        ScrollView {
                            VStack(spacing: 20) {
                                // 1. 기분 선택 (카드 스타일)
                                VStack(alignment: .leading, spacing: 10) {
                                    Text("오늘의 기분").font(.headline).foregroundColor(.gray)
                                    HStack(spacing: 5) {
                                        ForEach(1...5, id: \.self) { m in
                                            let asset = getMoodAsset(level: m)
                                            Button(action: { withAnimation { mood = m } }) {
                                                VStack(spacing: 8) {
                                                    Image(uiImage: UIImage(named: asset.image) ?? UIImage()) // Safety fallback
                                                        .resizable()
                                                        .scaledToFit()
                                                        .frame(width: 40, height: 40)
                                                    Text(asset.title)
                                                        .font(.system(size: 11, weight: .medium))
                                                        .foregroundColor(.primary)
                                                        .lineLimit(1)
                                                        .minimumScaleFactor(0.8)
                                                }
                                                .padding(.vertical, 10)
                                                .frame(maxWidth: .infinity)
                                                .background(mood == m ? asset.color.opacity(0.15) : Color.clear)
                                                .cornerRadius(12)
                                                .overlay(
                                                    RoundedRectangle(cornerRadius: 12)
                                                        .stroke(mood == m ? asset.color : Color.clear, lineWidth: 2)
                                                )
                                                .scaleEffect(mood == m ? 1.05 : 1.0)
                                                .opacity(mood == m ? 1.0 : 0.4)
                                                .animation(.spring(), value: mood)
                                            }
                                        }
                                    }
                                    .padding()
                                    .background(Color.white)
                                    .cornerRadius(16)
                                    .shadow(color: Color.black.opacity(0.03), radius: 5, x: 0, y: 2)
                                }
                                .padding(.top)
                                
                                // 질문 카드들
                                questionCard(
                                    title: "잠은 잘 주무셨나요?",
                                    binding: $qs,
                                    fieldId: 0
                                )
                                
                                questionCard(
                                    title: "오늘 무슨 일이 있었나요?",
                                    binding: $q1,
                                    fieldId: 1
                                )
                                
                                questionCard(
                                    title: "어떤 감정이 들었나요?",
                                    binding: $q2,
                                    fieldId: 2
                                )
                                
                                questionCard(
                                    title: "감정의 의미는 무엇인가요? (선택)",
                                    binding: $q3,
                                    fieldId: 3
                                )
                                
                                questionCard(
                                    title: "나에게 해주고 싶은 말 (선택)",
                                    binding: $q4,
                                    fieldId: 4
                                )
                                
                                Spacer(minLength: 50)
                            }
                            .padding()
                        }
                    }
                    .transition(.opacity)
                } else {
                    // Insight View (기존 유지)
                    VStack {
                        // 상단 날짜 및 닫기 버튼 영역
                        HStack {
                            Button(action: { isPresented = false }) {
                                Text("닫기").foregroundColor(.gray)
                            }
                            Spacer()
                            Text(dateString(date)).font(.headline).foregroundColor(.gray)
                            Spacer()
                            Button(action: {}) { Text("    ") }
                        }
                        .padding()
                        
                        // 날씨 정보
                        HStack {
                            Text("\(weatherDesc)")
                            Text(String(format: "%.1f°C", temp))
                        }
                        .font(.subheadline)
                        .foregroundColor(.blue)
                        .padding(.bottom, 20)

                        if isLoadingInsight {
                            // 로딩화면
                            VStack(spacing: 40) {
                                Spacer()
                                ZStack {
                                    Circle().fill(Color.purple.opacity(0.1)).frame(width: 120, height: 120)
                                    Image(systemName: "wand.and.stars").font(.system(size: 50)).foregroundColor(.purple)
                                }
                                VStack(spacing: 20) {
                                    Text("마음 가이드를 준비하고 있어요")
                                        .font(.title2).fontWeight(.bold).foregroundColor(.primary)
                                    Text("오늘의 날씨와 지난 감정 흐름을 연결하여\n당신만을 위한 특별한 조언을 만들고 있습니다.")
                                        .font(.body).multilineTextAlignment(.center).foregroundColor(.gray).lineSpacing(6)
                                    Text("잠시만 기다려주세요...").font(.subheadline).foregroundColor(.purple).padding(.top, 10)
                                }
                                ProgressView().progressViewStyle(CircularProgressViewStyle(tint: .purple)).scaleEffect(1.5)
                                Spacer()
                            }
                        } else {
                            // 인사이트 결과 화면
                            VStack(spacing: 30) {
                                Spacer()
                                Circle().fill(Color.purple.opacity(0.1)).frame(width: 80, height: 80)
                                    .overlay(Text("🧘‍♀️").font(.largeTitle))
                                Text("오늘의 마음 가이드").font(.title3).fontWeight(.bold).foregroundColor(.purple)
                                Text(insightMessage.isEmpty ? "오늘 하루도 수고 많으셨어요." : insightMessage)
                                    .font(.body).multilineTextAlignment(.center).padding()
                                    .frame(maxWidth: .infinity).background(Color.purple.opacity(0.05)).cornerRadius(15).padding(.horizontal)
                                Button(action: { withAnimation { showForm = true } }) {
                                    Text("오늘의 감정 기록하기").fontWeight(.bold).foregroundColor(.white).padding()
                                        .frame(maxWidth: .infinity).background(Color.black).cornerRadius(15)
                                }.padding(.horizontal, 40)
                                Spacer()
                            }
                        }
                    }
                    .background(Color.white)
                    .transition(.opacity)
                }
            }
            .navigationBarHidden(true)
        }
        .navigationViewStyle(StackNavigationViewStyle())
        .onAppear {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { fetchWeather() }
            DispatchQueue.main.asyncAfter(deadline: .now() + 300) {
                if isLoadingInsight {
                    isLoadingInsight = false
                    if insightMessage.isEmpty { insightMessage = "오늘 하루도 수고 많으셨어요." }
                }
            }
        }
        // 음성 인식 텍스트 반영
        .onChange(of: voiceRecorder.transcribedText) { newText in
            guard let field = activeRecordingField, !newText.isEmpty else { return }
            let combined = (baseTextBeforeRecording.isEmpty ? "" : baseTextBeforeRecording + " ") + newText
            
            switch field {
            case 0: qs = combined
            case 1: q1 = combined
            case 2: q2 = combined
            case 3: q3 = combined
            case 4: q4 = combined
            default: break
            }
        }
    }
    
    // MARK: - Components
    func questionCard(title: String, binding: Binding<String>, fieldId: Int) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(title)
                    .font(.headline)
                    .foregroundColor(Color(UIColor.darkGray))
                Spacer()
                
                // 마이크 버튼
                Button(action: { toggleRecording(for: fieldId, currentText: binding.wrappedValue) }) {
                    Image(systemName: (activeRecordingField == fieldId && voiceRecorder.isRecording) ? "stop.circle.fill" : "mic.circle.fill")
                        .font(.system(size: 30))
                        .foregroundColor((activeRecordingField == fieldId && voiceRecorder.isRecording) ? .red : .blue)
                        .scaleEffect((activeRecordingField == fieldId && voiceRecorder.isRecording) ? 1.2 : 1.0)
                        .animation(.easeInOut(duration: 0.2), value: voiceRecorder.isRecording)
                }
            }
            
            TextEditor(text: binding)
                .frame(height: 100)
                .padding(8)
                .background(Color(UIColor.secondarySystemBackground))
                .cornerRadius(12)
        }
        .padding()
        .background(Color.white)
        .cornerRadius(16)
        .shadow(color: Color.black.opacity(0.03), radius: 5, x: 0, y: 2)
    }
    
    // MARK: - Logic
    func toggleRecording(for fieldId: Int, currentText: String) {
        if activeRecordingField == fieldId && voiceRecorder.isRecording {
            // Stop
            voiceRecorder.stopRecording()
            activeRecordingField = nil
        } else {
            // Start
            // 다른 곳 녹음 중이면 중지
            if voiceRecorder.isRecording { voiceRecorder.stopRecording() }
            
            activeRecordingField = fieldId
            baseTextBeforeRecording = currentText
            voiceRecorder.startRecording()
        }
    }
    
    // (이하 기존 로직 동일)
    func fetchWeather() {
        guard let url = URL(string: "https://ipapi.co/json/") else {
            fetchInsight(); return
        }
        
        URLSession.shared.dataTask(with: url) { data, _, error in
            var lat = 37.5665
            var lon = 126.9780
            
            if error == nil, let data = data,
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let l = json["latitude"] as? Double,
               let g = json["longitude"] as? Double {
                lat = l; lon = g
            }
            
            let weatherUrlString = "https://api.open-meteo.com/v1/forecast?latitude=\(lat)&longitude=\(lon)&current_weather=true&timezone=auto"
            guard let wUrl = URL(string: weatherUrlString) else {
                DispatchQueue.main.async { self.fetchInsight() }
                return
            }
            
            URLSession.shared.dataTask(with: wUrl) { wData, _, _ in
                if let wData = wData,
                   let wJson = try? JSONSerialization.jsonObject(with: wData) as? [String: Any],
                   let current = wJson["current_weather"] as? [String: Any] {
                    
                    let code = current["weathercode"] as? Int ?? 0
                    let temperature = current["temperature"] as? Double ?? 20.0
                    let map: [Int: String] = [
                        0: "맑음 ☀️", 1: "대체로 맑음 🌤️", 2: "구름 조금 ⛅", 3: "흐림 ☁️",
                        45: "안개 🌫️", 48: "안개 🌫️", 51: "이슬비 🌧️", 53: "이슬비 🌧️", 55: "이슬비 🌧️",
                        61: "비 ☔", 63: "비 ☔", 65: "비 ☔", 80: "소나기 ☔", 95: "뇌우 ⚡"
                    ]
                    
                    DispatchQueue.main.async {
                        self.weatherDesc = map[code] ?? "흐림"
                        self.temp = temperature
                        self.fetchInsight()
                    }
                } else {
                    DispatchQueue.main.async { self.fetchInsight() }
                }
            }.resume()
        }.resume()
    }

    func fetchInsight() {
        guard let token = UserDefaults.standard.string(forKey: "authToken") else { 
            isLoadingInsight = false
            insightMessage = "로그인이 필요합니다."
            return 
        }
        
        let encodedWeather = weatherDesc.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "맑음"
        let dateStr = dateString(date)
        guard let url = URL(string: "\(baseURL)/api/insight?date=\(dateStr)&weather=\(encodedWeather)") else { return }
        
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        let task = URLSession.shared.dataTask(with: request) { data, _, error in
            DispatchQueue.main.async {
                isLoadingInsight = false
                if let error = error {
                    print("Insight Error: \(error)")
                    if insightMessage.isEmpty {
                        insightMessage = "오늘 하루도 수고 많으셨어요. 편안한 마음으로 기록해보세요."
                    }
                    return
                }
                
                guard let data = data else { return }
                do {
                    if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let msg = json["message"] as? String, !msg.isEmpty {
                        insightMessage = msg
                    } else {
                        insightMessage = "오늘 하루도 수고 많으셨어요. 편안한 마음으로 기록해보세요."
                    }
                } catch {
                     insightMessage = "오늘 하루도 수고 많으셨어요. 편안한 마음으로 기록해보세요."
                }
            }
        }
        task.resume()
    }
    
    func saveDiary() {
        guard let token = UserDefaults.standard.string(forKey: "authToken") else { return }
        guard let url = URL(string: "\(baseURL)/api/diaries") else { return }
        
        isSaving = true
        
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
            "sleep_desc": qs,
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
            
            DispatchQueue.main.async {
                onSave()
                isPresented = false
            }
        }.resume()
    }
    
    func dateString(_ d: Date) -> String {
        let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"; return f.string(from: d)
    }
    
    func moodEmoji(_ l: Int) -> String {
        ["", "😠", "😢", "😐", "😌", "😊"][min(l, 5)]
    }
}
