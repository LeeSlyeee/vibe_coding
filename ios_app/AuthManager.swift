
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
    
    @Published var username: String? = nil {
        didSet {
            UserDefaults.standard.set(username, forKey: "authUsername")
        }
    }
    
    init() {
        self.token = UserDefaults.standard.string(forKey: "authToken")
        self.username = UserDefaults.standard.string(forKey: "authUsername")
        self.isAuthenticated = self.token != nil
        self.riskLevel = UserDefaults.standard.integer(forKey: "userRiskLevel")
        self.isPremium = UserDefaults.standard.bool(forKey: "userIsPremium")
        if self.riskLevel == 0 { self.riskLevel = 1 } // Default to 1
    }
    
    // 단순 토큰 설정 (기존)
    func login(token: String) {
        self.token = token
    }
    
    // 실제 서버 로그인 API 호출
    // 실제 서버 로그인 API 호출
    // 실제 서버 로그인 API 호출
    // 실제 서버 로그인 API 호출 (Auto-Register Logic Included)
    func performLogin(username: String, password: String, name: String? = nil, centerCode: String? = nil, completion: @escaping (Bool, String) -> Void) {
        // [Fix] Use HTTPS and Correct API V1 Endpoint
        let baseUrl = "https://150.230.7.76.nip.io/api/v1" 
        
        // 1. Attempt Login First
        let loginUrl = URL(string: "\(baseUrl)/auth/login/")!
        var request = URLRequest(url: loginUrl)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // [Fix] Add explicit ngrok skip header just in case
        request.setValue("true", forHTTPHeaderField: "ngrok-skip-browser-warning")
        
        let body: [String: Any] = ["username": username, "password": password]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        print("🔐 [Auth] Trying Login for \(username)...")
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
                // Login Success
                self.handleLoginResponse(data: data, username: username, completion: completion)
            } else {
                // Login Failed -> Try Registration
                print("⚠️ [Auth] Login Failed. Attempting Registration for \(username)...")
                self.performRegister(baseUrl: baseUrl, username: username, password: password, name: name, centerCode: centerCode, completion: completion)
            }
        }.resume()
    }
    
    private func performRegister(baseUrl: String, username: String, password: String, name: String?, centerCode: String?, completion: @escaping (Bool, String) -> Void) {
        let regUrl = URL(string: "\(baseUrl)/auth/register/")!
        var request = URLRequest(url: regUrl)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        var body: [String: Any] = [
            "username": username,
            "password": password,
            "email": "" // Optional but often required struct
        ]
        // Profile or extra fields handling depends on backend implementation
        
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let httpResponse = response as? HTTPURLResponse, (200...201).contains(httpResponse.statusCode) {
                // Register Success -> Retry Login
                print("✅ [Auth] Registration Success. Retrying Login...")
                // Retry Login (Recursion safe? Yes, because login will succeed or fail definitely)
                // But better to just call login-endpoint code block again usually.
                // For simplicity, I'll allow one level of retry by calling performLogin WITHOUT fallback?
                // Actually, just handle login token here if returned, or call login API again.
                // DJ-Rest-Auth often returns token on register usually.
                
                if let data = data, let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any], json["key"] != nil || json["access"] != nil {
                     self.handleLoginResponse(data: data, username: username, completion: completion)
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
    
    private func handleLoginResponse(data: Data?, username: String, completion: @escaping (Bool, String) -> Void) {
        guard let data = data,
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            DispatchQueue.main.async { completion(false, "응답 오류") }
            return
        }
        
        let token = (json["key"] as? String) ?? (json["access"] as? String) ?? (json["access_token"] as? String)
        
        if let token = token {
            DispatchQueue.main.async {
                self.token = token
                self.username = username
                self.isAuthenticated = true
                LocalDataManager.shared.syncWithServer()
                completion(true, "로그인 성공")
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
        self.isAuthenticated = false
        self.riskLevel = 1
        self.isPremium = false
        UserDefaults.standard.removeObject(forKey: "authToken")
        UserDefaults.standard.removeObject(forKey: "authUsername")
        UserDefaults.standard.removeObject(forKey: "userRiskLevel")
        UserDefaults.standard.removeObject(forKey: "userIsPremium")
    }
}
