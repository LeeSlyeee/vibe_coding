import SwiftUI

struct AppDiaryWriteView: View {
    @Environment(\.presentationMode) var presentationMode
    @Binding var isPresented: Bool
    var date: Date
    var onSave: () -> Void
    
    // 수정할 일기 데이터 (nil이면 새 글 작성)
    var diaryToEdit: Diary? = nil
    
    // ✅ Base URL (Managed by APIService)
    // let baseURL = "https://217.142.253.35.nip.io/api"
    
    // Voice Recorder
    @StateObject private var voiceRecorder = VoiceRecorder()
    @State private var activeRecordingField: Int? = nil 
    // Field IDs: 
    // 0: qs (수면), 1: q1 (사건), 2: q2 (감정), 3: q3 (의미), 4: q4 (독백)
    @State private var baseTextBeforeRecording: String = ""
    
    @State private var mood: Int = 3
    @State private var showForm = false
    @State private var insightMessage: String = ""
    @State private var isLoadingInsight = true
    
    // Form State
    @State private var q1: String = "" // Event (무슨 일)
    @State private var q2: String = "" // Emotion (어떤 감정)
    @State private var q3: String = "" // Meaning (감정 의미)
    @State private var q4: String = "" // Self talk (나에게 말)
    @State private var qs: String = "" // Sleep (잠)
    @State private var isSaving = false
    @State private var showError = false
    @State private var errorMessage = ""
    
    // [Crisis Detection] 위기감지 SOS 팝업
    @State private var showCrisisSOSModal = false
    
    // Weather & Medication State
    @State private var weatherDesc: String = "맑음"
    @State private var temp: Double = 20.0
    @State private var isMedicationTaken: Bool = false // (Legacy & Fallback)
    @State private var takenMeds: Set<String> = [] // [New] 개별 약물 체크 상태
    @State private var showingMedSetting = false
    @State private var savedMeds: [String] = []
    
    // [Crash Recovery]
    @State private var recoveredDiary: Diary? = nil
    
