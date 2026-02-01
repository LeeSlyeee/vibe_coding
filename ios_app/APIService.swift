
import Foundation
import Combine

class APIService: NSObject {
    static let shared = APIService()
    
    // OCI Production Server (Main Backend)
    private let baseURL = "https://150.230.7.76.nip.io/api/v1"
    
    // [Target Fix] Dedicated LLM Node (217.142...)
    // 채팅 및 AI 기능은 이 주소를 타겟으로 함 (User Specified)
    private let llmServerURL = "https://217.142.253.35.nip.io/api/v1"
    
    private var token: String? {
        get { UserDefaults.standard.string(forKey: "serverAuthToken") }
        set { UserDefaults.standard.set(newValue, forKey: "serverAuthToken") }
    }
    
    private override init() {
        super.init()
    }
    
    // MARK: - Auth
    func ensureAuth(completion: @escaping (Bool) -> Void) {
        // [Auth - Unique Identity]
        // 1. Get or Generate Username
        var username = UserDefaults.standard.string(forKey: "app_username")
        if username == nil {
            // Generate unique ID: "user_" + Random 6 chars
            let randomStr = String(UUID().uuidString.prefix(6)).lowercased()
            username = "user_\(randomStr)"
            UserDefaults.standard.set(username, forKey: "app_username")
            // Also set nickname for display
            if UserDefaults.standard.string(forKey: "userNickname") == nil {
                 UserDefaults.standard.set("User \(randomStr)", forKey: "userNickname")
            }
        }
        
        // 2. Get or Generate Password
        var password = UserDefaults.standard.string(forKey: "app_password")
        if password == nil {
            // Generate random password
            password = String(UUID().uuidString.prefix(8))
            UserDefaults.standard.set(password, forKey: "app_password")
        }
        
        let body: [String: Any] = ["username": username!, "password": password!]
        
        print("🔐 [API-OCI] Attempting Auth for: '\(username!)' (PW: \(password!))")
        
        // Token Existence Check (Optional optimization)
        // if token != nil { completion(true); return }
        
        performRequest(endpoint: "/auth/login/", method: "POST", body: body, requiresAuth: false) { result in
            switch result {
            case .success(let response):
                if let accessToken = response["access"] as? String { // JWT returns 'access' not 'access_token' usually
                    self.token = accessToken
                    
                    // [Name Sync] 로그인 시 실명 정보 저장
                    if let rName = response["name"] as? String, !rName.isEmpty {
                        UserDefaults.standard.set(rName, forKey: "realName")
                    }
                    
                    print("🌐 [API] OCI Login Success: \(username!)")
                    completion(true)
                } else if let accessToken = response["access_token"] as? String {
                     self.token = accessToken
                     
                     // [Name Sync] 로그인 시 실명 정보 저장
                     if let rName = response["name"] as? String, !rName.isEmpty {
                         UserDefaults.standard.set(rName, forKey: "realName")
                     }
                     
                     print("🌐 [API] OCI Login Success: \(username!)")
                     completion(true)
                } else {
                    completion(false)
                }
             case .failure:
                print("🌐 [API-OCI] Login failed, trying registration for: \(username!)")
                // 회원가입 시도
                self.performRequest(endpoint: "/auth/register/", method: "POST", body: body, requiresAuth: false) { regResult in
                    switch regResult {
                    case .success:
                         self.performRequest(endpoint: "/auth/login/", method: "POST", body: body, requiresAuth: false) { loginRetry in
                            if case .success(let retryResp) = loginRetry,
                               let accessToken = retryResp["access_token"] as? String {
                                self.token = accessToken
                                completion(true)
                            } else {
                                completion(false)
                            }
                         }
                    case .failure(let err):
                        print("🌐 [API-OCI] Registration failed: \(err)")
                        completion(false)
                    }
                }
            }
        }
    }
    
