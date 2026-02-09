
import Foundation
import Combine

class ShareManager: NSObject, ObservableObject, URLSessionDelegate {
    static let shared = ShareManager()
    
    // API
    private let api = APIService.shared
    
    // State
    @Published var myCode: String = ""
    @Published var connectedUsers: [SharedUser] = [] // Me as Viewer (My Patients)
    @Published var myGuardians: [SharedUser] = []    // Me as Sharer (My Guardians)
    @Published var lastErrorMessage: String = ""     // [DEBUG] To show error on UI
    
    // Shared Stats Cache
    @Published var currentSharedStats: SharedStats?
    
    // Custom Session for SSL Bypass
    private lazy var session: URLSession = {
        let config = URLSessionConfiguration.default
        return URLSession(configuration: config, delegate: self, delegateQueue: nil)
    }()
    
    // Models
    struct SharedUser: Identifiable, Codable {
        let id: String
        let name: String
        let role: String? // 'sharer' or 'viewer'
        let connectedAt: String
        
        enum CodingKeys: String, CodingKey {
            case id
            case name
            case role
            case connectedAt = "connected_at"
        }
    }
    
    struct SharedStats: Codable {
        let userName: String
        let riskLevel: Int
        let latestReport: String
        let recentMoods: [DailyMood]
        let lastSync: String
        
        enum CodingKeys: String, CodingKey {
            case userName = "user_name"
            case riskLevel = "risk_level"
            case latestReport = "latest_report"
            case recentMoods = "recent_moods"
            case lastSync = "last_sync"
        }
    }
    
    struct DailyMood: Codable {
        let date: String
        let mood: Int
        let label: String
    }
    
