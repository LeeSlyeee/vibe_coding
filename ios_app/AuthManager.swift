
import Foundation
import Combine

class AuthManager: ObservableObject {
    @Published var isAuthenticated: Bool = false
    @Published var token: String? {
        didSet {
            UserDefaults.standard.set(token, forKey: "authToken")
            // APIService와 동기화
            UserDefaults.standard.set(token, forKey: "serverAuthToken")
            isAuthenticated = token != nil
        }
    }
    
    @Published var riskLevel: Int = 1 {
        didSet {
            UserDefaults.standard.set(riskLevel, forKey: "userRiskLevel")
        }
    }

    @Published var isPremium: Bool = false {
        didSet {
            UserDefaults.standard.set(isPremium, forKey: "userIsPremium")
        }
    }
    
    @Published var username: String? {
        didSet {
            UserDefaults.standard.set(username, forKey: "authUsername")
        }
    }
    
    @Published var birthDate: String? = nil {
        didSet {
            UserDefaults.standard.set(birthDate, forKey: "userBirthDate")
        }
    }
    
    init() {
        self.token = UserDefaults.standard.string(forKey: "authToken")
        self.username = UserDefaults.standard.string(forKey: "authUsername")
        self.birthDate = UserDefaults.standard.string(forKey: "userBirthDate")
        
        self.isAuthenticated = self.token != nil
        
        self.riskLevel = UserDefaults.standard.integer(forKey: "userRiskLevel")
        self.isPremium = UserDefaults.standard.bool(forKey: "userIsPremium")
        if self.riskLevel == 0 { self.riskLevel = 1 } // Default to 1
        
        // [Fix] userId가 없으면 JWT에서 추출 (자동 로그인 시 userId 누락 방지)
        if isAuthenticated, UserDefaults.standard.string(forKey: "userId") == nil,
           let savedToken = self.token {
            if let jwtId = APIService.shared.decodeUserIdFromJWT(token: savedToken) {
                UserDefaults.standard.set(jwtId, forKey: "userId")
            }
        }
        
        // [Standard Architecture] 
        // Single Source of Truth: 'authUsername'. No more 'app_username'.
        if isAuthenticated && (self.username == nil || self.username!.isEmpty) {
            // Trigger emergency fetch
            Task {
                APIService.shared.syncUserInfo { success in
                   if success, let recoveredName = UserDefaults.standard.string(forKey: "userId") {
                       DispatchQueue.main.async {
                           self.username = recoveredName // Updates 'authUsername' automatically
                       }
                   }
                }
            }
        }
    }
    
    // [New] Update Birth Date
    func updateBirthDate(_ dateStr: String, completion: @escaping (Bool) -> Void) {
        APIService.shared.updateProfile(nickname: nil, birthDate: dateStr) { success in
            if success {
                DispatchQueue.main.async {
                    self.birthDate = dateStr
                }
            }
            completion(success)
        }
    }
    
    // 단순 토큰 설정 (기존)
    func login(token: String) {
        self.token = token
    }
    
