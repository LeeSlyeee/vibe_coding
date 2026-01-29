
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
    func performLogin(username: String, password: String, name: String? = nil, completion: @escaping (Bool, String) -> Void) {
        // [SSH Tunnel] 외부 접속용 URL 사용 (로컬 네트워크 권한 우회)
        guard let url = URL(string: "https://ccf4cf0857dd08.lhr.life/api/login") else {
            completion(false, "잘못된 URL")
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        var body: [String: Any] = [
            "username": username,
            "password": password
        ]
        if let name = name, !name.isEmpty {
            body["name"] = name
        }
        
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                DispatchQueue.main.async { completion(false, error.localizedDescription) }
                return
            }
            
            guard let httpResponse = response as? HTTPURLResponse, (200...299).contains(httpResponse.statusCode),
                  let data = data else {
                DispatchQueue.main.async { completion(false, "로그인 실패: 아이디 또는 비밀번호를 확인하세요.") }
                return
            }
            
            // 토큰 파싱 (key, token, access 등 백엔드 응답 구조에 맞춤. dj-rest-auth는 'key'를 줌)
            // 하지만 백엔드 응답을 확인해봐야 함. 보통 {'key': '...'} 또는 {'access': '...'}
            // 여기선 일단 key, token, access_token 다 찾아봄.
            do {
                if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                    // 백엔드가 주는 키: access_token
                    let receivedToken = (json["key"] as? String) 
                        ?? (json["token"] as? String) 
                        ?? (json["access"] as? String)
                        ?? (json["access_token"] as? String) // Flask-JWT-Extended
                    
                    if let token = receivedToken {
                        DispatchQueue.main.async {
                            self.token = token
                            self.username = username
                            self.isAuthenticated = true
                            completion(true, "로그인 성공")
                        }
                    } else {
                        DispatchQueue.main.async { completion(false, "토큰 파싱 실패") }
                    }
                }
            } catch {
                DispatchQueue.main.async { completion(false, "응답 처리 오류") }
            }
        }.resume()
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
