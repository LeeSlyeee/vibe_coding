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
    
    // Temporary Dev State
    @State private var tempInputCode = ""
    @State private var showPremiumModal = false // New Modal State
    @State private var showExitAlert = false // Exit Confirmation
    @State private var showDisconnectAlert = false // Disconnect Confirmation [New]
    @State private var isPwVisible = false // Password Reveal Only
    @State private var useCustomLogin = false // Toggle between Auto-Account and Custom Login
    @State private var showBirthDatePicker = false // [New] Birth Date Picker
    @State private var showMindBridgeMain = false // [Phase 3] 마음 브릿지 메인
    
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
                                    .foregroundColor(.blue)
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
                                    .foregroundColor(.gray)
                            }
                            
                            // Edit Button (trigger sheet or inline picker)
                            Button("변경") {
                                showBirthDatePicker = true
                            }
                            .font(.caption)
                            .foregroundColor(.blue)
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
                                        .foregroundColor(.gray)
                                    Spacer()
                                    Text(UserDefaults.standard.string(forKey: "app_username") ?? "생성 중...")
                                        .fontWeight(.bold)
                                        .textSelection(.enabled)
                                }
                                .padding(.vertical, 4)
                                
                                // 2. PW Display
                                HStack {
                                    Text("비밀번호:")
                                        .foregroundColor(.gray)
                                    Spacer()
                                    if isPwVisible {
                                        Text(UserDefaults.standard.string(forKey: "app_password") ?? "****")
                                            .fontWeight(.bold)
                                            .foregroundColor(.orange)
                                    } else {
                                        Text("••••••••")
                                            .fontWeight(.bold)
                                    }
                                    
                                    Button(action: { isPwVisible.toggle() }) {
                                        Image(systemName: isPwVisible ? "eye.slash" : "eye")
                                            .foregroundColor(.blue)
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
                                    .background(Color.blue) // 브랜드 컬러 유지
                                    .cornerRadius(12)
                                    .shadow(color: Color.blue.opacity(0.3), radius: 4, x: 0, y: 2)
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
                                    UserDefaults.standard.set(loginPw, forKey: "app_password")
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
                                        .foregroundColor(.gray)
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
                                    .fill(Color.purple.opacity(0.1))
                                    .frame(width: 40, height: 40)
                                Image(systemName: "person.2.fill")
                                    .foregroundColor(.purple)
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
                                    .foregroundColor(.gray)
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
                                        .foregroundColor(.gray)
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
                                    .foregroundColor(.gray)
                            }
                            
                            // [Buttons] Sync Actions
                            VStack(spacing: 12) {
                                // 1. Force Sync (Push)
                                Button(action: {
                                    // [Haptic & Action]
                                    let generator = UIImpactFeedbackGenerator(style: .medium)
                                    generator.impactOccurred()
                                    
                                    // [Fix] Dual Sync: Sync Personal (Calendar) AND B2G (Center)
                                    LocalDataManager.shared.syncWithServer(force: true)
                                    b2gManager.syncData(force: true)
                                    
                                    activeAlert = .info("모든 데이터를 서버로 다시 전송합니다.\n(개인 캘린더 및 센터 대시보드 동기화)")
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
                                    .background(Color.blue)
                                    .foregroundColor(.white)
                                    .cornerRadius(12)
                                    .shadow(color: Color.blue.opacity(0.3), radius: 4, x: 0, y: 2)
                                }
                                .buttonStyle(BorderlessButtonStyle()) // [Fix] List 내부 버튼 간섭 방지

                                // 2. Pull Data (Server -> App)
                                Button(action: {
                                    // [Haptic & Action]
                                    let generator = UIImpactFeedbackGenerator(style: .medium)
                                    generator.impactOccurred()
                                    
                                    b2gManager.pullDataFromServer { success, msg in
                                        activeAlert = .info(msg)
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
                                    .background(Color.green) // Distinct Color
                                    .foregroundColor(.white)
                                    .cornerRadius(12)
                                    .shadow(color: Color.green.opacity(0.3), radius: 4, x: 0, y: 2)
                                }
                                .buttonStyle(BorderlessButtonStyle()) // [Fix] List 내부 버튼 간섭 방지
                            }
                            .padding(.vertical, 8)
                            
                            Text("* 데이터가 보이지 않거나 꼬였을 때 위 버튼들을 눌러 동기화하세요.")
                                .font(.caption2)
                                .foregroundColor(.gray)
                                .multilineTextAlignment(.center)
                        }
                        .padding(.vertical, 8)
                        
                    } else {
                        // 연동 안 된 상태
                        VStack(alignment: .leading, spacing: 10) {
                            Text("보건소/정신건강복지센터 연결하기")
                                .font(.headline)
                            Text("담당 선생님께 전달받은 코드를 입력하세요.")
                                .font(.caption)
                                .foregroundColor(.gray)
                            
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
                
                // Section 3: 멤버십 (Membership)
                Section(header: Text("멤버십")) {
                    if b2gManager.isLinked {
                        // Case A: 기관 연동 사용자 (보건소 연동 유저)
                        HStack {
                            Image(systemName: "building.columns.fill")
                                .foregroundColor(.blue)
                                .font(.title2)
                            VStack(alignment: .leading, spacing: 4) {
                                Text("기관 연동 멤버십")
                                    .font(.headline)
                                    .fontWeight(.bold)
                                    .foregroundColor(.blue)
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
                                                colors: [Color(hexString: "6366f1"), Color(hexString: "8b5cf6")],
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
                                        Text("🌉 마음 브릿지")
                                            .font(.headline)
                                            .fontWeight(.bold)
                                            .foregroundColor(Color(hexString: "6366f1"))
                                        
                                        Text(SubscriptionManager.shared.isInTrialPeriod ? "체험 중" : "구독 중")
                                            .font(.caption2)
                                            .fontWeight(.bold)
                                            .padding(.horizontal, 8)
                                            .padding(.vertical, 3)
                                            .background(Color(hexString: "6366f1").opacity(0.1))
                                            .foregroundColor(Color(hexString: "6366f1"))
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
                                        colors: [Color(hexString: "6366f1"), Color(hexString: "8b5cf6")],
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
                                .foregroundColor(.gray)
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
                                                colors: [Color(hexString: "6366f1"), Color(hexString: "8b5cf6")],
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
                                    Text("🌉 마음 브릿지")
                                        .font(.headline)
                                        .fontWeight(.bold)
                                        .foregroundColor(Color(hexString: "6366f1"))
                                    Text("가족·상담사에게 내 마음을 안전하게 전해보세요")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                                Spacer()
                                Image(systemName: "chevron.right")
                                    .foregroundColor(.gray)
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
                                .foregroundColor(.blue)
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
                            .foregroundColor(.gray)
                    }
                    HStack {
                        Text("개발자")
                        Spacer()
                        Text("Maum-on Team")
                            .foregroundColor(.gray)
                    }
                    
                    // [Hidden Feature] 개발자용 데이터 생성 버튼
                    Button(action: {
                        seedData()
                    }) {
                        Text("[개발자용] 테스트 데이터 생성 (Demo)")
                            .font(.caption)
                            .foregroundColor(.blue)
                    }
                }
                
                // Section 4.5: 법적 고지 (Legal Disclaimer)
                Section(header: Text("⚖️ 법적 고지")) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("마음온은 감정 기록 보조 도구입니다")
                            .font(.subheadline)
                            .fontWeight(.semibold)
                        
                        Text("본 서비스는 의료 행위, 심리 치료, 또는 전문 상담을 대체하지 않습니다. AI가 제공하는 분석과 코멘트는 참고용이며, 의료적 판단으로 간주될 수 없습니다.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Text("⚠️ AI의 위기 감지 기능은 보조적 수단이며, 100% 정확성을 보장하지 않습니다. AI가 감지하지 못하는 위기 상황이 발생할 수 있으므로, 긴급한 상황에서는 즉시 1393 또는 119에 직접 연락해 주세요.")
                            .font(.caption)
                            .foregroundColor(.orange)
                        
                        Divider()
                        
                        Text("⚠️ 긴급 상황 안내")
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundColor(.red)
                        
                        Text("정신건강 위기 상황에서는 반드시 전문 의료기관 또는 아래 긴급전화를 이용해 주세요.\n• 자살예방 상담전화: 1393\n• 정신건강 위기상담전화: 1577-0199\n• 경찰: 112")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Divider()
                        
                        Text("📋 개인정보 처리")
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
                                print("👋 [App] User confirmed exit.")
                                exit(0)
                            },
                            secondaryButton: .cancel(Text("취소"))
                        )
                    }
                }
                
                // Section 4: 개발자 임시 기능 (Requested Feature)
                Section(header: Text("🛠️ 개발자 임시 기능 (Remove Later)")) {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("연동 코드 강제 변경")
                            .font(.headline)
                            .foregroundColor(.orange)
                        
                        Text("기존 연동을 무시하고 새로운 코드로 강제 재연동합니다.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        HStack {
                            TextField("새 코드 (예: TEMP-001)", text: $tempInputCode)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                #if os(iOS)
                                .textInputAutocapitalization(.characters)
                                #endif
                            
                            Button(action: {
                                guard !tempInputCode.isEmpty else { return }
                                
                                // Debug: Print Endpoint
                                print("⚪️ Requesting Verification for: \(tempInputCode)")
                                
                                // APIService를 통한 직접 연동 시도
                                APIService.shared.verifyCenterCode(tempInputCode) { res in
                                    switch res {
                                    case .success(let data):
                                        // Handle both Int and String IDs (MongoDB ObjectId is String)
                                        var targetId: Any? = data["center_id"]
                                        
                                        if let idInt = data["center_id"] as? Int {
                                            targetId = idInt
                                        } else if let idStr = data["center_id"] as? String {
                                            targetId = idStr
                                        }
                                        
                                        if let validId = targetId {
                                            APIService.shared.connectToCenter(centerId: validId) { success in
                                                DispatchQueue.main.async {
                                                    if success {
                                                        // B2GManager 상태 강제 동기화 (Updated for encapsulation)
                                                        b2gManager.forceLink(code: tempInputCode.uppercased())
                                                        activeAlert = .info("✅ 강제 연동 성공!\n코드: \(tempInputCode.uppercased())")
                                                        tempInputCode = ""
                                                    } else {
                                                        activeAlert = .info("❌ 기관 연결(Connect) API 실패")
                                                    }
                                                }
                                            }
                                        } else {
                                            DispatchQueue.main.async {
                                                activeAlert = .info("⚠️ 센터 ID를 찾을 수 없습니다 (응답 데이터 오류).")
                                            }
                                        }
                                    case .failure(let err):
                                        DispatchQueue.main.async {
                                            activeAlert = .info("❌ 오류 발생 (재빌드 필요?)\n\(err.localizedDescription)")
                                        }
                                    }
                                }
                            }) {
                                Text("변경")
                                    .fontWeight(.bold)
                                    .foregroundColor(.white)
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 8)
                                    .background(Color.orange)
                                    .cornerRadius(8)
                            }
                            .buttonStyle(BorderlessButtonStyle()) // [Fix] Touch Separation
                        }
                    }
                    .padding(.vertical, 8)
                    
                    // [Recovery Tool] Tombstone Clear
                    Button(action: {
                        UserDefaults.standard.removeObject(forKey: "deleted_diary_ids")
                        UserDefaults.standard.removeObject(forKey: "deleted_diary_dates")
                        activeAlert = .info("🗑️ 차단 목록(Tombstone)이 초기화되었습니다.\n이제 서버에서 삭제된 일기도 다시 가져올 수 있습니다.")
                    }) {
                        Text("삭제/차단 기록 초기화 (Recover Deleted)")
                            .font(.caption)
                            .foregroundColor(.red)
                    }
                    .padding(.top, 4)
                    
                    // [New] Clean Today's Fake Data
                    Button(action: {
                        print("🧹 [Settings] Requesting cleanup...")
                        cleanTodayFakeData()
                    }) {
                        Text("🧹 오늘 가짜 데이터 청소 (Clean Today's Fake)")
                            .font(.caption)
                            .foregroundColor(.orange)
                    }
                    .padding(.top, 4)
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
                    .screenshotProtected(isProtected: false)
            }
            .sheet(isPresented: $showBirthDatePicker) {
                BirthDatePickerView(isPresented: $showBirthDatePicker)
            }
            .sheet(isPresented: $showMindBridgeMain) {
                MindBridgeMainView()
            }
    }
    
    // 이스터에그 함수
    func seedData() {
        DataSeeder.shared.seedDummyData { count in
            // [Test] 친구 데이터도 함께 생성
            DataSeeder.shared.seedDummyFriends()
            activeAlert = .info("테스트용 일기 \(count)개와\n가짜 친구(오늘 생일)가 생성되었습니다.\n앱을 재시작하거나 탭을 이동해보세요.")
        }
    }
    
    // [New] Clean Fake Data Logic
    func cleanTodayFakeData() {
        let today = Date()
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        // [Safety] 명시적으로 2026-02-11 등 타겟팅 가능하지만 일단 오늘 날짜
        let todayStr = formatter.string(from: today)
        
        // DataSeeder Patterns (Short Keywords)
        let fakePatterns = ["직장", "실수", "친구", "말다툼", "평범", "산책", "프로젝트", "성공"]
        
        let allDiaries = LocalDataManager.shared.diaries
        let todayDiaries = allDiaries.filter { $0.date == todayStr }
        
        // Filter & Delete
        var toDeleteIds: [String] = []
        for diary in todayDiaries {
            let content = (diary.event ?? "") + (diary.emotion_desc ?? "")
            for pattern in fakePatterns {
                if content.contains(pattern), let id = diary.id {
                    toDeleteIds.append(id)
                    break
                }
            }
        }
        
        if toDeleteIds.isEmpty {
            activeAlert = .info("🔍 검색 결과: 오늘(\(todayStr)) 작성된 일기 중\n'가짜 패턴'과 일치하는 항목이 없습니다.")
            return
        }
        
        // Count for alert
        let deleteCount = toDeleteIds.count
        
        print("🧹 Cleaning \(deleteCount) fake diaries...")
        
        for id in toDeleteIds {
            LocalDataManager.shared.deleteDiary(id: id) { _ in }
        }
        
        activeAlert = .info("✨ 청소 완료!\n오늘 작성된 가짜 일기 \(deleteCount)개를 삭제했습니다.\n(진짜 일기는 안전합니다)")
        
        // Refresh Stats
        NotificationCenter.default.post(name: NSNotification.Name("RefreshStats"), object: nil)
    }
}

// [New] Birth Date Picker View
struct BirthDatePickerView: View {
    @Binding var isPresented: Bool
    @EnvironmentObject var authManager: AuthManager
    
    @State private var selectedDate = Date()
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("생일 선택")) {
                    DatePicker("생년월일", selection: $selectedDate, displayedComponents: .date)
                        .datePickerStyle(.graphical)
                }
                
                Section {
                    Button(action: {
                        let formatter = DateFormatter()
                        formatter.dateFormat = "yyyy-MM-dd"
                        let dateStr = formatter.string(from: selectedDate)
                        
                        // Save & Close
                        authManager.updateBirthDate(dateStr) { success in
                            isPresented = false
                        }
                    }) {
                        HStack {
                            Spacer()
                            Text("저장하기")
                                .fontWeight(.bold)
                            Spacer()
                        }
                    }
                    .foregroundColor(.white)
                    .listRowBackground(Color.blue)
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
                    // Default to 1986-03-11 (User's Example) for convenience
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