    // 실제 서버 로그인 API 호출
    // 실제 서버 로그인 API 호출 (Auto-Register Logic Included)
    // 실제 서버 로그인 API 호출 (Auto-Register Logic Included)
    func performLogin(username: String, password: String, name: String? = nil, centerCode: String? = nil, completion: @escaping (Bool, String) -> Void) {
        // [Architecture] URL 단일 진실 공급원: APIService.swift > ServerConfig
        // ⚠️ 서버 주소 변경은 APIService.swift 의 ServerConfig.productionHost 만 수정
        let baseUrl = ServerConfig.apiBase

        // 1. Attempt Login First
        let loginUrl = URL(string: "\(baseUrl)/login")!
        var request = URLRequest(url: loginUrl)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // [Fix] Add explicit ngrok skip header just in case
        request.setValue("true", forHTTPHeaderField: "ngrok-skip-browser-warning")
        
        let body: [String: Any] = ["username": username, "password": password]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
                // Login Success
                // [Fix] 비밀번호 안전하게 저장 (ensureAuth 토큰 갱신에 필요)
                KeychainHelper.standard.saveString(password, account: "app_password")
                self.handleLoginResponse(data: data, username: username, centerCode: centerCode, completion: completion)
            } else {
                // Login Failed -> Try Registration
                self.performRegister(baseUrl: baseUrl, username: username, password: password, name: name, centerCode: centerCode, completion: completion)
            }
        }.resume()
    }
    
    private func performRegister(baseUrl: String, username: String, password: String, name: String?, centerCode: String?, completion: @escaping (Bool, String) -> Void) {
        let regUrl = URL(string: "\(baseUrl)/register")!
        var request = URLRequest(url: regUrl)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        var body: [String: Any] = [
            "username": username,
            "password": password,
            "email": "",
            "name": name ?? "", // [Fix] Send Real Name
            "center_code": centerCode ?? "" // [Fix] Send Center Code
        ]
        // Profile or extra fields handling depends on backend implementation
        
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let httpResponse = response as? HTTPURLResponse, (200...201).contains(httpResponse.statusCode) {
                // Register Success -> Retry Login
                // Retry Login (Recursion safe? Yes, because login will succeed or fail definitely)
                // But better to just call login-endpoint code block again usually.
                // For simplicity, I'll allow one level of retry by calling performLogin WITHOUT fallback?
                // Actually, just handle login token here if returned, or call login API again.
                // DJ-Rest-Auth often returns token on register usually.
                
                if let data = data, let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any], json["key"] != nil || json["access"] != nil {
                     self.handleLoginResponse(data: data, username: username, centerCode: centerCode, completion: completion)
                } else {
                    // Call Login Explicitly
                    // Recurse? We need to be careful of infinite loop if logic logic is flawed.
                    // But here we are in 'performRegister'.
                    // Let's just manually call login URL logic again.
                    self.performLogin(username: username, password: password, name: name, centerCode: centerCode, completion: completion)
                }
            } else {
                // Register Failed
                let msg = "로그인 및 가입 실패. 아이디/비밀번호를 확인하거나 다른 아이디를 사용하세요."
                DispatchQueue.main.async { completion(false, msg) }
            }
        }.resume()
    }
    
    private func handleLoginResponse(data: Data?, username: String, centerCode: String? = nil, completion: @escaping (Bool, String) -> Void) {
        guard let data = data,
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            DispatchQueue.main.async { completion(false, "응답 오류") }
            return
        }
        
        let token = (json["key"] as? String) ?? (json["access"] as? String) ?? (json["access_token"] as? String)
        
        if let token = token {
            // [Critical Logic]
            // UI 전환(isAuthenticated=true) 전에 B2G 연동 상태를 먼저 확정지어야 함.
            // 1. 토큰을 조용히 저장 (APIService가 사용할 수 있도록)
            UserDefaults.standard.set(token, forKey: "serverAuthToken")
            
            // [Fix] userId 저장 — 서버 응답에서 추출
            if let user = json["user"] as? [String: Any] {
                if let uid = user["id"] as? Int {
                    UserDefaults.standard.set(String(uid), forKey: "userId")
                } else if let uid = user["id"] as? String {
                    UserDefaults.standard.set(uid, forKey: "userId")
                }
                if let nickname = user["nickname"] as? String {
                    UserDefaults.standard.set(nickname, forKey: "userNickname")
                }
                if let realName = user["real_name"] as? String {
                    UserDefaults.standard.set(realName, forKey: "realName")
                }
            }
            // JWT fallback — response body에 user 객체가 없는 경우
            if UserDefaults.standard.string(forKey: "userId") == nil {
                if let jwtId = APIService.shared.decodeUserIdFromJWT(token: token) {
                    UserDefaults.standard.set(jwtId, forKey: "userId")
                }
            }
            
            // 2. 연동 코드 확인 (User Input > Server Response)
            let inputCode = centerCode
            let serverCode = json["center_code"] as? String ?? json["linked_center_code"] as? String
            
            let codeToLink = (inputCode?.isEmpty == false) ? inputCode! : (serverCode ?? "")
            
            if !codeToLink.isEmpty {
                B2GManager.shared.connect(code: codeToLink) { success, msg in
                    DispatchQueue.main.async {
                        // 결과와 상관없이 로그인은 성공 처리 (연동 실패했다고 로그인 막으면 안됨)
                        // 단, 성공 시 isLinked가 true가 되어 PHQ-9 스킵됨.
                        if success {
                             // [New] 연동 성공 시, 서버 데이터를 즉시 가져옴 (Auto-Restore)
                             B2GManager.shared.syncData(force: true)
                        } else {
                        }
                        
                        // 3. Finalize Login (Trigger UI)
                        // [Critical Fix] Save username to "authUsername" (Single Source of Truth)
                        UserDefaults.standard.set(username, forKey: "authUsername")
                        self.username = username
                        
                        self.token = token // This triggers isAuthenticated = true
                        
                        LocalDataManager.shared.syncWithServer()
                        completion(true, "로그인 성공")
                    }
                }
            } else {
                // 연동 코드 없음 -> 바로 진입
                DispatchQueue.main.async {
                    // [Critical Fix] Save username to "authUsername" (Single Source of Truth)
                    UserDefaults.standard.set(username, forKey: "authUsername")
                    self.username = username
                    
                    self.token = token
                    
                    LocalDataManager.shared.syncWithServer()
                    completion(true, "로그인 성공")
                }
            }
        } else {
            DispatchQueue.main.async { completion(false, "토큰 없음") }
        }
    }
    
    func setRiskLevel(_ level: Int) {
        self.riskLevel = level
    }
    
    func setPremium(_ status: Bool) {
        self.isPremium = status
    }
    
    func logout() {
        self.token = nil
        self.username = nil
        self.birthDate = nil
        self.isAuthenticated = false
        self.riskLevel = 1
        self.isPremium = false
        
        // [Fix] 모든 인증/프로필 관련 UserDefaults 완전 정리
        let keysToRemove = [
            "authToken", "authUsername", "userRiskLevel", "userIsPremium",
            "serverAuthToken", "userId", "realName",
            "userNickname", "userBirthDate", "app_username",
            "hasCompletedAssessment"
        ]
        for key in keysToRemove {
            UserDefaults.standard.removeObject(forKey: key)
        }
        
        // [Fix] Keychain에서도 비밀번호 정리
        KeychainHelper.standard.deleteString(account: "app_password")
    }
}