    // Helper: Custom Request to 217 Server (where backend code is deployed)
    private func performShareRequest(endpoint: String, method: String, body: [String: Any]? = nil, completion: @escaping (Result<[String: Any], Error>) -> Void) {
        // [Important] Target the 217 Server (LLM Node) which has the Share Backend Code
        let baseURL = "https://217.142.253.35.nip.io/api/v1"
        guard let url = URL(string: baseURL + endpoint) else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Auth Token (Get from APIService / UserDefaults)
        if let token = UserDefaults.standard.string(forKey: "serverAuthToken") {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        if let body = body {
            request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        }
        
        print("🚀 [Share] \(method) \(url.absoluteString)")
        
        // Use 'self.session' instead of 'URLSession.shared' to apply SSL Bypass
        self.session.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data, let httpResponse = response as? HTTPURLResponse else {
                completion(.failure(NSError(domain: "Network", code: -1)))
                return
            }
            
            if !(200...299).contains(httpResponse.statusCode) {
                print("❌ [Share] Status: \(httpResponse.statusCode)")
                completion(.failure(NSError(domain: "HTTP", code: httpResponse.statusCode)))
                return
            }
            
            do {
                if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                    completion(.success(json))
                } else if let list = try JSONSerialization.jsonObject(with: data) as? [[String: Any]] {
                     completion(.success(["data": list])) // Wrap list
                } else {
                    completion(.failure(NSError(domain: "JSON", code: -1)))
                }
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    // URLSessionDelegate: Bypass SSL (Identify Server Trust)
    func urlSession(_ session: URLSession, didReceive challenge: URLAuthenticationChallenge, completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        if challenge.protectionSpace.authenticationMethod == NSURLAuthenticationMethodServerTrust {
            if let trust = challenge.protectionSpace.serverTrust {
                 completionHandler(.useCredential, URLCredential(trust: trust))
                 return
            }
        }
        completionHandler(.performDefaultHandling, nil)
    }
    
    // 1. Generate Code
    func generateCode(completion: @escaping (String?) -> Void) {
        // [BYPASS FIX] Send Identity explicitly in Body to bypass JWT Key Mismatch
        let defaults = UserDefaults.standard
        // If "userId" key is different in your app (e.g. "mongoId"), please verify. Using standard "userId"
        let userId = defaults.string(forKey: "userId") ?? "unknown_ios_user" 
        let userName = defaults.string(forKey: "userNickname") ?? "사용자"
        
        let body: [String: Any] = [
            "user_id": userId,
            "user_name": userName
        ]
        
        performShareRequest(endpoint: "/share/code", method: "POST", body: body) { result in
            DispatchQueue.main.async {
                switch result {
                case .success(let json):
                    if let code = json["code"] as? String {
                        self.myCode = code
                        completion(code)
                    } else {
                        completion(nil)
                    }
                case .failure(let err):
                    print("❌ Generate Code Failed: \(err)")
                    completion(nil)
                }
            }
        }
    }
    
    // 2. Connect (Viewer)
    func connectWithCode(_ code: String, completion: @escaping (Bool, String) -> Void) {
        let body = ["code": code]
        performShareRequest(endpoint: "/share/connect", method: "POST", body: body) { result in
            DispatchQueue.main.async {
                switch result {
                case .success(let json):
                    let msg = json["message"] as? String ?? "연결 성공"
                    self.fetchList() // Refresh List
                    completion(true, msg)
                case .failure(let err):
                    let errMsg = err.localizedDescription
                    completion(false, errMsg)
                }
            }
        }
    }
    
    // 3. List
    func fetchList(role: String = "viewer") {
        let defaults = UserDefaults.standard
        let userId = defaults.string(forKey: "userId") ?? "unknown_ios_user"
        
        self.lastErrorMessage = "" // Reset Error
        
        // GET Request with Explicit ID & Role
        let endpoint = "/share/list?user_id=\(userId)&role=\(role)"
        print("🚀 Fetching List: \(endpoint)")
        
        performShareRequest(endpoint: endpoint, method: "GET") { result in
            DispatchQueue.main.async {
                switch result {
                case .success(let json):
                    if let list = json["data"] as? [[String: Any]] {
                        do {
                            let data = try JSONSerialization.data(withJSONObject: list)
                            let users = try JSONDecoder().decode([SharedUser].self, from: data)
                            
                            // Save based on Role
                            if role == "viewer" {
                                self.connectedUsers = users
                            } else {
                                self.myGuardians = users
                            }
                            print("✅ Fetch Success: \(users.count) items")
                            
                        } catch {
                            print("❌ Parse List Failed: \(error)")
                            self.lastErrorMessage = "파싱 에러: \(error)"
                        }
                    } else {
                        self.lastErrorMessage = "데이터 형식 불일치 (data key missing)"
                    }
                case .failure(let err):
                    print("❌ Fetch List Failed: \(err)")
                    self.lastErrorMessage = "통신 에러: \(err.localizedDescription)"
                }
            }
        }
    }
    
    // 4. Disconnect (Added)
    func disconnect(targetId: String, completion: @escaping (Bool) -> Void) {
        let defaults = UserDefaults.standard
        let userId = defaults.string(forKey: "userId") ?? "unknown_ios_user"
        
        let body: [String: Any] = [
            "user_id": userId,
            "target_id": targetId
        ]
        
        performShareRequest(endpoint: "/share/disconnect", method: "POST", body: body) { result in
            DispatchQueue.main.async {
                switch result {
                case .success(_):
                    // Refresh Lists
                    self.fetchList(role: "sharer")
                    self.fetchList(role: "viewer")
                    completion(true)
                case .failure(let err):
                    print("❌ Disconnect Failed: \(err)")
                    completion(false)
                }
            }
        }
    }

    // 5. View Insights
    func fetchSharedStats(targetId: String, completion: @escaping (Bool) -> Void) {
        self.currentSharedStats = nil // Clear previous
        performShareRequest(endpoint: "/share/insights/\(targetId)", method: "GET") { result in
            DispatchQueue.main.async {
                switch result {
                case .success(let json):
                    do {
                        let data = try JSONSerialization.data(withJSONObject: json)
                        let stats = try JSONDecoder().decode(SharedStats.self, from: data)
                        self.currentSharedStats = stats
                        completion(true)
                    } catch {
                        print("❌ Parse Stats Failed: \(error)")
                        completion(false)
                    }
                case .failure(let err):
                    print("❌ Fetch Stats Failed: \(err)")
                    completion(false)
                }
            }
        }
    }

}
