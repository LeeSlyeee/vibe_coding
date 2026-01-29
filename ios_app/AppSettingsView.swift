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
                        // 로그인 안 된 상태 (On-Device Mode)
                        VStack(alignment: .leading, spacing: 12) {
                            HStack {
                                Image(systemName: "person.crop.circle.badge.exclamationmark")
                                    .font(.largeTitle)
                                    .foregroundColor(.gray)
                                VStack(alignment: .leading) {
                                    Text("로컬 프로필")
                                        .font(.headline)
                                    Text("로그인하면 웹과 데이터를 동기화합니다.")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                            }
                            
                            // 로그인 폼
                            VStack(spacing: 12) {
                                TextField("아이디", text: $loginId)
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                                    .textInputAutocapitalization(.none)
                                
                                SecureField("비밀번호", text: $loginPw)
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                                
                                Button(action: {
                                    isLoggingIn = true
                                    authManager.performLogin(username: loginId, password: loginPw) { success, msg in
                                        isLoggingIn = false
                                        alertMessage = msg
                                        showAlert = true
                                        if success { 
                                            loginPw = "" 
                                            // 로그인 성공 시, 이미 B2G 연동되어 있다면 데이터 동기화 시도
                                            if b2gManager.isLinked {
                                                b2gManager.syncData()
                                            }
                                        }
                                    }
                                }) {
                                    HStack {
                                        if isLoggingIn { ProgressView().padding(.trailing, 5) }
                                        Text("로그인 및 동기화")
                                    }
                                    .frame(maxWidth: .infinity)
                                    .padding()
                                    .background(Color.accent)
                                    .foregroundColor(.white)
                                    .cornerRadius(10)
                                }
                                .disabled(loginId.isEmpty || loginPw.isEmpty || isLoggingIn)
                            }
                            .padding(.top, 8)
                        }
                        .padding(.vertical, 8)
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
                            }
                            
                            if b2gManager.lastSyncDate > 0 {
                                Text("마지막 전송: \(Date(timeIntervalSince1970: b2gManager.lastSyncDate).formatted())")
                                    .font(.caption2)
                                    .foregroundColor(.gray)
                            }
                            
                            HStack(spacing: 20) {
                                Button(action: {
                                    b2gManager.syncData()
                                    alertMessage = "모든 데이터를 서버로 다시 전송합니다.\n(잠시 후 대시보드를 새로고침하세요)"
                                    showAlert = true
                                }) {
                                    HStack {
                                        Image(systemName: "arrow.triangle.2.circlepath")
                                        Text("데이터 강제 전송 (Force Sync)")
                                            .fontWeight(.bold)
                                    }
                                    .padding()
                                    .background(Color.blue.opacity(0.1))
                                    .cornerRadius(8)
                                }
                                
                                Button(action: {
                                    b2gManager.disconnect()
                                }) {
                                    Text("연동 해제")
                                        .foregroundColor(.red)
                                        .font(.caption)
                                }
                            }
                            .padding(.top, 4)
                            
                            Text("* 대시보드에 데이터가 뜨지 않으면 위 버튼을 누르세요.")
                                .font(.caption2)
                                .foregroundColor(.orange)
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
                                    .textFieldStyle(RoundedBorderTextFieldStyle())
                                    #if os(iOS)
                                    .textInputAutocapitalization(.characters)
                                    #endif
                                
                                Button(action: {
                                    b2gManager.connect(code: inputCode) { success, message in
                                        alertMessage = message
                                        showAlert = true
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
                
                // Section 3: 앱 정보
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
                                                        // B2GManager 상태 강제 동기화
                                                        b2gManager.centerCode = tempInputCode.uppercased()
                                                        b2gManager.isLinked = true
                                                        alertMessage = "✅ 강제 연동 성공!\n코드: \(tempInputCode.uppercased())"
                                                        tempInputCode = ""
                                                    } else {
                                                        alertMessage = "❌ 기관 연결(Connect) API 실패"
                                                    }
                                                    showAlert = true
                                                }
                                            }
                                        } else {
                                            DispatchQueue.main.async {
                                                alertMessage = "⚠️ 센터 ID를 찾을 수 없습니다 (응답 데이터 오류)."
                                                showAlert = true
                                            }
                                        }
                                    case .failure(let err):
                                        DispatchQueue.main.async {
                                            alertMessage = "❌ 오류 발생 (재빌드 필요?)\n\(err.localizedDescription)"
                                            showAlert = true
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
                }
            }
            .navigationTitle("설정")
            .alert(isPresented: $showAlert) {
                Alert(title: Text("알림"), message: Text(alertMessage), dismissButton: .default(Text("확인")))
            }
        }
    }
    
    // 이스터에그 함수
    func seedData() {
        DataSeeder.shared.seedDummyData { count in
            alertMessage = "테스트용 일기 \(count)개가 생성되었습니다.\n캘린더와 통계 탭을 확인해보세요."
            showAlert = true
        }
    }
}
