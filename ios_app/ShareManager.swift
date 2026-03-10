
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
        let birthDate: String? // [New] Birth Date (YYYY-MM-DD)
        let connectedAt: String
        
        enum CodingKeys: String, CodingKey {
            case id
            case name
            case role
            case birthDate = "birth_date"
            case connectedAt = "connected_at"
        }
    }
    
    struct SharedStats: Codable {
        let sharerName: String
        let avgMood: Double?
        let hasSafetyConcern: Bool?
        let moodTrend: [DailyMood]
        let recentStatus: String
        let totalEntries: Int
        let writingStreak: Int
        let moodRestricted: Bool?
        let narrativeSummary: [String]?
        
        enum CodingKeys: String, CodingKey {
            case sharerName = "sharer_name"
            case avgMood = "avg_mood"
            case hasSafetyConcern = "has_safety_concern"
            case moodTrend = "mood_trend"
            case recentStatus = "recent_status"
            case totalEntries = "total_entries"
            case writingStreak = "writing_streak"
            case moodRestricted = "mood_restricted"
            case narrativeSummary = "narrative_summary"
        }
    }
    
    struct DailyMood: Codable {
        let date: String
        let mood: Int
    }
    
    private func performShareRequest(endpoint: String, method: String, body: [String: Any]? = nil, completion: @escaping (Result<[String: Any], Error>) -> Void) {
        // [Fix] Share API moved to /api/share/ (no v1 prefix)
        let baseURL = "https://217.142.253.35.nip.io/api"
        
        // [Standard] RFC 6750 Sec 2.3 & Custom Nginx: URI Query Parameter
        // APIService does this, so ShareManager should too for consistency.
        var components = URLComponents(string: baseURL + endpoint)
        
        // Auth Token (Get from APIService / UserDefaults)
        let token = UserDefaults.standard.string(forKey: "serverAuthToken")
        
        if let token = token {
            var items = components?.queryItems ?? []
            items.append(URLQueryItem(name: "jwt", value: token))
            components?.queryItems = items
        }
        
        guard let url = components?.url else {
            completion(.failure(NSError(domain: "Invalid URL", code: -1)))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let token = token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        if let body = body {
            request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        }
        
        
        
        // [Standardization] Use URLSession.shared for 217 Server (Official Cert)
        // SSL Bypass is no longer needed/recommended for nip.io with Let's Encrypt
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data, let httpResponse = response as? HTTPURLResponse else {
                completion(.failure(NSError(domain: "Network", code: -1)))
                return
            }
            
            if !(200...299).contains(httpResponse.statusCode) {
                // [Debug] Print Body
                if let str = String(data: data, encoding: .utf8) {
                }
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
        
        // [GEMINI Rule: No Silent Fallback] Verify identity strictly
        guard let userId = defaults.string(forKey: "userId"), !userId.isEmpty,
              let authUsername = defaults.string(forKey: "authUsername"), !authUsername.isEmpty else {
            let missing = (defaults.string(forKey: "userId") == nil) ? "userId" : "authUsername"
            self.lastErrorMessage = "로그인 정보 누락 (\(missing)). 재로그인 해주세요."
            completion(nil)
            return
        }
        
        let nickname = defaults.string(forKey: "userNickname") ?? "사용자"
        
        let body: [String: Any] = [
            "user_id": userId,
            "username": authUsername, // [Fix] Add explicit username
            "user_name": nickname
        ]
        
        // [Fix] Remove trailing slash
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
                    completion(nil)
                }
            }
        }
    }
    
    // 2. Connect (Viewer)
    func connectWithCode(_ code: String, completion: @escaping (Bool, String) -> Void) {
        let body = ["code": code]
        // [Fix] Remove trailing slash
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
        
        // [GEMINI Rule: No Silent Fallback]
        guard let userId = defaults.string(forKey: "userId"), !userId.isEmpty else {
            self.lastErrorMessage = "사용자 정보를 불러올 수 없습니다."
            return
        }
        let username = defaults.string(forKey: "authUsername") ?? ""
        
        self.lastErrorMessage = "" // Reset Error
        
        // GET Request with Explicit ID & Role
        // [Fix] Include username query param for robustness. Use percent encoding for safe URL.
        let encodedUsername = username.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? username
        let endpoint = "/share/list?user_id=\(userId)&username=\(encodedUsername)&role=\(role)"
        
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
                            
                        } catch {
                            self.lastErrorMessage = "파싱 에러: \(error)"
                        }
                    } else {
                        self.lastErrorMessage = "데이터 형식 불일치 (data key missing)"
                    }
                case .failure(let err):
                    self.lastErrorMessage = "통신 에러: \(err.localizedDescription)"
                }
            }
        }
    }
    
    // 4. Disconnect (Added)
    func disconnect(targetId: String, completion: @escaping (Bool) -> Void) {
        let defaults = UserDefaults.standard
        
        // [GEMINI Rule: No Silent Fallback]
        guard let userId = defaults.string(forKey: "userId"), !userId.isEmpty else {
            completion(false)
            return
        }
        let username = defaults.string(forKey: "authUsername") ?? ""
        
        let body: [String: Any] = [
            "user_id": userId,
            "username": username, // [Fix] Add explicit username
            "target_id": targetId
        ]
        
        // [Fix] Remove trailing slash
        performShareRequest(endpoint: "/share/disconnect", method: "POST", body: body) { result in
            DispatchQueue.main.async {
                switch result {
                case .success(_):
                    // Refresh Lists
                    self.fetchList(role: "sharer")
                    self.fetchList(role: "viewer")
                    completion(true)
                case .failure(let err):
                    completion(false)
                }
            }
        }
    }
    
    // 5. View Insights
    func fetchSharedStats(targetId: String, completion: @escaping (Bool) -> Void) {
        self.currentSharedStats = nil // Clear previous
        // [Fix] Remove trailing slash
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
                        completion(false)
                    }
                case .failure(let err):
                    completion(false)
                }
            }
        }
    }
    // 6. Check Friend Birthdays
    // 6. Check Friend Birthdays (Today + Upcoming 7 Days)
    func checkFriendBirthdays() -> [(name: String, dDay: Int)] {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        let today = Date()
        let cal = Calendar.current
        
        // Remove time component for accurate comparison
        let currentDay = cal.startOfDay(for: today)
        let currentYear = cal.component(.year, from: currentDay)
        
        var upcomingBirthdays: [(name: String, dDay: Int)] = []
        var processedIDs: Set<String> = [] // Avoid duplicates
        
        let allFriends = connectedUsers + myGuardians
        
        for user in allFriends {
            if processedIDs.contains(user.id) { continue }
            
            if let bString = user.birthDate, let birthDate = f.date(from: bString) {
                let month = cal.component(.month, from: birthDate)
                let day = cal.component(.day, from: birthDate)
                
                // Create this year's birthday
                var components = DateComponents()
                components.year = currentYear
                components.month = month
                components.day = day
                
                guard let thisYearBirthday = cal.date(from: components) else { continue }
                
                // Calculate difference
                let diffComponents = cal.dateComponents([.day], from: currentDay, to: thisYearBirthday)
                
                if let days = diffComponents.day {
                    if days >= 0 && days <= 7 {
                        upcomingBirthdays.append((name: user.name, dDay: days))
                        processedIDs.insert(user.id)
                    } else if days < 0 {
                         // Check next year (e.g. Dec 31 vs Jan 1) if needed, 
                         // but for "Birthday Week" usually means upcoming. 
                         // If today is Jan 1 and birthday was Dec 31, it's passed.
                         // Only edge case: Today is Dec 28, Birthday is Jan 2. 
                         // Then thisYearBirthday (Jan 2 2026) is passed? No wait.
                         // If today is Dec, and birthday is Jan, currentYear Jan has passed. 
                         // Need to check next year.
                         
                         var nextComponents = components
                         nextComponents.year = currentYear + 1
                         if let nextYearBirthday = cal.date(from: nextComponents),
                            let nextDays = cal.dateComponents([.day], from: currentDay, to: nextYearBirthday).day,
                            nextDays >= 0 && nextDays <= 7 {
                             upcomingBirthdays.append((name: user.name, dDay: nextDays))
                             processedIDs.insert(user.id)
                         }
                    }
                }
            }
        }
        
        return upcomingBirthdays.sorted { $0.dDay < $1.dDay }
    }
    
    // MARK: - Guardian Alert Model
    struct GuardianAlert: Identifiable, Codable {
        var id: String { "\(type)_\(sharerId)" }
        let type: String           // "crisis", "mood_drop", "inactivity"
        let sharerId: Int
        let sharerName: String
        let message: String
        let severity: String       // "high", "medium", "low"
        let icon: String // Revert systemIcon -> icon
        let actionGuide: [String]?
        let avgMood: Double?
        
        enum CodingKeys: String, CodingKey {
            case type
            case sharerId = "sharer_id"
            case sharerName = "sharer_name"
            case message
            case severity
            case icon
            case actionGuide = "action_guide"
            case avgMood = "avg_mood"
        }
    }
    
    @Published var guardianAlerts: [GuardianAlert] = []
    
    // 8. Fetch Guardian Alerts (보호자 알림 이력 조회)
    func fetchGuardianAlerts() {
        performShareRequest(endpoint: "/share/guardian-alerts", method: "GET") { result in
            DispatchQueue.main.async {
                switch result {
                case .success(let json):
                    if let alertsArray = json["alerts"] as? [[String: Any]] {
                        do {
                            let data = try JSONSerialization.data(withJSONObject: alertsArray)
                            let alerts = try JSONDecoder().decode([GuardianAlert].self, from: data)
                            self.guardianAlerts = alerts
                        } catch {
                        }
                    }
                case .failure(_):
                    break
                }
            }
        }
    }
    
    // 7. Update Share Scope (내담자가 보호자에게 공유할 데이터 범위 설정)
    func updateShareScope(viewerId: String, shareMood: Bool? = nil, shareReport: Bool? = nil, shareCrisis: Bool? = nil, completion: @escaping (Bool) -> Void) {
        var body: [String: Any] = ["viewer_id": viewerId]
        if let v = shareMood { body["share_mood"] = v }
        if let v = shareReport { body["share_report"] = v }
        if let v = shareCrisis { body["share_crisis"] = v }
        
        performShareRequest(endpoint: "/share/share-scope", method: "PUT", body: body) { result in
            DispatchQueue.main.async {
                switch result {
                case .success(_):
                    completion(true)
                case .failure(let err):
                    completion(false)
                }
            }
        }
    }
}
