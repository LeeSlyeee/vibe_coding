import SwiftUI

struct AppSettingsView: View {
    @EnvironmentObject var authManager: AuthManager
    @ObservedObject var b2gManager = B2GManager.shared
    
    @State private var inputCode = ""
    @State private var showAlert = false
    @State private var alertMessage = ""
    
    // Login States
    @State private var loginId = ""
    @State private var loginPw = ""
    @State private var isLoggingIn = false
    

    @State private var showPremiumModal = false // New Modal State
    @State private var showExitAlert = false // Exit Confirmation
    @State private var showDisconnectAlert = false // Disconnect Confirmation [New]
    @State private var isPwVisible = false // Password Reveal Only
    @State private var useCustomLogin = false // Toggle between Auto-Account and Custom Login
    @State private var showBirthDatePicker = false // [New] Birth Date Picker
    @State private var showMindBridgeMain = false // [Phase 3] 마음 브릿지 메인
    
    // [보안] 스크린샷 방지 설정
    @AppStorage("isScreenshotPreventionOn") private var isScreenshotPreventionOn: Bool = false
    
    // [일기 알림] 매일 알림 설정
    @AppStorage("isDiaryReminderOn") private var isDiaryReminderOn: Bool = false
    @AppStorage("diaryReminderHour") private var diaryReminderHour: Int = 21
    @AppStorage("diaryReminderMinute") private var diaryReminderMinute: Int = 0
    @State private var diaryReminderDate = Date()
    
    // Unified Alert System [Fix]
    enum ActiveAlert: Identifiable {
        case info(String)
        case disconnect
        
        var id: String {
            switch self {
            case .info(let msg): return "info-\(msg)"
            case .disconnect: return "disconnect"
            }
        }
    }
    @State private var activeAlert: ActiveAlert?
    