    // [New] User Info Sync without Re-login
    // [New] User Info Sync without Re-login (Targets 217 Server)
    func syncUserInfo(completion: @escaping (Bool) -> Void) {
        let urlStr = self.llmServerURL + "/auth/me"
        guard let url = URL(string: urlStr) else { completion(false); return }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = 10.0
        
        if let token = self.token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        print("🚀 [API-217] Syncing User Info: \(urlStr)")
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("⚠️ [API-217] Sync Failed: \(error.localizedDescription)")
                completion(false)
                return
            }
            
            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                completion(false)
                return
            }
            
            // Success Logic
            if let name = json["name"] as? String, !name.isEmpty {
                UserDefaults.standard.set(name, forKey: "realName")
                print("✅ [API-217] Real Name Synced: \(name)")
            }
            if let nickname = json["nickname"] as? String, !nickname.isEmpty {
                UserDefaults.standard.set(nickname, forKey: "userNickname")
            }
            completion(true)
        }.resume()
    }
    
    // MARK: - Diary Sync
    
    // Unified Sync Method
    // Unified Sync Method
    func syncDiary(_ diary: Diary, completion: @escaping (Bool) -> Void = { _ in }) {
        ensureAuth { success in
            guard success else { completion(false); return }
            let dateStr = diary.date ?? ""
            
            // 1. Check existence by Date
            self.performRequest(endpoint: "/diaries/date/\(dateStr)/", method: "GET") { result in
                switch result {
                case .success(let data):
                    // Found -> Update (PUT)
                    if let id = data["id"] as? Int {
                        self.updateDiaryOnServer(diaryId: String(id), diary: diary, completion: completion)
                    } else if let id = data["id"] as? String {
                        self.updateDiaryOnServer(diaryId: id, diary: diary, completion: completion)
                    } else {
                         completion(false)
                    }
                case .failure:
                    // Not Found -> Create (POST)
                    self.createDiaryOnServer(diary, completion: completion)
                }
            }
        }
    }

    private func createDiaryOnServer(_ diary: Diary, completion: @escaping (Bool) -> Void) {
        let payload = buildDiaryPayload(diary)
        print("🚀 [API] Creating New Diary: \(diary.date ?? "")")
        print("📦 [API] Payload Keys: \(payload.keys)")
        
        performRequest(endpoint: "/diaries/", method: "POST", body: payload) { result in
            switch result {
            case .success(let data):
                print("✅ [API] Diary Created. ID: \(data["id"] ?? "null")")
                completion(true)
            case .failure(let error):
                print("❌ [API] Create Failed: \(error.localizedDescription)")
                completion(false)
            }
        }
    }
    
    private func updateDiaryOnServer(diaryId: String, diary: Diary, completion: @escaping (Bool) -> Void) {
        let payload = buildDiaryPayload(diary)
        print("🚀 [API] Updating Diary ID: \(diaryId)")
        
        performRequest(endpoint: "/diaries/\(diaryId)/", method: "PUT", body: payload) { result in
            switch result {
            case .success:
                print("✅ [API] Diary Updated.")
                completion(true)
            case .failure(let error):
                let nsError = error as NSError
                if nsError.code == 404 {
                     print("⚠️ [API] Update Failed (404). Trying Create instead...")
                     self.createDiaryOnServer(diary, completion: completion)
                } else {
                    print("❌ [API] Update Failed: \(error.localizedDescription)")
                    completion(false)
                }
            }
        }
    }
    

    
    private func buildDiaryPayload(_ diary: Diary) -> [String: Any] {
        // Pack metadata and AI results into analysis_result JSON
        let analysisData: [String: Any] = [
            "weather": diary.weather ?? "",
            "sleep_condition": diary.sleep_desc ?? "",
            "emotion_desc": diary.emotion_desc ?? "",
            "emotion_meaning": diary.emotion_meaning ?? "",
            "self_talk": diary.self_talk ?? "",
            "ai_comment": diary.ai_comment ?? "",
            "ai_advice": diary.ai_advice ?? "",
            "ai_analysis": diary.ai_analysis ?? "",
            "ai_prediction": diary.ai_prediction ?? ""
        ]
        
        // Prefer full ISO timestamp, fallback to date string
        let createdAt = diary.created_at ?? diary.date ?? ""
        
        return [
            "created_at": createdAt,
            "content": diary.event ?? "", // Main content
            "mood_score": diary.mood_level,
            "analysis_result": analysisData
        ]
    }
    
    // Legacy support (Deprecated)
    func saveDiaryInitial(_ diary: Diary) { syncDiary(diary) }
    func updateDiaryAnalysis(_ diary: Diary) { syncDiary(diary) }
    
    // MARK: - B2G Data Sync (Push)
    func syncCenterData(payload: [String: Any], completion: @escaping (Bool, String?) -> Void) {
        // Updated endpoint path
        performRequest(endpoint: "/centers/sync-data/", method: "POST", body: payload, requiresAuth: false) { result in
            switch result {
            case .success(let json):
                if let success = json["success"] as? Bool, success == true { 
                    completion(true, nil)
                } else if let message = json["message"] as? String, message.contains("Data synced") {
                     // [Fix] Backend returns message, not success bool
                     completion(true, nil)
                } else {
                    let msg = json["error"] as? String ?? json["message"] as? String ?? "Sync Failed"
                    completion(false, msg)
                }
            case .failure(let error):
                completion(false, error.localizedDescription)
            }
        }
    }
    
    func verifyCenterCode(_ code: String, completion: @escaping (Result<[String: Any], Error>) -> Void) {
        let nickname = UserDefaults.standard.string(forKey: "userNickname") ?? "Guest"
        let payload = ["code": code, "user_nickname": nickname]
        performRequest(endpoint: "/centers/verify-code/", method: "POST", body: payload, requiresAuth: false, completion: completion)
    }
    
    func connectToCenter(centerId: Any, completion: @escaping (Bool) -> Void) {
        ensureAuth { success in
            guard success else { completion(false); return }
            var payload: [String: Any] = [:]
            if let idInt = centerId as? Int { payload["center_id"] = idInt }
            else if let idStr = centerId as? String { payload["center_id"] = idStr }
            
            self.performRequest(endpoint: "/centers/connect/", method: "POST", body: payload) { result in
                if case .success = result { completion(true) } else { completion(false) }
            }
        }
    }
    
    func fetchDiaries(completion: @escaping ([ [String: Any] ]?) -> Void) {
        ensureAuth { success in
            guard success else { completion(nil); return }
            self.performRequestList(endpoint: "/diaries/", method: "GET") { result in
                if case .success(let list) = result { completion(list) } else { completion(nil) }
            }
        }
    }
    
    // MARK: - Diary CRUD
    func deleteDiaryOnServer(diaryId: String, completion: @escaping (Bool) -> Void = { _ in }) {
        ensureAuth { success in
            guard success else { completion(false); return }
            print("🗑️ [API] Deleting Diary ID: \(diaryId)")
            // 204 No Content expected, so we relax parsing checks or handle failure
            self.performRequest(endpoint: "/diaries/\(diaryId)/", method: "DELETE") { result in
                switch result {
                case .success:
                    print("✅ [API] Delete Success")
                    completion(true)
                case .failure(let error):
                    // If status was 204/200 but parsing failed due to empty body, consider it success
                    let nsError = error as NSError
                    if nsError.code == 3840 { // JSON text did not start with array or object... caused by empty body
                         print("✅ [API] Delete Success (Empty Body)")
                         completion(true)
                    } else {
                        print("❌ [API] Delete Failed: \(error.localizedDescription)")
                        completion(false)
                    }
                }
            }
        }
    }
    
    // MARK: - Mind Guide (Weekly Analysis)
    func fetchMindGuide(date: Date, weather: String, completion: @escaping (String?) -> Void) {
        ensureAuth { success in
            guard success else { completion(nil); return }
            
            let f = DateFormatter()
            f.dateFormat = "yyyy-MM-dd"
            let dateStr = f.string(from: date)
            
            // Query Params
            let weatherParam = weather.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
            let endpoint = "/insight?date=\(dateStr)&weather=\(weatherParam)"
            
            self.performRequest(endpoint: endpoint, method: "GET") { result in
                switch result {
                case .success(let data):
                    if let msg = data["message"] as? String {
                        completion(msg)
                    } else {
                        completion(nil)
                    }
                case .failure(let error):
                    print("❌ [API] Mind Guide Failed: \(error.localizedDescription)")
                    completion(nil)
                }
            }
        }
    }
    
    // MARK: - Chat (OCI Server Mode: Maum-On 217 Node)
    func sendChatMessage(text: String, history: String, completion: @escaping (Result<String, Error>) -> Void) {
        ensureAuth { success in
            guard success else {
                completion(.failure(NSError(domain: "Auth", code: 401, userInfo: [NSLocalizedDescriptionKey: "OCI 서버 로그인이 필요합니다."])))
                return
            }
            
            // [Config] 217 Server for LLM
            // Class-level property 사용으로 타겟 명확화
            let llmBaseURL = self.llmServerURL
            let endpoint = "/chat/reaction"
            
            guard let url = URL(string: llmBaseURL + endpoint) else { return }
            
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.timeoutInterval = 70.0 // [Fallback] Wait up to 70s for Server LLM (Safety)
            
            // Auth Token (Pass it just in case 217 needs it, or for logging)
            if let token = self.token {
                request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            }
            
            let payload: [String: Any] = [
                "text": text,
                "mode": "reaction",
                "history": history
            ]
            
            request.httpBody = try? JSONSerialization.data(withJSONObject: payload)
            
            print("🚀 [API-217] Chat Request to LLM Node: \(llmBaseURL)")
            
            URLSession.shared.dataTask(with: request) { data, response, error in
                if let error = error {
                    print("❌ [API-217] Connection Failed: \(error.localizedDescription)")
                    completion(.failure(error))
                    return
                }
                
                guard let data = data, let httpResponse = response as? HTTPURLResponse else {
                    completion(.failure(NSError(domain: "Network", code: -1, userInfo: nil)))
                    return
                }
                
                if httpResponse.statusCode != 200 {
                    print("⚠️ [API-217] Server Error: \(httpResponse.statusCode)")
                    completion(.failure(NSError(domain: "HTTP", code: httpResponse.statusCode, userInfo: nil)))
                    return
                }
                
                do {
                    if let dataDict = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                        if let reply = dataDict["reaction"] as? String {
                            completion(.success(reply))
                        } else if let reply = dataDict["response"] as? String ?? dataDict["message"] as? String {
                             completion(.success(reply))
                        } else {
                            completion(.failure(NSError(domain: "API", code: -1, userInfo: [NSLocalizedDescriptionKey: "응답 형식 오류"])))
                        }
                    }
                } catch {
                    completion(.failure(error))
                }
            }.resume()
        }
    }
    

    // MARK: - Core Networking
    
    // [Security Bypass] Custom Session for Self-Signed Certs
    private lazy var session: URLSession = {
        let config = URLSessionConfiguration.default
        return URLSession(configuration: config, delegate: self, delegateQueue: nil)
    }()

    private func performRequest(endpoint: String, method: String, body: [String: Any]? = nil, requiresAuth: Bool = true, completion: @escaping (Result<[String: Any], Error>) -> Void) {
        guard let url = URL(string: baseURL + endpoint) else {
            completion(.failure(NSError(domain: "Invalid URL", code: -1, userInfo: nil)))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("true", forHTTPHeaderField: "ngrok-skip-browser-warning")
        
        if requiresAuth, let token = self.token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        // [Sync Headers] Pass credentials for 217 Sync (OCI Only)
        if let pwd = UserDefaults.standard.string(forKey: "app_password") {
            request.setValue(pwd, forHTTPHeaderField: "X-Sync-Password")
        }
        
        if let body = body {
            request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        }
        
        print("🚀 [API-OCI] \(method) \(endpoint)")
        
        // Use Custom Session
        session.dataTask(with: request) { data, response, error in
            if let error = error {
                print("❌ [API-OCI] Error: \(error.localizedDescription)")
                completion(.failure(error))
                return
            }
            
            guard let httpResponse = response as? HTTPURLResponse else {
                completion(.failure(NSError(domain: "No Data", code: -1, userInfo: nil)))
                return
            }
            
            // Should be optional, but handle safely
            let responseData = data ?? Data()
            
            if !(200...299).contains(httpResponse.statusCode) {
                print("📡 [API-OCI] Failed: \(httpResponse.statusCode)")
                if let str = String(data: responseData, encoding: .utf8) {
                     print("📡 [API-OCI] Body: \(str)")
                }
                completion(.failure(NSError(domain: "HTTP", code: httpResponse.statusCode, userInfo: nil)))
                return
            }
            
            do {
                if let json = try JSONSerialization.jsonObject(with: responseData) as? [String: Any] {
                    completion(.success(json))
                } else if let jsonArray = try JSONSerialization.jsonObject(with: responseData) as? [[String: Any]] {
                      // Compatibility
                      completion(.success(["data": jsonArray]))
                } else {
                      if let str = String(data: responseData, encoding: .utf8) {
                        print("📡 [API-OCI] Invalid Dict Format: \(str)")
                      }
                      completion(.failure(NSError(domain: "Invalid Format", code: -1, userInfo: nil)))
                }
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    // Array Response helper
    private func performRequestList(endpoint: String, method: String, completion: @escaping (Result<[[String: Any]], Error>) -> Void) {
        guard let url = URL(string: baseURL + endpoint) else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let token = self.token {
            request.addValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        print("🚀 [API-OCI-LIST] \(method) \(endpoint)")
        
        session.dataTask(with: request) { data, response, error in
            if let error = error { completion(.failure(error)); return }
            
            guard let httpResponse = response as? HTTPURLResponse else {
                 completion(.failure(NSError(domain: "No Response", code: 0, userInfo: nil)))
                 return
            }
            
            // Should be optional, but if compiler complains, handle gracefully
            let responseData = data ?? Data()
            
            if !(200...299).contains(httpResponse.statusCode) {
                print("📡 [API-OCI-LIST] Failed: \(httpResponse.statusCode)")
                if let str = String(data: responseData, encoding: .utf8) { print("Body: \(str)") }
                completion(.failure(NSError(domain: "HTTP", code: httpResponse.statusCode, userInfo: nil)))
                return
            }
            
            do {
                if let json = try JSONSerialization.jsonObject(with: responseData) as? [[String: Any]] {
                    completion(.success(json))
                } else if let jsonDict = try JSONSerialization.jsonObject(with: responseData) as? [String: Any],
                          let results = jsonDict["results"] as? [[String: Any]] {
                    completion(.success(results))
                } else {
                     if let str = String(data: responseData, encoding: .utf8) { print("Invalid List JSON: \(str)") }
                    completion(.failure(NSError(domain: "API", code: -1, userInfo: nil)))
                }
            } catch {
                print("JSON Error: \(error)")
                completion(.failure(error))
            }
        }.resume()
    }

}

// MARK: - SSL Bypass Delegate
extension APIService: URLSessionDelegate {
    func urlSession(_ session: URLSession, didReceive challenge: URLAuthenticationChallenge, completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        // [Security Warning] Trust ALL Certs (for Dev/Private Server)
        // Only do this for trusted endpoints
        if challenge.protectionSpace.authenticationMethod == NSURLAuthenticationMethodServerTrust {
            if let trust = challenge.protectionSpace.serverTrust {
                 completionHandler(.useCredential, URLCredential(trust: trust))
                 return
            }
        }
        completionHandler(.performDefaultHandling, nil)
    }

    
    // MARK: - 217 Bulk Sync
    // MARK: - 217 Bulk Sync (Deprecated / Integrated)
    func triggerBulkSync(completion: @escaping (Bool) -> Void) {
        // [Fix] Removed legacy sync trigger which caused 404.
        // B2G Sync handles data propagation.
        print("✅ [API] Bulk Sync Skipped (Legacy Endpoint Removed)")
        completion(true)
        
        /*
        performRequest(endpoint: "/maum_on/sync_all/", method: "POST") { result in
            switch result {
            case .success:
                print("✅ [API] Bulk Sync Triggered Success")
                completion(true)
            case .failure(let error):
                print("❌ [API] Bulk Sync Failed: \(error.localizedDescription)")
                completion(false)
            }
        }
        */
    }
}
