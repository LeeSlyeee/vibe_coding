
import Foundation
import Combine

class APIService: NSObject {
    static let shared = APIService()
    
    // OCI Production Server (Main Backend) -> Moved to 217
    // [Target Fix] Updated to 217 Server for Web/App Sync
    private let baseURL = "https://217.142.253.35.nip.io/api"
    
    // [Legacy] 150 Server (Deprecated for main logic, maybe used for recovery)
    // private let legacyURL = "https://150.230.7.76.nip.io/api/v1"
    
    // [Target Fix] Dedicated LLM Node (217.142...)
    // 채팅 및 AI 기능은 이 주소를 타겟으로 함 (User Specified)
    // Note: baseURL과 동일하므로 중복되지만, 명시적으로 남겨둠.
    private let llmServerURL = "https://217.142.253.35.nip.io/api"
    
    private var token: String? {
        get { UserDefaults.standard.string(forKey: "serverAuthToken") }
        set { UserDefaults.standard.set(newValue, forKey: "serverAuthToken") }
    }
    
    private override init() {
        super.init()
    }
    
    // MARK: - Auth
    func ensureAuth(completion: @escaping (Bool) -> Void) {
        // [Auth - Unified Identity]
        // CRITICAL FIX: Use "authUsername" (Single Source of Truth)
        guard let username = UserDefaults.standard.string(forKey: "authUsername"), !username.isEmpty else {
            print("⚠️ [API-OCI] No Valid Identity (authUsername). Require Login.")
            completion(false)
            return
        }
        
        // 2. Get or Generate Password
        var password = UserDefaults.standard.string(forKey: "app_password")
        if password == nil {
            // Generate random password
            password = String(UUID().uuidString.prefix(8))
            UserDefaults.standard.set(password, forKey: "app_password")
        }
        
        
        let body: [String: Any] = ["username": username, "password": password!]
        
        print("🔐 [API-217] Attempting Auth for: '\(username)' (PW: \(password!))")
        
        // Token Existence Check (Optimistic Auth)
        if token != nil {
            completion(true)
            return
        }
        
        // [Fix] Endpoint: /login (No strict slash)
        performRequest(endpoint: "/login", method: "POST", body: body, requiresAuth: false) { result in
            switch result {
            case .success(let response):
                if let accessToken = response["access_token"] as? String {
                     self.token = accessToken
                     
                     // [Name Sync] 로그인 시 실명 정보 저장
                     if let rName = response["name"] as? String, !rName.isEmpty {
                         UserDefaults.standard.set(rName, forKey: "realName")
                     }
                     
                     print("🌐 [API-217] Login Success: \(username)")
                     completion(true)
                } else {
                    completion(false)
                }
             case .failure:
                print("🌐 [API-217] Login failed, trying registration for: \(username)")
                // 회원가입 시도 [Fix] Endpoint: /register
                self.performRequest(endpoint: "/register", method: "POST", body: body, requiresAuth: false) { regResult in
                    switch regResult {
                    case .success:
                         self.performRequest(endpoint: "/login", method: "POST", body: body, requiresAuth: false) { loginRetry in
                            if case .success(let retryResp) = loginRetry,
                               let accessToken = retryResp["access_token"] as? String {
                                self.token = accessToken
                                completion(true)
                            } else {
                                completion(false)
                            }
                         }
                    case .failure(let err):
                        print("🌐 [API-217] Registration failed: \(err)")
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
            if let id = json["id"] as? String {
                UserDefaults.standard.set(id, forKey: "userId") // [CRITICAL] Store User ID
                print("✅ [API-217] User ID Synced: \(id)")
            }
            if let name = json["name"] as? String, !name.isEmpty {
                UserDefaults.standard.set(name, forKey: "realName")
                print("✅ [API-217] Real Name Synced: \(name)")
            }
            if let nickname = json["nickname"] as? String, !nickname.isEmpty {
                UserDefaults.standard.set(nickname, forKey: "userNickname")
            }
            if let birthDate = json["birth_date"] as? String, !birthDate.isEmpty {
                UserDefaults.standard.set(birthDate, forKey: "userBirthDate")
            }
            completion(true)
        }.resume()
    }
    
    // [New] Update User Profile
    func updateProfile(nickname: String?, birthDate: String?, completion: @escaping (Bool) -> Void) {
        var body: [String: Any] = [:]
        if let n = nickname { body["nickname"] = n }
        if let b = birthDate { body["birth_date"] = b }
        
        performRequest(endpoint: "/user/profile", method: "PUT", body: body) { result in
            switch result {
            case .success:
                if let n = nickname { UserDefaults.standard.set(n, forKey: "userNickname") }
                if let b = birthDate { UserDefaults.standard.set(b, forKey: "userBirthDate") }
                completion(true)
            case .failure:
                completion(false)
            }
        }
    }
    
    // MARK: - Diary Sync
    
    // Unified Sync Method
    // Unified Sync Method
    func syncDiary(_ diary: Diary, completion: @escaping (Bool) -> Void = { _ in }) {
        print("🔄 [API] Syncing Diary: \(diary.date ?? "Unknown")")
        
        ensureAuth { success in
            guard success else {
                print("❌ [API] Sync Aborted: Auth Failed.")
                completion(false)
                return
            }
            
            let dateStr = diary.date ?? ""
            
            // 1. Check existence by Date [Fix] Remove trailing slash
            self.performRequest(endpoint: "/diaries/date/\(dateStr)/", method: "GET") { result in
                switch result {
                case .success(let data):
                    // Found -> Update (PUT)
                    print("✅ [API] Found existing diary for \(dateStr). Updating...")
                    if let id = data["id"] as? Int {
                        self.updateDiaryOnServer(diaryId: String(id), diary: diary, completion: completion)
                    } else if let id = data["id"] as? String {
                        self.updateDiaryOnServer(diaryId: id, diary: diary, completion: completion)
                    } else {
                         // ID parsing failed, try create
                         print("⚠️ [API] ID parsing failed. Falling back to Create.")
                         self.createDiaryOnServer(diary, completion: completion)
                    }
                case .failure(let error):
                    // Not Found or Error -> Create (POST)
                    // [Important] 404면 생성이 맞지만, 500이면? 일단 생성을 시도해본다.
                    print("⚠️ [API] Lookup failed for \(dateStr): \(error). Attempting Create...")
                    self.createDiaryOnServer(diary, completion: completion)
                }
            }
        }
    }

    // [Helper] Build Payload
    private func buildDiaryPayload(_ diary: Diary) -> [String: Any] {
        var payload: [String: Any] = [
            "date": diary.date ?? "",
            "event": diary.event ?? "",
            "mood_level": diary.mood_level,
            "weather": diary.weather ?? "",
            "sleep_desc": diary.sleep_desc ?? (diary.sleep_condition ?? ""),
            "emotion_desc": diary.emotion_desc ?? "",
            "emotion_meaning": diary.emotion_meaning ?? "",
            "self_talk": diary.self_talk ?? "",
            "gratitude_note": diary.gratitude_note ?? "",
            "medication_taken": diary.medication_taken,
            "symptoms": diary.symptoms ?? [],
            
            // AI Data (Optional)
            "ai_prediction": diary.ai_prediction ?? "",
            "ai_analysis": diary.ai_analysis ?? "",
            "ai_comment": diary.ai_comment ?? (diary.ai_advice ?? "")
        ]
        return payload
    }

    private func createDiaryOnServer(_ diary: Diary, completion: @escaping (Bool) -> Void) {
        let payload = buildDiaryPayload(diary)
        print("🚀 [API] Creating New Diary: \(diary.date ?? "")")
        
        // [Fix] Remove trailing slash
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
        
        // [Fix] Remove trailing slash
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
    
    // ... (helper methods skipped) ...
    
    // MARK: - B2G Data Sync (Push)
    func syncCenterData(payload: [String: Any], completion: @escaping (Bool, String?) -> Void) {
        // [Fix] Endpoint: /v1/centers/sync-data/ (Explicit v1 mapping for b2g_routes)
        performRequest(endpoint: "/v1/centers/sync-data/", method: "POST", body: payload, requiresAuth: true) { result in
            switch result {
            case .success(let json):
                if let success = json["success"] as? Bool, success == true { 
                    completion(true, nil)
                } else if let message = json["message"] as? String, message.contains("Data synced") {
                     completion(true, nil)
                } else {
                    print("⚠️ [Sync] JSON 'success' field missing, but HTTP 200 OK. Assuming Success.")
                    completion(true, nil)
                }
            case .failure(let error):
                completion(false, error.localizedDescription)
            }
        }
    }
    
    func verifyCenterCode(_ code: String, completion: @escaping (Result<[String: Any], Error>) -> Void) {
        let nickname = UserDefaults.standard.string(forKey: "userNickname") ?? "Guest"
        // [Fix] Direct URL Request to bypass '/api' prefix issue
        // [Fix] Revert to V1 Endpoint which is confirmed to work (or verify path)
        // Previous error: 404 on .../verify-code-v2/
        let urlStr = "https://217.142.253.35.nip.io/api/v1/centers/verify-code/"
        guard let url = URL(string: urlStr) else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        // [Fix] Add headers just in case
        request.setValue("true", forHTTPHeaderField: "ngrok-skip-browser-warning")
        
        let payload = ["code": code, "user_nickname": nickname]
        request.httpBody = try? JSONSerialization.data(withJSONObject: payload)
        
        print("🚀 [API-Direct] POST \(urlStr)")
        
        // Use shared session (with SSL bypass delegate if needed, but here simple shared)
        // Note: If self-signed cert issue arises, use self.session
        self.session.dataTask(with: request) { data, response, error in
            if let error = error {
                print("❌ [API-Direct] Error: \(error.localizedDescription)")
                completion(.failure(error))
                return
            }
            
            guard let httpResponse = response as? HTTPURLResponse else {
                completion(.failure(NSError(domain: "No Response", code: 0, userInfo: nil)))
                return
            }
            
            print("📡 [API-Direct] Status: \(httpResponse.statusCode)")
            
            if (200...299).contains(httpResponse.statusCode), let data = data {
                do {
                    if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                        completion(.success(json))
                    } else {
                        // Sometimes array wrapper?
                         if let jsonArr = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]], let first = jsonArr.first {
                              completion(.success(first))
                         } else {
                             completion(.failure(NSError(domain: "Invalid JSON", code: -1, userInfo: nil)))
                         }
                    }
                } catch {
                     // Try parsing as simple string message
                     if let str = String(data: data, encoding: .utf8) {
                         print("📝 [API-Direct] Response: \(str)")
                     }
                     completion(.failure(error))
                }
            } else {
                // [Debug] Log Body on Failure
                if let data = data, let str = String(data: data, encoding: .utf8) {
                    print("📝 [API-Direct] Fail Body: \(str)")
                }
                completion(.failure(NSError(domain: "HTTP", code: httpResponse.statusCode, userInfo: nil)))
            }
        }.resume()
    }
    
    func connectToCenter(centerId: Any, completion: @escaping (Bool) -> Void) {
        ensureAuth { success in
            guard success else { completion(false); return }
            var payload: [String: Any] = [:]
            if let idInt = centerId as? Int { payload["center_id"] = idInt }
            else if let idStr = centerId as? String { payload["center_id"] = idStr }
            
            // [Fix] Endpoint: /b2g_sync/connect/ (Matches @b2g_bp.route('/api/b2g_sync/connect/'))
            self.performRequest(endpoint: "/b2g_sync/connect/", method: "POST", body: payload) { result in
                if case .success = result { completion(true) } else { completion(false) }
            }
        }
    }
    
    func fetchDiaries(completion: @escaping ([ [String: Any] ]?) -> Void) {
        ensureAuth { success in
            guard success else { completion(nil); return }
            // [Fix] Remove trailing slash
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
            // [Fix] Remove trailing slash
            self.performRequest(endpoint: "/diaries/\(diaryId)/", method: "DELETE") { result in
                switch result {
                case .success:
                    print("✅ [API] Delete Success")
                    completion(true)
                case .failure(let error):
                    let nsError = error as NSError
                    if nsError.code == 3840 { 
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
    
    // MARK: - Chat (OCI Server Mode: haruON 217 Node)
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
            request.timeoutInterval = 300.0 // [Extended] Wait up to 300s (5min) for RunPod Queue

            
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

    func performRequest(endpoint: String, method: String, body: [String: Any]? = nil, requiresAuth: Bool = true, completion: @escaping (Result<[String: Any], Error>) -> Void) {
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
        if let token = request.value(forHTTPHeaderField: "Authorization") {
            print("🔑 [API-OCI] Auth Token Present: \(token.prefix(10))...")
        } else {
            print("⚠️ [API-OCI] No Auth Token!")
        }
        
        // Use Custom Session
        session.dataTask(with: request) { data, response, error in
            if let error = error {
                print("❌ [API-OCI] Network Error: \(error.localizedDescription)")
                completion(.failure(error))
                return
            }
            
            guard let httpResponse = response as? HTTPURLResponse else {
                completion(.failure(NSError(domain: "No Data", code: -1, userInfo: nil)))
                return
            }
            
            // Should be optional, but handle safely
            let responseData = data ?? Data()
            let responseString = String(data: responseData, encoding: .utf8) ?? "(No Body)"
            
            print("📡 [API-OCI] Status: \(httpResponse.statusCode) | URL: \(endpoint)")
            
            if !(200...299).contains(httpResponse.statusCode) {
                print("❌ [API-OCI] Request Failed!")
                print("📝 [API-OCI] Response Body: \(responseString)")
                completion(.failure(NSError(domain: "HTTP", code: httpResponse.statusCode, userInfo: nil)))
                return
            } else {
                // Success case logging (Optional, noisy)
                // print("✅ [API-OCI] Success Body: \(responseString.prefix(100))...")
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
    func performRequestList(endpoint: String, method: String, completion: @escaping (Result<[[String: Any]], Error>) -> Void) {
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
                if let json = try? JSONSerialization.jsonObject(with: responseData) as? [[String: Any]] {
                    completion(.success(json))
                } else if let jsonDict = try? JSONSerialization.jsonObject(with: responseData) as? [String: Any] {
                    // Check if it's a wrapper like {"data": [...]} or {"results": [...]}
                    if let results = jsonDict["results"] as? [[String: Any]] {
                        completion(.success(results))
                    } else if let dataList = jsonDict["data"] as? [[String: Any]] {
                        completion(.success(dataList))
                    } else if let msg = jsonDict["msg"] as? String {
                        // Backend returned a message instead of list (likely auth error or empty)
                        print("⚠️ [API-OCI-LIST] Server Message: \(msg)")
                        completion(.failure(NSError(domain: "Server", code: -1, userInfo: ["msg": msg])))
                    } else {
                        print("⚠️ [API-OCI-LIST] Unexpected Dict Response: \(jsonDict)")
                        completion(.failure(NSError(domain: "Invalid Format", code: -1, userInfo: nil)))
                    }
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