    var body: some View {
            List {
                // Section 1: 계정 & 프로필
                Section(header: Text("내 정보")) {
                    if authManager.isAuthenticated {
                        // 로그인 된 상태
                        HStack {
                            Image(systemName: "person.circle.fill")
                                .font(.largeTitle)
                                .foregroundColor(.accent)
                            VStack(alignment: .leading) {
                                Text(authManager.username ?? "사용자")
                                    .font(.headline)
                                Text("연동 계정 로그인됨")
                                    .font(.caption)
                                    .foregroundColor(.accent)
                            }
                            Spacer()
                            Button("로그아웃") {
                                authManager.logout()
                            }
                            .foregroundColor(.red)
                            .font(.caption)
                        }
                        .padding(.vertical, 8)
                        
                        // [New] Birth Date Setting
                        HStack {
                            Text("생년월일")
                            Spacer()
                            if let bDate = authManager.birthDate {
                                Text(bDate)
                                    .foregroundColor(.primary)
                            } else {
                                Text("설정되지 않음")
                                    .foregroundColor(.hintText)
                            }
                            
                            // Edit Button (trigger sheet or inline picker)
                            Button("변경") {
                                showBirthDatePicker = true
                            }
                            .font(.caption)
                            .foregroundColor(.accent)
                        }
                    } else {
                        // [Dual Mode] Auto Account vs Custom Login
                        if !useCustomLogin {
                            // [Auto-Auth Info] 앱이 자동 생성한 계정 정보 표시
                            VStack(alignment: .leading, spacing: 12) {
                                HStack {
                                    Image(systemName: "person.crop.circle.fill.badge.checkmark")
                                        .font(.largeTitle)
                                        .foregroundColor(.green)
                                    VStack(alignment: .leading) {
                                        Text("내 앱 계정")
                                            .font(.headline)
                                        Text("웹(Web)에서 이 정보로 로그인하세요.")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                }
                                
                                // 1. ID Display
                                HStack {
                                    Text("아이디:")
                                        .foregroundColor(.hintText)
                                    Spacer()
                                    Text(UserDefaults.standard.string(forKey: "app_username") ?? "생성 중...")
                                        .fontWeight(.bold)
                                        .textSelection(.enabled)
                                }
                                .padding(.vertical, 4)
                                
                                // 2. PW Display
                                HStack {
                                    Text("비밀번호:")
                                        .foregroundColor(.hintText)
                                    Spacer()
                                    if isPwVisible {
                                        Text(KeychainHelper.standard.readString(account: "app_password") ?? "****")
                                            .fontWeight(.bold)
                                            .foregroundColor(.orange)
                                    } else {
                                        Text("••••••••")
                                            .fontWeight(.bold)
                                    }
                                    
                                    Button(action: { isPwVisible.toggle() }) {
                                        Image(systemName: isPwVisible ? "eye.slash" : "eye")
                                            .foregroundColor(.accent)
                                    }
                                }
                                .padding(.vertical, 4)
                                
                                Divider()
                                
                                // 사용자 친화적 로그인 버튼 (Web ID 연동)
                                Button(action: {
                                    withAnimation { useCustomLogin = true }
                                }) {
                                    HStack(spacing: 12) {
                                        Image(systemName: "globe")
                                            .font(.title2)
                                            .foregroundColor(.white)
                                            
                                        VStack(alignment: .leading, spacing: 2) {
                                            Text("웹사이트 아이디로 연결하기")
                                                .fontWeight(.bold)
                                                .foregroundColor(.white)
                                            Text("웹 캘린더와 데이터를 동기화합니다")
                                                .font(.caption)
                                                .foregroundColor(.white.opacity(0.9))
                                        }
                                        Spacer()
                                        Image(systemName: "chevron.right")
                                            .foregroundColor(.white.opacity(0.8))
                                    }
                                    .padding()
                                    .background(Color.accent) // 브랜드 컬러 유지
                                    .cornerRadius(12)
                                    .shadow(color: Color.accent.opacity(0.3), radius: 4, x: 0, y: 2)
                                }
                                .padding(.top, 8)
                            }
                            .padding(.vertical, 8)
                        } else {
                            // [Custom Login Form] 기존 계정 로그인
                            VStack(alignment: .leading, spacing: 12) {
                                Text("기존 계정 로그인")
                                    .font(.headline)
                                
                                TextField("아이디 (Web)", text: $loginId)
                                    .keyboardType(.default) // [Fix] Allow Korean/English switch
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                                    .textInputAutocapitalization(.none)
                                
                                SecureField("비밀번호", text: $loginPw)
                                    .keyboardType(.default) // [User Request] Allow user's keyboard choice
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                                
                                Button(action: {
                                    isLoggingIn = true
                                    // 1. Overwrite Credentials
                                    UserDefaults.standard.set(loginId, forKey: "app_username")
                                    KeychainHelper.standard.saveString(loginPw, account: "app_password")
                                    UserDefaults.standard.set(loginId, forKey: "userNickname") // Display Name
                                    // [Fix] authUsername도 함께 설정 (Single Source of Truth)
                                    UserDefaults.standard.set(loginId, forKey: "authUsername")
                                    
                                    // 2. Auth Check
                                    APIService.shared.ensureAuth { success in
                                        isLoggingIn = false
                                        if success {
                                            authManager.username = loginId // Update UI state if needed
                                            activeAlert = .info("로그인 성공! 이제 이 계정으로 동기화됩니다.")
                                        } else {
                                            // [Fix] 실패 시 authUsername 롤백
                                            UserDefaults.standard.removeObject(forKey: "authUsername")
                                            activeAlert = .info("로그인 실패. 아이디/비밀번호를 확인하세요.")
                                        }
                                        // loginPw = "" // Keep it for retry convenience
                                    }
                                }) {
                                    HStack {
                                        if isLoggingIn { ProgressView().padding(.trailing, 5) }
                                        Text("로그인 하기")
                                    }
                                    .frame(maxWidth: .infinity)
                                    .padding()
                                    .background(Color.accent)
                                    .foregroundColor(.white)
                                    .cornerRadius(10)
                                }
                                .disabled(loginId.isEmpty || loginPw.isEmpty || isLoggingIn)
                                
                                Button(action: {
                                    withAnimation { useCustomLogin = false }
                                }) {
                                    Text("취소 (앱 계정 사용)")
                                        .font(.caption)
                                        .foregroundColor(.hintText)
                                }
                                .frame(maxWidth: .infinity)
                            }
                            .padding(.vertical, 8)
                        }
                    }
                }
                
                // [Section 1.5] 보호자/친구 연결 (독립 섹션)
                Section {
                    NavigationLink(destination: AppShareView()) {
                        HStack(spacing: 15) {
                            ZStack {
                                Circle()
                                    .fill(Color.accent.opacity(0.1))
                                    .frame(width: 40, height: 40)
                                Image(systemName: "person.2.fill")
                                    .foregroundColor(.accent)
                                    .font(.system(size: 20))
                            }
                            
                            VStack(alignment: .leading, spacing: 2) {
                                Text("보호자/친구 연결")
                                    .font(.headline)
                                    .foregroundColor(.primary)
                                Text("가족과 감정 통계 공유하기")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                        .padding(.vertical, 4)
                    }
                }
                
                // Section 2: B2G 연동 (핵심 기능)
                Section(header: Text("기관 연동 (B2G)")) {
                    if b2gManager.isLinked {
                        // 연동 된 상태
                        VStack(alignment: .leading, spacing: 12) {
                            HStack {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(.green)
                                Text("보건소 연동됨")
                                    .font(.headline)
                                    .foregroundColor(.green)
                            }
                            
                            Text("현재 담당 선생님과 연결되어 있습니다.")
                                .font(.subheadline)
                            
                            HStack {
                                Text("연동 코드:")
                                    .foregroundColor(.hintText)
                                Text(b2gManager.centerCode)
                                    .font(.system(.body, design: .monospaced))
                                    .fontWeight(.bold)
                                
                                Spacer()
                                
                                // [UX Change] Disconnect button moved next to code
                                Button(action: {
                                    activeAlert = .disconnect
                                }) {
                                    Text("연동 해제")
                                        .font(.caption)
                                        .fontWeight(.bold)
                                        .padding(.horizontal, 10)
                                        .padding(.vertical, 5)
                                        .background(Color.red.opacity(0.1))
                                        .foregroundColor(.red)
                                        .cornerRadius(8)
                                }
                            }
                            
                            // [Debug Info] Show Current App User ID
                            if let username = UserDefaults.standard.string(forKey: "app_username") {
                                HStack {
                                    Text("앱 계정 ID:")
                                        .foregroundColor(.hintText)
                                        .font(.caption)
                                    Text(username)
                                        .foregroundColor(.secondary)
                                        .font(.caption)
                                }
                                .padding(.top, 4)
                            }
                            
                            if b2gManager.lastSyncDate > 0 {
                                Text("마지막 전송: \(Date(timeIntervalSince1970: b2gManager.lastSyncDate).formatted())")
                                    .font(.caption2)
                                    .foregroundColor(.hintText)
                            }
                            

                        }
                        .padding(.vertical, 8)
                        
                    } else {
                        // 연동 안 된 상태
                        VStack(alignment: .leading, spacing: 10) {
                            Text("보건소/정신건강복지센터 연결하기")
                                .font(.headline)
                            Text("담당 선생님께 전달받은 코드를 입력하세요.")
                                .font(.caption)
                                .foregroundColor(.hintText)
                            
                            HStack {
                                TextField("예: SEOUL-001", text: $inputCode)
                                    .keyboardType(.default) // [Fix] Allow Korean input
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                                    #if os(iOS)
                                    .textInputAutocapitalization(.characters)
                                    #endif
                                
                                Button(action: {
                                    b2gManager.connect(code: inputCode) { success, message in
                                        activeAlert = .info(message)
                                    }
                                }) {
                                    if b2gManager.isSyncing {
                                        ProgressView()
                                    } else {
                                        Text("연결")
                                            .fontWeight(.bold)
                                    }
                                }
                                .disabled(inputCode.isEmpty || b2gManager.isSyncing)
                            }
                        }
                        .padding(.vertical, 8)
                    }
                }
                
                // Section: 데이터 동기화 (B2G 연동 여부와 무관하게 항상 표시)
                Section(header: Text("데이터 동기화")) {
                    VStack(spacing: 12) {
                        // 1. Force Sync (Push: App → Server)
                        Button(action: {
                            let generator = UIImpactFeedbackGenerator(style: .medium)
                            generator.impactOccurred()
                            
                            LocalDataManager.shared.syncWithServer(force: true)
                            if b2gManager.isLinked {
                                b2gManager.syncData(force: true)
                            }
                            
                            activeAlert = .info("모든 데이터를 서버로 다시 전송합니다.")
                        }) {
                            HStack {
                                Image(systemName: "arrow.up.circle.fill")
                                    .font(.system(size: 18))
                                Text("데이터 강제 전송 (App → Server)")
                                    .fontWeight(.bold)
                                    .font(.system(size: 16))
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.accent)
                            .foregroundColor(.white)
                            .cornerRadius(12)
                            .shadow(color: Color.accent.opacity(0.3), radius: 4, x: 0, y: 2)
                        }
                        .buttonStyle(BorderlessButtonStyle())
                        
                        // 2. Pull Data (Server → App)
                        Button(action: {
                            let generator = UIImpactFeedbackGenerator(style: .medium)
                            generator.impactOccurred()
                            
                            APIService.shared.fetchDiaries { serverData in
                                if let data = serverData {
                                    LocalDataManager.shared.mergeServerDiaries(data) {
                                        DispatchQueue.main.async {
                                            activeAlert = .info("서버에서 \(data.count)개의 데이터를 가져왔습니다.")
                                        }
                                    }
                                } else {
                                    DispatchQueue.main.async {
                                        activeAlert = .info("데이터를 가져오지 못했습니다. (서버 응답 없음)")
                                    }
                                }
                            }
                        }) {
                            HStack {
                                Image(systemName: "arrow.down.circle.fill")
                                    .font(.system(size: 18))
                                Text("서버 데이터 가져오기 (Server → App)")
                                    .fontWeight(.bold)
                                    .font(.system(size: 16))
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.green)
                            .foregroundColor(.white)
                            .cornerRadius(12)
                            .shadow(color: Color.green.opacity(0.3), radius: 4, x: 0, y: 2)
                        }
                        .buttonStyle(BorderlessButtonStyle())
                    }
                    .padding(.vertical, 8)
                    
                    Text("* 데이터가 보이지 않거나 꼬였을 때 위 버튼들을 눌러 동기화하세요.")
                        .font(.caption2)
                        .foregroundColor(.hintText)
                        .multilineTextAlignment(.center)
                }
                
                // Section 3: 멤버십 (Membership)
                Section(header: Text("멤버십")) {
                    if b2gManager.isLinked {
                        // Case A: 기관 연동 사용자 (보건소 연동 유저)
                        HStack {
                            Image(systemName: "building.columns.fill")
                                .foregroundColor(.accent)
                                .font(.title2)
                            VStack(alignment: .leading, spacing: 4) {
                                Text("기관 연동 멤버십")
                                    .font(.headline)
                                    .fontWeight(.bold)
                                    .foregroundColor(.accent)
                                Text("보건소 연동으로 프리미엄 혜택이 적용됩니다.")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            Spacer()
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                        }
                        .padding(.vertical, 4)
                        
                    } else if SubscriptionManager.shared.isSubscribed {
                        // Case B: 마음 브릿지 구독 중
                        VStack(alignment: .leading, spacing: 12) {
                            HStack(spacing: 15) {
                                ZStack {
                                    Circle()
                                        .fill(
                                            LinearGradient(
                                                colors: [Color.gray900, Color.gray600],
                                                startPoint: .topLeading,
                                                endPoint: .bottomTrailing
                                            )
                                        )
                                        .frame(width: 40, height: 40)
                                    Image(systemName: "heart.text.clipboard")
                                        .foregroundColor(.white)
                                        .font(.system(size: 18))
                                }
                                
                                VStack(alignment: .leading, spacing: 4) {
                                    HStack {
                                        Text("마음 브릿지")
                                            .font(.headline)
                                            .fontWeight(.bold)
                                            .foregroundColor(Color.gray900)
                                        
                                        Text(SubscriptionManager.shared.isInTrialPeriod ? "체험 중" : "구독 중")
                                            .font(.caption2)
                                            .fontWeight(.bold)
                                            .padding(.horizontal, 8)
                                            .padding(.vertical, 3)
                                            .background(Color.gray900.opacity(0.1))
                                            .foregroundColor(Color.gray900)
                                            .cornerRadius(8)
                                    }
                                    
                                    if let days = SubscriptionManager.shared.daysUntilExpiry {
                                        Text("다음 갱신까지 \(days)일")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                }
                                Spacer()
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(.green)
                            }
                            .padding(.vertical, 4)
                            
                            // [Phase 3] 마음 브릿지 메인 진입
                            Button(action: { showMindBridgeMain = true }) {
                                HStack {
                                    Image(systemName: "heart.text.clipboard")
                                        .font(.caption)
                                    Text("마음 브릿지 열기")
                                        .font(.subheadline)
                                        .fontWeight(.bold)
                                }
                                .foregroundColor(.white)
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 10)
                                .background(
                                    LinearGradient(
                                        colors: [Color.gray900, Color.gray600],
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    )
                                )
                                .cornerRadius(10)
                            }
                            .buttonStyle(BorderlessButtonStyle())
                            
                            // 구독 관리 링크
                            Button(action: {
                                if let url = URL(string: "https://apps.apple.com/account/subscriptions") {
                                    UIApplication.shared.open(url)
                                }
                            }) {
                                HStack {
                                    Image(systemName: "gear")
                                        .font(.caption)
                                    Text("구독 관리 (App Store)")
                                        .font(.caption)
                                }
                                .foregroundColor(.hintText)
                            }
                        }
                        
                    } else {
                        // Case C: 일반 사용자 (마음 브릿지 업그레이드 유도)
                        Button(action: { showPremiumModal = true }) {
                            HStack(spacing: 15) {
                                ZStack {
                                    Circle()
                                        .fill(
                                            LinearGradient(
                                                colors: [Color.gray900, Color.gray600],
                                                startPoint: .topLeading,
                                                endPoint: .bottomTrailing
                                            )
                                        )
                                        .frame(width: 40, height: 40)
                                    Image(systemName: "heart.text.clipboard")
                                        .foregroundColor(.white)
                                        .font(.system(size: 18))
                                }
                                
                                VStack(alignment: .leading, spacing: 4) {
                                    Text("마음 브릿지")
                                        .font(.headline)
                                        .fontWeight(.bold)
                                        .foregroundColor(Color.gray900)
                                    Text("가족·상담사에게 내 마음을 안전하게 전해보세요")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                                Spacer()
                                Image(systemName: "chevron.right")
                                    .foregroundColor(.hintText)
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }
                
                // Section 3.5: 지원 (Support)
                Section(header: Text("지원")) {
                    NavigationLink(destination: AppGuideView()) {
                        HStack {
                            Image(systemName: "book.fill")
                                .foregroundColor(.accent)
                            Text("사용 가이드")
                                .foregroundColor(.primary)
                        }
                    }
                }
                
                // Section 4: 앱 정보
                Section(header: Text("앱 정보")) {
                    HStack {
                        Text("버전")
                        Spacer()
                        Text("1.0.0 (On-Device Al)")
                            .foregroundColor(.hintText)
                    }
                    HStack {
                        Text("개발자")
                        Spacer()
                        Text("Maum-on Team")
                            .foregroundColor(.hintText)
                    }

                }
                
                // Section 4.5: 보안 설정
                Section(header: Text("보안")) {
                    HStack {
                        Image(systemName: "lock.shield.fill")
                            .foregroundColor(.green)
                            .font(.title2)
                        VStack(alignment: .leading, spacing: 4) {
                            Toggle("화면 캡처 방지", isOn: $isScreenshotPreventionOn)
                                .font(.headline)
                            Text("앱 화면이 캡처되거나 녹화되는 것을 방지합니다.")
                                .font(.caption)
                                .foregroundColor(.hintText)
                        }
                    }
                    .padding(.vertical, 4)
                }
                
                // Section: 일기 알림 (Daily Diary Reminder)
                Section(header: Text("일기 알림")) {
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Image(systemName: "bell.badge.fill")
                                .foregroundColor(.orange)
                                .font(.title2)
                            VStack(alignment: .leading, spacing: 4) {
                                Toggle("매일 일기 알림", isOn: $isDiaryReminderOn)
                                    .font(.headline)
                                    .onChange(of: isDiaryReminderOn) { newValue in
                                        if newValue {
                                            DiaryReminderManager.schedule(hour: diaryReminderHour, minute: diaryReminderMinute)
                                        } else {
                                            DiaryReminderManager.cancel()
                                        }
                                    }
                                Text("설정한 시간에 일기 작성을 알려드려요")
                                    .font(.caption)
                                    .foregroundColor(.hintText)
                            }
                        }
                        
                        if isDiaryReminderOn {
                            HStack {
                                Image(systemName: "clock.fill")
                                    .foregroundColor(.accent)
                                Text("알림 시간")
                                Spacer()
                                DatePicker(
                                    "",
                                    selection: $diaryReminderDate,
                                    displayedComponents: .hourAndMinute
                                )
                                .labelsHidden()
                                .onChange(of: diaryReminderDate) { newDate in
                                    let calendar = Calendar.current
                                    diaryReminderHour = calendar.component(.hour, from: newDate)
                                    diaryReminderMinute = calendar.component(.minute, from: newDate)
                                    DiaryReminderManager.schedule(hour: diaryReminderHour, minute: diaryReminderMinute)
                                }
                            }
                            
                            // 알림 미리보기
                            HStack(spacing: 8) {
                                Image(systemName: "bubble.left.fill")
                                    .foregroundColor(.accent.opacity(0.6))
                                    .font(.caption)
                                Text("\"오늘 하루는 어땠나요? 마음을 기록해보세요 ✍️\"")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                    .italic()
                            }
                            .padding(10)
                            .background(Color.accent.opacity(0.05))
                            .cornerRadius(8)
                        }
                    }
                    .padding(.vertical, 4)
                    .onAppear {
                        // 저장된 시간으로 DatePicker 초기화
                        var components = DateComponents()
                        components.hour = diaryReminderHour
                        components.minute = diaryReminderMinute
                        if let date = Calendar.current.date(from: components) {
                            diaryReminderDate = date
                        }
                    }
                }
                
                // Section 4.5: 법적 고지 (Legal Disclaimer)
                Section(header: HStack {
                    Image(systemName: "building.columns.fill")
                    Text("법적 고지")
                }) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("마음온은 감정 기록 보조 도구입니다")
                            .font(.subheadline)
                            .fontWeight(.semibold)
                        
                        Text("본 서비스는 의료 행위, 심리 치료, 또는 전문 상담을 대체하지 않습니다. AI가 제공하는 분석과 코멘트는 참고용이며, 의료적 판단으로 간주될 수 없습니다.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        HStack(alignment: .top, spacing: 4) {
                            Image(systemName: "exclamationmark.triangle.fill")
                            Text("AI의 위기 감지 기능은 보조적 수단이며, 100% 정확성을 보장하지 않습니다. AI가 감지하지 못하는 위기 상황이 발생할 수 있으므로, 긴급한 상황에서는 즉시 1393 또는 119에 직접 연락해 주세요.")
                        }
                        .font(.caption)
                        .foregroundColor(.orange)
                        
                        Divider()
                        
                        HStack(spacing: 4) {
                            Image(systemName: "exclamationmark.triangle.fill")
                            Text("긴급 상황 안내")
                        }
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundColor(.red)
                        
                        Text("정신건강 위기 상황에서는 반드시 전문 의료기관 또는 아래 긴급전화를 이용해 주세요.\n• 자살예방 상담전화: 1393\n• 정신건강 위기상담전화: 1577-0199\n• 경찰: 112")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Divider()
                        
                        HStack(spacing: 4) {
                            Image(systemName: "doc.text.fill")
                            Text("개인정보 처리")
                        }
                        .font(.caption)
                        .fontWeight(.semibold)
                        
                        Text("기본적으로 모든 데이터는 사용자 기기에만 저장됩니다. 기관 연동 시에만 선택한 정보가 암호화되어 전송됩니다.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    .padding(.vertical, 4)
                }
                
                // Section 5: 앱 종료 (Safe Exit)
                Section {
                    Button(action: {
                        showExitAlert = true
                    }) {
                        HStack {
                            Spacer()
                            Text("앱 종료 (Exit)")
                                .fontWeight(.bold)
                                .foregroundColor(.red)
                            Spacer()
                        }
                    }
                    .alert(isPresented: $showExitAlert) {
                        Alert(
                            title: Text("앱 종료"),
                            message: Text("앱을 완전히 종료하시겠습니까?"),
                            primaryButton: .destructive(Text("종료")) {
                                exit(0)
                            },
                            secondaryButton: .cancel(Text("취소"))
                        )
                    }
                }

            } // End List
            .navigationTitle("설정")
            .alert(item: $activeAlert) { item in
                switch item {
                case .info(let message):
                    return Alert(title: Text("알림"), message: Text(message), dismissButton: .default(Text("확인")))
                case .disconnect:
                    return Alert(
                        title: Text("연동 해제"),
                        message: Text("정말 연결을 끊으시겠습니까?\n서버의 데이터는 삭제되지 않지만, 앱에서는 더 이상 전송되지 않습니다."),
                        primaryButton: .destructive(Text("해제")) {
                            b2gManager.disconnect(force: true)
                        },
                        secondaryButton: .cancel(Text("취소"))
                    )
                }
            }
            .sheet(isPresented: $showPremiumModal) {
                MindBridgePaywallView(isPresented: $showPremiumModal)
            }
            .sheet(isPresented: $showBirthDatePicker) {
                BirthDatePickerView(isPresented: $showBirthDatePicker)
                    .environmentObject(authManager)
            }
            .sheet(isPresented: $showMindBridgeMain) {
                MindBridgeMainView()
            }
    }
    

}

// [New] Birth Date Picker View
struct BirthDatePickerView: View {
    @Binding var isPresented: Bool
    @EnvironmentObject var authManager: AuthManager
    
    @State private var selectedDate = Date()
    @State private var isSaving = false
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("생년월일을 선택하세요")) {
                    DatePicker(
                        "생년월일",
                        selection: $selectedDate,
                        in: ...Date(),
                        displayedComponents: .date
                    )
                    .datePickerStyle(.wheel)
                    .labelsHidden()
                    .environment(\.locale, Locale(identifier: "ko_KR"))
                }
                
                Section {
                    Button(action: {
                        isSaving = true
                        let formatter = DateFormatter()
                        formatter.dateFormat = "yyyy-MM-dd"
                        let dateStr = formatter.string(from: selectedDate)
                        
                        authManager.updateBirthDate(dateStr) { success in
                            isSaving = false
                            isPresented = false
                        }
                    }) {
                        HStack {
                            Spacer()
                            if isSaving {
                                ProgressView()
                            } else {
                                Text("저장하기")
                                    .fontWeight(.bold)
                            }
                            Spacer()
                        }
                    }
                    .disabled(isSaving)
                    .foregroundColor(.white)
                    .listRowBackground(Color.accent)
                }
            }
            .navigationTitle("생년월일 설정")
            .navigationBarItems(trailing: Button("취소") { isPresented = false })
            .onAppear {
                let formatter = DateFormatter()
                formatter.dateFormat = "yyyy-MM-dd"
                if let saved = authManager.birthDate, let date = formatter.date(from: saved) {
                    selectedDate = date
                } else {
                    // 기본값: 1986-03-11
                    var components = DateComponents()
                    components.year = 1986
                    components.month = 3
                    components.day = 11
                    if let defaultDate = Calendar.current.date(from: components) {
                        selectedDate = defaultDate
                    }
                }
            }
        }
    }
}
