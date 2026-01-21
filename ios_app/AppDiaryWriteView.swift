
import SwiftUI

struct AppDiaryWriteView: View {
    @Environment(\.presentationMode) var presentationMode
    @Binding var isPresented: Bool
    var date: Date
    var onSave: () -> Void
    
    // ✅ Base URL
    let baseURL = "https://217.142.253.35.nip.io"
    
    @State private var mood: Int = 3
    @State private var showForm = false
    @State private var insightMessage: String = ""
    @State private var isLoadingInsight = true
    
    // Form State
    @State private var q1: String = ""
    @State private var q2: String = ""
    @State private var q3: String = ""
    @State private var q4: String = ""
    @State private var isSaving = false
    
    // Weather State
    @State private var weatherDesc: String = "맑음"
    @State private var temp: Double = 20.0
    
    var body: some View {
        NavigationView {
            ZStack {
                // 기본 배경
                Color.white.edgesIgnoringSafeArea(.all)
                
                if showForm {
                    // 일기 작성 폼
                    Form {
                        Section(header: Text("오늘의 기분")) {
                            Picker("기분", selection: $mood) {
                                Text("😠").tag(1)
                                Text("😢").tag(2)
                                Text("😐").tag(3)
                                Text("😌").tag(4)
                                Text("😊").tag(5)
                            }
                            .pickerStyle(SegmentedPickerStyle())
                            .padding(.vertical)
                        }
                        Section(header: Text("질문 1: 오늘 무슨일이 있었나요?")) {
                            TextEditor(text: $q1).frame(height: 100)
                        }
                        Section(header: Text("질문 2: 어떤 감정이 들었나요?")) {
                            TextEditor(text: $q2).frame(height: 100)
                        }
                        Section(header: Text("질문 3: 감정의 의미 (선택)")) {
                            TextEditor(text: $q3).frame(height: 80)
                        }
                        Section(header: Text("질문 4: 나에게 보내는 위로 (선택)")) {
                            TextEditor(text: $q4).frame(height: 80)
                        }
                    }
                    .transition(.opacity) // 부드러운 전환
                } else {
                    // 가이드 및 로딩 화면 (전체 화면 덮기)
                    VStack {
                        // 상단 날짜 및 닫기 버튼 영역 (커스텀 헤더)
                        HStack {
                            Button(action: { isPresented = false }) {
                                Text("닫기").foregroundColor(.gray)
                            }
                            Spacer()
                            Text(dateString(date)).font(.headline).foregroundColor(.gray)
                            Spacer()
                            Button(action: {}) { Text("    ") } // 균형 맞추기용 더미
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
                            // 로딩 안내 화면
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
                    .background(Color.white) // 배경 확실하게 지정
                    .transition(.opacity)
                }
            }
            .navigationBarHidden(true) // 네비게이션 바 숨기고 커스텀 헤더 사용
        }
        .navigationViewStyle(StackNavigationViewStyle()) // 렌더링 오류 방지
        .onAppear {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { fetchWeather() }
            DispatchQueue.main.asyncAfter(deadline: .now() + 300) {
                if isLoadingInsight {
                    isLoadingInsight = false
                    if insightMessage.isEmpty { insightMessage = "오늘 하루도 수고 많으셨어요." }
                }
            }
        }
    }
    
    // MARK: - Logic
    func fetchWeather() {
        guard let url = URL(string: "https://ipapi.co/json/") else {
            fetchInsight(); return
        }
        
        URLSession.shared.dataTask(with: url) { data, _, error in
            var lat = 37.5665
            var lon = 126.9780
            
            // IP 조회 성공 시 좌표 업데이트
            if error == nil, let data = data,
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let l = json["latitude"] as? Double,
               let g = json["longitude"] as? Double {
                lat = l; lon = g
            }
            
            // 좌표 기반 날씨 조회
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
                     // Code mapping
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
        
        // 날씨 정보가 URL 인코딩 되도록 처리
        let encodedWeather = weatherDesc.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "맑음"
        let dateStr = dateString(date)
        guard let url = URL(string: "\(baseURL)/api/insight?date=\(dateStr)&weather=\(encodedWeather)") else { return }
        
        var request = URLRequest(url: url)
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        // Timeout handling (similar to web)
        let task = URLSession.shared.dataTask(with: request) { data, _, error in
            DispatchQueue.main.async {
                isLoadingInsight = false
                if let error = error {
                    print("Insight Error: \(error)")
                    // 만약 에러가 나더라도 기본 메시지는 설정 안함 (이미 위에서 초기화 된 상태거나 빈 상태)
                    // 타임아웃 블록이나 아래 로직에서 처리
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
                         // API가 200 OK지만 빈 메시지를 줄 경우
                        insightMessage = "오늘 하루도 수고 많으셨어요. 편안한 마음으로 기록해보세요."
                    }
                } catch {
                     insightMessage = "오늘 하루도 수고 많으셨어요. 편안한 마음으로 기록해보세요."
                }
            }
        }
        task.resume()
        
        // Timeout safety
        DispatchQueue.main.asyncAfter(deadline: .now() + 300) {
            if isLoadingInsight {
                isLoadingInsight = false
                if insightMessage.isEmpty {
                    insightMessage = "오늘 하루도 수고 많으셨어요. 편안한 마음으로 기록해보세요."
                }
            }
        }
    }
    
    func saveDiary() {
        guard let token = UserDefaults.standard.string(forKey: "authToken") else { return }
        guard let url = URL(string: "\(baseURL)/api/diaries") else { return }
        
        isSaving = true
        
        // Date format: YYYY-MM-DD
        // let dateStr = dateString(date) // We might need full datetime or just date
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
