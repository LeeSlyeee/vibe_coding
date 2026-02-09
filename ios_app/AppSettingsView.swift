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
        NavigationView {
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
                                
                                // Switch to Custom Login
                                Button(action: {
                                    withAnimation { useCustomLogin = true }
                                }) {
                                    HStack {
                                        Image(systemName: "arrow.right.circle")
                                        Text("기존 웹(Web) 계정으로 로그인")
                                    }
                                    .font(.subheadline)
                                    .foregroundColor(.blue)
                                    .frame(maxWidth: .infinity)
                                }
                                .padding(.top, 4)
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
                                    
                                    // 2. Auth Check
                                    APIService.shared.ensureAuth { success in
                                        isLoggingIn = false
                                        if success {
                                            authManager.username = loginId // Update UI state if needed
                                            activeAlert = .info("로그인 성공! 이제 이 계정으로 동기화됩니다.")
                                        } else {
                                            activeAlert = .info("로그인 실패. 아이디/비밀번호를 확인하세요.")
                                            // Revert if failed? Maybe let them try again.
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
                                        .foregroundColor(.red)
                                        .padding(.horizontal, 10)
                                        .padding(.vertical, 5)
                                        .background(Color.red.opacity(0.1))
                                        .cornerRadius(6)
                                }
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
                                    b2gManager.syncData(force: true)
                                    activeAlert = .info("모든 데이터를 서버로 다시 전송합니다.\n(잠시 후 대시보드를 새로고침하세요)")
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
                                
                                // 2. Pull Data (Server -> App)
                                Button(action: {
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
                            Text("보건소/상담센터 연결하기")
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
                        
                    } else {
                        // Case B: 일반 사용자 (업그레이드 유도)
                        // 프리미엄 결제 여부와 상관없이 연동이 안되어 있으면 무조건 노출
                        Button(action: { showPremiumModal = true }) {
                            HStack {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text("마음챙김 플러스 +")
                                        .font(.headline)
                                        .fontWeight(.bold)
                                        .foregroundColor(.purple)
                                    Text("더 깊은 분석과 무제한 상담을 받아보세요.")
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
                        Text("Haru-on Team")
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
                }
                }
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
                PremiumModalView(isPresented: $showPremiumModal, onUpgrade: {
                     // Simple Mock Upgrade
                     DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                         authManager.setPremium(true)
                         showPremiumModal = false
                     }
                })
            }
        }
    }
    
    // 이스터에그 함수
    func seedData() {
        DataSeeder.shared.seedDummyData { count in
            activeAlert = .info("테스트용 일기 \(count)개가 생성되었습니다.\n캘린더와 통계 탭을 확인해보세요.")
        }
    }
}