    var body: some View {
        NavigationView {
            ZStack {
                Color.gray.opacity(0.1).edgesIgnoringSafeArea(.all)
                
                if showForm {
                    // 일기 작성 폼
                    VStack(spacing: 0) {
                        // 커스텀 헤더
                        HStack {
                            Button("취소") { isPresented = false }
                                .foregroundColor(.gray)
                            Spacer()
                            Text(diaryToEdit != nil ? "일기 수정" : dateStringLocal(date)).font(.headline)
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
                                                    Image(asset.image)
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
                                
                                // [New] 1.5 약물 복용 & 날씨
                                HStack(alignment: .top, spacing: 15) {
                                    // 약물 체크 (동적 리스트)
                                    VStack(alignment: .leading, spacing: 10) {
                                        HStack {
                                            Text("약물 복용")
                                                .fontWeight(.semibold)
                                                .foregroundColor(.primary)
                                            Spacer()
                                            Button(action: { showingMedSetting = true }) {
                                                Image(systemName: "gearshape.fill")
                                                    .foregroundColor(.gray)
                                            }
                                        }
                                        
                                        if savedMeds.isEmpty {
                                            // 등록된 약이 없을 때: 단순 토글
                                            Button(action: { isMedicationTaken.toggle() }) {
                                                HStack {
                                                    Image(systemName: isMedicationTaken ? "checkmark.square.fill" : "square")
                                                        .foregroundColor(isMedicationTaken ? .green : .gray)
                                                    Text("복용 완료")
                                                        .font(.subheadline)
                                                        .foregroundColor(.primary)
                                                }
                                            }
                                        } else {
                                            // 등록된 약이 있을 때: 개별 체크
                                            ForEach(savedMeds, id: \.self) { med in
                                                Button(action: {
                                                    if takenMeds.contains(med) {
                                                        takenMeds.remove(med)
                                                    } else {
                                                        takenMeds.insert(med)
                                                    }
                                                }) {
                                                    HStack {
                                                        Image(systemName: takenMeds.contains(med) ? "checkmark.square.fill" : "square")
                                                            .foregroundColor(takenMeds.contains(med) ? .green : .gray)
                                                        Text(med)
                                                            .font(.subheadline)
                                                            .foregroundColor(.primary)
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    .padding()
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .background(Color.white)
                                    .cornerRadius(16)
                                    .shadow(color: Color.black.opacity(0.03), radius: 5, x: 0, y: 2)
                                    
                                    // 날씨 확인/수정
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text("오늘의 날씨")
                                            .font(.caption)
                                            .foregroundColor(.gray)
                                        HStack {
                                            TextField("날씨", text: $weatherDesc)
                                                .font(.headline)
                                            Spacer()
                                            Text(String(format: "%.0f°", temp))
                                                .font(.subheadline)
                                                .foregroundColor(.secondary)
                                        }
                                    }
                                    .padding()
                                    .frame(width: 140) // 날씨 영역 고정 너비
                                    .background(Color.white)
                                    .cornerRadius(16)
                                    .shadow(color: Color.black.opacity(0.03), radius: 5, x: 0, y: 2)
                                }
                                
                                // 질문 카드들
                                questionCard(
                                    title: "잠은 잘 주무셨나요?",
                                    binding: $qs, 
                                    fieldId: 0
                                )
                                questionCard(title: "오늘 무슨 일이 있었나요?", binding: $q1, fieldId: 1)
                                questionCard(title: "어떤 감정이 들었나요?", binding: $q2, fieldId: 2)
                                questionCard(title: "감정의 의미는 무엇인가요? (선택)", binding: $q3, fieldId: 3)
                                questionCard(title: "나에게 해주고 싶은 말 (선택)", binding: $q4, fieldId: 4)
                                
                                Spacer(minLength: 50)
                            }
                            .padding()
                        }
                        #if os(iOS)
                        .scrollDismissesKeyboard(.interactively)
                        #endif
                    }
                    .transition(.opacity)
                } else {
                    // Insight View (작성 모드일 때만) -- 기존 유지
                    VStack {
                        // ...
                        HStack {
                            Button(action: { isPresented = false }) {
                                Text("닫기").foregroundColor(.gray)
                            }
                            Spacer()
                            Text(dateStringLocal(date)).font(.headline).foregroundColor(.gray)
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
                        
                        // (생략: 기존 Insight 로직 유지)
                        if isLoadingInsight {
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
                            VStack(spacing: 30) {
                                Spacer()
                                Circle().fill(Color.purple.opacity(0.1)).frame(width: 80, height: 80)
                                    .overlay(Image(systemName: "figure.mind.and.body").font(.largeTitle).foregroundColor(.blue))
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
            #if os(iOS)
            .dismissKeyboardOnTap() // [Cursor Fix] UIKit 기반 키보드 닫기 (TextField 포커스 방해 없음)
            .navigationBarHidden(true)
            #endif
            .alert(isPresented: $showError) {
                Alert(title: Text("저장 실패"), message: Text(errorMessage), dismissButton: .default(Text("확인")))
            }
        }
        #if os(iOS)
        .navigationViewStyle(StackNavigationViewStyle())
        #endif
                .onAppear {
            if let edit = diaryToEdit {
                // [강제 업데이트] 약간의 딜레이를 주어 State 반영 보장
                DispatchQueue.main.async {
                    self.q1 = edit.event ?? ""
                    self.q2 = edit.emotion_desc ?? ""
                    self.q3 = edit.emotion_meaning ?? ""
                    self.q4 = edit.self_talk ?? ""
                    
                    if let sleep = edit.sleep_desc ?? edit.sleep_condition {
                        self.qs = sleep
                    } else {
                        self.qs = ""
                    }
                    
                    self.mood = edit.mood_level
                    self.weatherDesc = edit.weather ?? "맑음"
                    self.temp = edit.temperature ?? 20.0
                    
                    // [New] 약물 데이터 로드
                    if let desc = edit.medication_desc, !desc.isEmpty {
                        self.takenMeds = Set(desc.components(separatedBy: ", "))
                    } else {
                        self.isMedicationTaken = edit.medication ?? false
                    }
                    
                    self.showForm = true
                    self.isLoadingInsight = false
                }
            } else {
                // 새 글 작성
                // [Crash Recovery] 미저장 데이터 복구
                if let data = UserDefaults.standard.data(forKey: "diary_crash_snapshot"),
                   let snapshot = try? JSONDecoder().decode(Diary.self, from: data) {
                    
                    DispatchQueue.main.async {
                        self.q1 = snapshot.event ?? ""
                        self.q2 = snapshot.emotion_desc ?? ""
                        self.q3 = snapshot.emotion_meaning ?? ""
                        self.q4 = snapshot.self_talk ?? ""
                        
                        if let sleep = snapshot.sleep_desc ?? snapshot.sleep_condition {
                             self.qs = sleep
                        }
                        
                        self.mood = snapshot.mood_level
                        self.weatherDesc = snapshot.weather ?? "맑음"
                        // 약물 복구
                        if let desc = snapshot.medication_desc {
                            self.takenMeds = Set(desc.components(separatedBy: ", "))
                        } else {
                            self.isMedicationTaken = snapshot.medication ?? false
                        }
                        
                        // [Fix] 기존 다이어리의 ID, _id, date 등을 보존하기 위해 snapshot 저장
                        self.recoveredDiary = snapshot
                        
                        // 복구 알림을 위해 폼 즉시 노출
                        self.showForm = true
                        self.isLoadingInsight = false
                    }
                }
                
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { 
                    // 복구된 날씨가 없으면 새로 가져오기
                    if self.weatherDesc == "맑음" { self.fetchWeather() }
                }
                
                DispatchQueue.main.asyncAfter(deadline: .now() + 300) {
                    if isLoadingInsight {
                        isLoadingInsight = false
                        if insightMessage.isEmpty { insightMessage = "오늘 하루도 수고 많으셨어요." }
                    }
                }
            }
            loadMedications() // 약물 목록 로드
        }
        // [New] 약물 설정 시트
        .sheet(isPresented: $showingMedSetting, onDismiss: loadMedications) {
            MedicationSettingView()
        }
        // [Crisis Detection] 일기 작성 중 위기 감지 시 SOS 팝업
        .sheet(isPresented: $showCrisisSOSModal) {
            SOSView()
        }
        // 음성 인식 텍스트 반영
        .onChangeCompat(of: voiceRecorder.transcribedText) { newText in
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
    
    // Components (질문 카드)
    func questionCard(title: String, binding: Binding<String>, fieldId: Int) -> some View {
        QuestionCardView(
            title: title,
            text: binding,
            fieldId: fieldId,
            activeRecordingField: $activeRecordingField,
            voiceRecorder: voiceRecorder,
            onToggleRecording: { fid, currentText in
                toggleRecording(for: fid, currentText: currentText)
            }
        )
    }
    
    // Logic: 녹음 토글
    func toggleRecording(for fieldId: Int, currentText: String) {
        if activeRecordingField == fieldId && voiceRecorder.isRecording {
            voiceRecorder.stopRecording()
            activeRecordingField = nil
        } else {
            if voiceRecorder.isRecording { voiceRecorder.stopRecording() }
            activeRecordingField = fieldId
            baseTextBeforeRecording = currentText
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                if self.activeRecordingField == fieldId { self.voiceRecorder.startRecording() }
            }
        }
    }
    
    // Logic: 날씨 API
    func fetchWeather() {
        guard let url = URL(string: "https://ipapi.co/json/") else { fetchInsight(); return }
        
        URLSession.shared.dataTask(with: url) { data, _, error in
            var lat = 37.5665; var lon = 126.9780
            if error == nil, let data = data, let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let l = json["latitude"] as? Double, let g = json["longitude"] as? Double {
                lat = l; lon = g
            }
            
            let weatherUrlString = "https://api.open-meteo.com/v1/forecast?latitude=\(lat)&longitude=\(lon)&current_weather=true&timezone=auto"
            guard let wUrl = URL(string: weatherUrlString) else { DispatchQueue.main.async { self.fetchInsight() }; return }
            
            URLSession.shared.dataTask(with: wUrl) { wData, _, _ in
                if let wData = wData, let wJson = try? JSONSerialization.jsonObject(with: wData) as? [String: Any],
                   let current = wJson["current_weather"] as? [String: Any] {
                    let code = current["weathercode"] as? Int ?? 0
                    let temp = current["temperature"] as? Double ?? 20.0
                    let map: [Int: String] = [0: "맑음", 1: "대체로 맑음", 2: "구름 조금", 3: "흐림", 4: "안개", 45: "안개", 48: "안개", 51: "이슬비", 53: "이슬비", 55: "이슬비", 61: "비", 63: "비", 65: "비", 80: "소나기", 95: "뇌우"]
                    DispatchQueue.main.async {
                        self.weatherDesc = map[code] ?? "흐림 ☁️"
                        self.temp = temp
                        self.fetchInsight()
                    }
                } else { DispatchQueue.main.async { self.fetchInsight() } }
            }.resume()
        }.resume()
    }

    func fetchInsight() {
        // [OOM Prevention] Disable Auto-Inference on View Load
        // Writing Screen should be lightweight. Inference happens only AFTER save.
        
        isLoadingInsight = false
        
        let quotes = [
            "오늘 하루도 수고 많으셨어요.",
            "당신의 감정은 소중합니다.",
            "천천히, 편안하게 기록해보세요.",
            "오늘의 날씨처럼 마음도 변할 수 있어요."
        ]
        insightMessage = quotes.randomElement() ?? "오늘 하루도 수고 많으셨어요."
        
        /* [Legacy: Auto LLM Call causing OOM]
        Task {
            let message = await LLMService.shared.generateMindGuide(
                recentDiaries: context, 
                weather: weatherDesc, 
                weatherStats: nil
            )
            
            await MainActor.run {
                self.isLoadingInsight = false
                self.insightMessage = message
            }
        }
        */
    }
    
    // Logic: 저장 (Local + LLM)
    func saveDiary() {
        // [Crisis Detection] 저장 전 위기 키워드 검사
        let allText = [q1, q2, q3, q4, qs].joined(separator: " ")
        let crisisLevel3 = ["죽고", "자살", "뛰어내", "목을", "손목", "유서", "마지막", "끝내고", "자해", "목숨"]
        let crisisLevel2 = ["사라지고", "없어지고", "살기 싫", "의미 없", "끝내", "망했", "수면제", "칼", "약 먹", "다 끝"]
        
        let hasLevel3 = crisisLevel3.contains(where: { allText.contains($0) })
        let hasLevel2 = crisisLevel2.contains(where: { allText.contains($0) })
        
        if hasLevel3 || hasLevel2 {
            showCrisisSOSModal = true
            return // 저장하지 않고 즉시 반환
        }
        
        isSaving = true
        
        // [New] 약물 데이터 병합
        var finalMedDesc: String? = nil
        var finalMedication: Bool = false
        
        if !savedMeds.isEmpty {
            if !takenMeds.isEmpty {
                finalMedDesc = takenMeds.joined(separator: ", ")
                finalMedication = true
            }
        } else {
            // 목록이 없으면 기존 토글 사용
            finalMedication = isMedicationTaken
        }

        var newDiary: Diary
        if let existing = diaryToEdit ?? recoveredDiary {
            newDiary = existing
        } else {
            newDiary = Diary(
                id: UUID().uuidString,
                _id: nil,
                date: dateStringLocal(date),
                mood_level: mood,
                event: q1,
                emotion_desc: q2,
                emotion_meaning: q3,
                self_talk: q4,
                sleep_desc: qs,
                weather: weatherDesc,
                temperature: temp,
                created_at: nil,
                medication: finalMedication,
                medication_desc: finalMedDesc // [New]
            )
        }
        
        // Update fields
        newDiary.mood_level = mood
        newDiary.event = q1
        newDiary.sleep_desc = qs
        newDiary.emotion_desc = q2
        newDiary.emotion_meaning = q3
        newDiary.self_talk = q4
        newDiary.weather = weatherDesc
        newDiary.medication = finalMedication
        newDiary.medication_desc = finalMedDesc // [New]
        
        // [Crash Prevention] Safety Snapshot (저장 전 백업)
        if let encoded = try? JSONEncoder().encode(newDiary) {
            UserDefaults.standard.set(encoded, forKey: "diary_crash_snapshot")
        }
        
        // [UX] 재분석 중임을 표시 (캘린더 즉시 반영)
        // AI 큐에서 분석이 완료되면 실제 결과로 덮어씌워짐
        newDiary.ai_prediction = "재분석 중..."
        
        // 1. First Save (Synchronous-like)
        LocalDataManager.shared.saveDiary(newDiary) { success in
            if success {
                // [Safety] 성공 시 스냅샷 제거
                UserDefaults.standard.removeObject(forKey: "diary_crash_snapshot")
                
                // [UX Fix] 저장 즉시 화면 닫기 (AI 분석 완료를 기다리지 않음)
                // AI 분석은 백그라운드에서 진행되며, 완료 시 자동으로 일기에 반영됨
                DispatchQueue.main.async {
                    // [B2G] 저장 즉시 센터로 데이터 동기화
                    if B2GManager.shared.isLinked {
                        B2GManager.shared.syncData()
                    }
                    
                    self.isSaving = false
                    self.onSave()
                    self.isPresented = false
                }
                
                // [OOM Prevention] UI Dismiss 후 메모리가 안정화될 때까지 1초 지연 후 AI 분석 시작
                DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                    let accepted = LLMService.shared.tryEnqueueDiaryAnalysis(newDiary)
                    if accepted {
                    } else {
                        // AI 분석이 거절되어도 일기는 이미 저장됨
                        // "재분석 중..." 상태를 해제하여 캘린더에서 정상 표시
                        if let index = LocalDataManager.shared.diaries.firstIndex(where: { $0.id == newDiary.id }) {
                            LocalDataManager.shared.diaries[index].ai_prediction = nil
                            LocalDataManager.shared.diaries[index].ai_analysis = nil
                        }
                    }
                }
            } else {
                DispatchQueue.main.async {
                    self.isSaving = false
                    self.errorMessage = "로컬 저장 실패"
                    self.showError = true
                    // 실패 시 스냅샷 유지 (재시도 가능하게)
                }
            }
        }
    }
    

    
    func dateStringLocal(_ d: Date) -> String {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        // 로컬 타임존 기준 문자열 반환
        f.timeZone = TimeZone.current 
        return f.string(from: d)
    }
    
    func moodEmoji(_ l: Int) -> String {
        ["", "매우나쁨", "나쁨", "보통", "좋음", "매우좋음"][min(l, 5)]
    }
    
    // [New] 약물 목록 로드
    func loadMedications() {
        if let saved = UserDefaults.standard.array(forKey: "savedMedications") as? [String] {
            savedMeds = saved
        }
    }
}

// MARK: - Medication Setting View
struct MedicationSettingView: View {
    @Environment(\.presentationMode) var presentationMode
    @State private var medications: [String] = []
    @State private var newMedName: String = ""
    
    // UserDefaults Key
    private let key = "savedMedications"
    
    var body: some View {
        NavigationView {
            VStack {
                // 입력창
                HStack {
                    TextField("약 이름 (예: 비타민, 혈압약)", text: $newMedName)
                        .padding()
                        .background(Color.gray.opacity(0.1))
                        .cornerRadius(10)
                    
                    Button(action: addMedication) {
                        Image(systemName: "plus")
                            .font(.title2)
                            .foregroundColor(.white)
                            .padding()
                            .background(newMedName.isEmpty ? Color.gray : Color.blue)
                            .cornerRadius(10)
                    }
                    .disabled(newMedName.isEmpty)
                }
                .padding()
                
                // 목록
                List {
                    ForEach(medications, id: \.self) { med in
                        HStack {
                            Image(systemName: "pills")
                                .foregroundColor(.green)
                            Text(med)
                                .font(.body)
                        }
                    }
                    .onDelete(perform: deleteMedication)
                }
                .listStyle(InsetGroupedListStyle())
                
                Spacer()
                
                Text("등록된 약들은 일기 작성 시\n확인할 수 있습니다.")
                    .font(.caption)
                    .foregroundColor(.gray)
                    .multilineTextAlignment(.center)
                    .padding()
            }
            .navigationTitle("나의 약물 관리")
            .navigationBarItems(trailing: Button("닫기") {
                presentationMode.wrappedValue.dismiss()
            })
            .onAppear(perform: loadMedications)
        }
    }
    
    func loadMedications() {
        if let saved = UserDefaults.standard.array(forKey: key) as? [String] {
            medications = saved
        }
    }
    
    func addMedication() {
        guard !newMedName.isEmpty else { return }
        // 중복 방지
        if !medications.contains(newMedName) {
            medications.append(newMedName)
            saveMedications()
        }
        newMedName = ""
    }
    
    func deleteMedication(at offsets: IndexSet) {
        medications.remove(atOffsets: offsets)
        saveMedications()
    }
    
    func saveMedications() {
        UserDefaults.standard.set(medications, forKey: key)
    }
}

// MARK: - QuestionCardView (포커스 상태 시각 피드백)
struct QuestionCardView: View {
    let title: String
    @Binding var text: String
    let fieldId: Int
    @Binding var activeRecordingField: Int?
    @ObservedObject var voiceRecorder: VoiceRecorder
    var onToggleRecording: (Int, String) -> Void
    
    @FocusState private var isFocused: Bool
    
    private let placeholders: [Int: String] = [
        0: "수면 상태를 적어보세요...",
        1: "오늘 있었던 일을 적어보세요...",
        2: "느낀 감정을 표현해보세요...",
        3: "그 감정이 나에게 어떤 의미인지...",
        4: "스스로에게 해주고 싶은 말..."
    ]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(title).font(.headline).foregroundColor(Color.secondary)
                Spacer()
                // 마이크 버튼
                Button(action: { onToggleRecording(fieldId, text) }) {
                    Image(systemName: (activeRecordingField == fieldId && voiceRecorder.isRecording) ? "stop.circle.fill" : "mic.circle.fill")
                        .font(.system(size: 30))
                        .foregroundColor((activeRecordingField == fieldId && voiceRecorder.isRecording) ? .red : .blue)
                        .scaleEffect((activeRecordingField == fieldId && voiceRecorder.isRecording) ? 1.2 : 1.0)
                        .animation(.easeInOut(duration: 0.2), value: voiceRecorder.isRecording)
                }
            }
            
            ZStack(alignment: .topLeading) {
                // Placeholder (텍스트가 비어있고 포커스 아닐 때)
                if text.isEmpty {
                    Text(placeholders[fieldId] ?? "여기에 입력하세요...")
                        .foregroundColor(Color.gray.opacity(0.5))
                        .padding(.horizontal, 13)
                        .padding(.vertical, 16)
                        .allowsHitTesting(false)
                }
                
                TextEditor(text: $text)
                    .focused($isFocused)
                    .frame(height: 100)
                    .padding(8)
                    .scrollContentBackground(.hidden)
                    .background(isFocused ? Color.blue.opacity(0.04) : Color.gray.opacity(0.08))
                    .cornerRadius(12)
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(isFocused ? Color.blue.opacity(0.6) : Color.clear, lineWidth: 2)
                    )
                    .tint(.blue) // 커서 색상
                    .animation(.easeInOut(duration: 0.2), value: isFocused)
            }
        }
        .padding()
        .background(Color.white)
        .cornerRadius(16)
        .shadow(color: Color.black.opacity(0.03), radius: 5, x: 0, y: 2)
    }
}