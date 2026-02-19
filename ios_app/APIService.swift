
import Foundation
import Combine

class APIService: NSObject {
    static let shared = APIService()
    
    // OCI Production Server (Main Backend) -> Moved to 217
    // [Target Fix] Updated to 217 Server for Web/App Sync
    private let baseURL = "https://217.142.253.35.nip.io/api"
    
    // [Medical Dashboard] Django API (Role: Source of Truth for Diaries)
    private let medicalURL = "https://217.142.253.35.nip.io/api/v1"
    
    // [Target Fix] Dedicated LLM Node (217.142...)
    private let llmServerURL = "https://217.142.253.35.nip.io/api"
    
    private var memoryToken: String?
    
    private var token: String? {
        get { 
            if let t = memoryToken { return t }
            return UserDefaults.standard.string(forKey: "serverAuthToken")
        }
        set { 
            memoryToken = newValue
            UserDefaults.standard.set(newValue, forKey: "serverAuthToken")
        }
    }
    
    private override init() {
        super.init()
        // Initialize memory cache
        self.memoryToken = UserDefaults.standard.string(forKey: "serverAuthToken")
    }
    
    // MARK: - Auth
    // ... (Auth methods remain unchanged, using baseURL/Flask) ...
    // Note: Login generates token valid for both Flask and Django (Shared Secret)

    func ensureAuth(completion: @escaping (Bool) -> Void) {
        // [Auth - Unified Identity]
        // CRITICAL FIX: Use "authUsername" (Single Source of Truth)
        guard let username = UserDefaults.standard.string(forKey: "authUsername"), !username.isEmpty else {
            print("⚠️ [API-OCI] No Valid Identity (authUsername). Require Login.")
            completion(false)
            return
        }
        
        // [Fix] 토큰이 이미 있으면 재로그인 없이 바로 통과
        // 토큰 만료 시 서버가 401을 반환하면 그때 실패 처리
        if let existingToken = self.token, !existingToken.isEmpty {
            completion(true)
            return
        }
        
        // 토큰이 없는 경우에만 재로그인 시도
        // [Fix] 사용자가 실제 입력한 비밀번호 사용 (랜덤 UUID 생성 제거)
        guard let password = UserDefaults.standard.string(forKey: "app_password"), !password.isEmpty else {
            print("⚠️ [API-OCI] No stored password. User must re-login from Login screen.")
            completion(false)
            return
        }
        
        let body: [String: Any] = ["username": username, "password": password]
        
        // [Fix] Endpoint: /login (Correct path under /api/)
        performRequest(baseURL: self.baseURL, endpoint: "/login", method: "POST", body: body, requiresAuth: false) { result in
            switch result {
            case .success(let response):
                if let accessToken = response["access_token"] as? String {
                     self.token = accessToken
                     
                     // [Name Sync]
                     if let rName = response["name"] as? String, !rName.isEmpty {
                         UserDefaults.standard.set(rName, forKey: "realName")
                     }
                     
                     // [ID Sync Strategy: JWT Decoding]
                     var idSaved = false
                     
                     // 1. Try Response Body
                     if let uid = response["id"] as? Int {
                         UserDefaults.standard.set(String(uid), forKey: "userId")
                         idSaved = true
                     } else if let uidStr = response["id"] as? String {
                         UserDefaults.standard.set(uidStr, forKey: "userId")
                         idSaved = true
                     }
                     
                     // 2. Try JWT Decoding (Fallback)
                     if !idSaved {
                         if let jwtId = self.decodeUserIdFromJWT(token: accessToken) {
                             UserDefaults.standard.set(jwtId, forKey: "userId")
                             idSaved = true
                             print("✅ [Auth] Extracted User ID from JWT: \(jwtId)")
                         }
                     }
                     
                     completion(true)
                } else {
                    completion(false)
                }
             case .failure(let err):
                // [Fix] 로그인 실패 시 랜덤 회원가입 시도 제거
                // ensureAuth는 이미 가입된 사용자의 토큰 갱신 전용
                // 신규 가입은 AppLoginView → AuthManager.performLogin()에서 처리
                print("⚠️ [API-OCI] Re-login failed: \(err). User must re-login from Login screen.")
                completion(false)
            }
        }
    }
    
    // [New] User Info Sync without Re-login
    // [New] User Info Sync without Re-login (Targets 217 Server)
    func syncUserInfo(completion: @escaping (Bool) -> Void) {
        // [Fix] /api/auth/me/ → /api/user/me (Flask 엔드포인트, nginx 라우팅 정상)
        let urlStr = self.baseURL + "/user/me"
        guard let url = URL(string: urlStr) else { completion(false); return }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = 10.0
        
        if let token = self.token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        // print("🚀 [API-217] Syncing User Info: \(urlStr)")
        
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
                // print("✅ [API-217] User ID Synced: \(id)")
            }
            if let name = json["name"] as? String, !name.isEmpty {
                UserDefaults.standard.set(name, forKey: "realName")
                // print("✅ [API-217] Real Name Synced: \(name)")
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
        
        performRequest(baseURL: self.baseURL, endpoint: "/user/profile/", method: "PUT", body: body) { result in
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
    func syncDiary(_ diary: Diary, completion: @escaping (Bool) -> Void = { _ in }) {
        let dateStr = diary.date ?? "Unknown"
        // print("🔄 [API] Syncing Diary: \(dateStr)")
        
        ensureAuth { success in
            guard success else {
                print("❌ [API] Sync Aborted: Auth Failed.")
                completion(false)
                return
            }
            
            // [Switch] Use Medical Dashboard API (Django)
            // Django Endpoint: /diaries/date/YYYY-MM-DD/
            self.performRequest(baseURL: self.medicalURL, endpoint: "/diaries/date/\(dateStr)/", method: "GET") { result in
                switch result {
                case .success(let data):
                    // Found -> Update (PUT)
                    // print("✅ [API] Found existing diary for \(dateStr). Updating...")
                    if let id = data["id"] as? Int {
                        self.updateDiaryOnServer(diaryId: String(id), diary: diary, completion: completion)
                    } else if let id = data["id"] as? String {
                        self.updateDiaryOnServer(diaryId: id, diary: diary, completion: completion)
                    } else {
                         print("⚠️ [API] ID parsing failed. Falling back to Create.")
                         self.createDiaryOnServer(diary, completion: completion)
                    }
                case .failure(let error):
                    // Not Found (404)
                    // [Fix] 이미 동기화된 항목인데 서버에 없다면 → 서버에서 삭제된 것
                    // 재생성하지 않고 로컬에서도 제거
                    if diary.isSynced == true, let sid = diary._id, !sid.isEmpty {
                        print("🗑️ [API-Medical] Server-deleted diary detected: \(dateStr) (was ID: \(sid)). Skipping re-create.")
                        DispatchQueue.main.async {
                            LocalDataManager.shared.removeServerDeletedDiary(serverId: sid, dateStr: dateStr)
                        }
                        completion(true)
                    } else {
                        // 순수 로컬 신규 항목 → 서버에 새로 생성
                        self.createDiaryOnServer(diary, completion: completion)
                    }
                }
            }
        }
    }


    // [Helper] Build Payload (Django Schema)
    private func buildDiaryPayload(_ diary: Diary) -> [String: Any] {
        // Django Model: content, mood_score, date(for creation), sleep_condition, etc.
        var basePayload: [String: Any] = [
            "date": diary.date ?? "", // Serializer will map this to created_at
            "content": diary.event ?? "", // [Fix] 'content' instead of 'event'
            "mood_score": diary.mood_level, // [Fix] 'mood_score' instead of 'mood_level'
            "weather": diary.weather ?? "",
            "sleep_condition": diary.sleep_desc ?? (diary.sleep_condition ?? ""),
            "emotion_desc": diary.emotion_desc ?? "",
            "emotion_meaning": diary.emotion_meaning ?? "",
            "self_talk": diary.self_talk ?? "",
            "gratitude_note": diary.gratitude_note ?? "",
            "medication_taken": diary.medication_taken
        ]
            
        // Flat fields for legacy/extended support (Django Serializer flattens them)
        // No need for nested 'analysis_result' if serializer handles it,
        // But Django Serializer updates analysis_result JSON field if we send specific keys.
        // We send them as top-level keys because `MaumOnSerializer.update` expects them.
        
        basePayload["ai_prediction"] = diary.ai_prediction ?? ""
        basePayload["ai_analysis"] = diary.ai_analysis ?? ""
        basePayload["ai_comment"] = diary.ai_comment ?? (diary.ai_advice ?? "")
        basePayload["ai_advice"] = diary.ai_advice ?? ""
        basePayload["symptoms"] = diary.symptoms ?? []
        basePayload["temperature"] = String(diary.temperature ?? 0.0) // String or Number? Django CharField.
        
        return basePayload
    }

    private func createDiaryOnServer(_ diary: Diary, completion: @escaping (Bool) -> Void) {
        var payload = buildDiaryPayload(diary)
        print("🚀 [API-Medical] Creating New Diary: \(diary.date ?? "")")
        
        // Django Endpoint: /diaries/ (POST)
        performRequest(baseURL: self.medicalURL, endpoint: "/diaries/", method: "POST", body: payload) { result in
            switch result {
            case .success(let data):
                print("✅ [API-Medical] Diary Created. ID: \(data["id"] ?? "null")")
                completion(true)
            case .failure(let error):
                print("❌ [API-Medical] Create Failed: \(error.localizedDescription)")
                completion(false)
            }
        }
    }
    
    private func updateDiaryOnServer(diaryId: String, diary: Diary, completion: @escaping (Bool) -> Void) {
        var payload = buildDiaryPayload(diary)
        print("🚀 [API-Medical] Updating Diary ID: \(diaryId)")
        
        // Django Endpoint: /diaries/{id}/ (PUT)
        performRequest(baseURL: self.medicalURL, endpoint: "/diaries/\(diaryId)/", method: "PUT", body: payload) { result in
            switch result {
            case .success:
                print("✅ [API-Medical] Diary Updated.")
                completion(true)
            case .failure(let error):
                print("❌ [API-Medical] Update Failed: \(error.localizedDescription)")
                completion(false)
            }
        }
    }
    
    // ... (helper methods skipped) ...
    
    // MARK: - B2G / Center Data Sync
    
    func syncCenterData(payload: [String: Any], completion: @escaping (Bool, String?) -> Void) {
        // [Fix] Endpoint: /centers/sync-data/ (Base URL already includes /v1)
        performRequest(baseURL: self.medicalURL, endpoint: "/centers/sync-data/", method: "POST", body: payload, requiresAuth: true) { result in
            switch result {
            case .success(let json):
                if let success = json["success"] as? Bool, success == true { 
                    completion(true, nil)
                } else if let message = json["message"] as? String, message.contains("Data synced") {
                     completion(true, nil)
                } else {
                    // print("⚠️ [Sync] JSON 'success' field missing, but HTTP 200 OK. Assuming Success.")
                    completion(true, nil)
                }
            case .failure(let error):
                completion(false, error.localizedDescription)
            }
        }
    }
    
    func verifyCenterCode(_ code: String, completion: @escaping (Result<[String: Any], Error>) -> Void) {
        let nickname = UserDefaults.standard.string(forKey: "userNickname") ?? "Guest"
        let payload = ["code": code, "user_nickname": nickname]
        
        // [Fix] Endpoint: /centers/verify-code/
        performRequest(baseURL: self.medicalURL, endpoint: "/centers/verify-code/", method: "POST", body: payload, requiresAuth: false) { result in
            completion(result)
        }
    }

    func connectToCenter(centerId: Any, completion: @escaping (Bool) -> Void) {
        let payload: [String: Any] = ["center_id": centerId]
        
        // [Fix] Endpoint: /b2g_sync/connect/ (Django urls.py에 등록된 경로)
        performRequest(baseURL: self.medicalURL, endpoint: "/b2g_sync/connect/", method: "POST", body: payload, requiresAuth: true) { result in
            switch result {
            case .success:
                completion(true)
            case .failure(let error):
                print("❌ [API] Connect Center Failed: \(error.localizedDescription)")
                completion(false)
            }
        }
    }
    
    // MARK: - Mind Guide
    func fetchMindGuide(completion: @escaping ([String: Any]?) -> Void) {
        ensureAuth { success in
            guard success else { completion(nil); return }
            
            // [Fix] Endpoint: /mind-guide/today/
            self.performRequest(baseURL: self.medicalURL, endpoint: "/mind-guide/today/", method: "GET") { result in
                switch result {
                case .success(let data):
                    completion(data)
                case .failure(let error):
                    print("❌ [API] Fetch MindGuide Failed: \(error.localizedDescription)")
                    completion(nil)
                }
            }
        }
    }
    
    func fetchDiaries(completion: @escaping ([[String: Any]]?) -> Void) {
        ensureAuth { success in
            guard success else { completion(nil); return }
            // Django Endpoint: /diaries/ (GET List)
            self.performRequestList(baseURL: self.medicalURL, endpoint: "/diaries/", method: "GET") { result in
                switch result {
                case .success(let list):
                    completion(list)
                case .failure(let error):
                    print("❌ [API-Medical] Fetch Diaries Failed: \(error.localizedDescription)")
                    completion(nil)
                }
            }
        }
    }
    
    // MARK: - Diary CRUD
    func deleteDiaryOnServer(diaryId: String, completion: @escaping (Bool) -> Void = { _ in }) {
        ensureAuth { success in
            guard success else { completion(false); return }
            print("🗑️ [API-Medical] Deleting Diary ID: \(diaryId)")
            
            // Django Endpoint: /diaries/{id}/ (DELETE)
            self.performRequest(baseURL: self.medicalURL, endpoint: "/diaries/\(diaryId)/", method: "DELETE") { result in
                switch result {
                case .success:
                    print("✅ [API-Medical] Delete Success")
                    completion(true)
                case .failure(let error):
                    print("❌ [API-Medical] Delete Failed: \(error.localizedDescription)")
                    completion(false)
                }
            }
        }
    }
    
    // MARK: - Chat (OCI Server Mode: maumON 217 Node)
    func sendChatMessage(text: String, history: String, completion: @escaping (Result<String, Error>) -> Void) {
        ensureAuth { success in
            guard success else {
                completion(.failure(NSError(domain: "Auth", code: 401, userInfo: [NSLocalizedDescriptionKey: "OCI 서버 로그인이 필요합니다."])))
                return
            }
            
            // [Config] 217 Server for LLM
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
            
            // print("🚀 [API-217] Chat Request to LLM Node: \(llmBaseURL)")
            
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
    
    // ... (Core Networking needs to support variable baseURL) ...
    
    // MARK: - Core Networking

    // Refactored to accept baseURL
    func performRequest(baseURL: String? = nil, endpoint: String, method: String, body: [String: Any]? = nil, requiresAuth: Bool = true, completion: @escaping (Result<[String: Any], Error>) -> Void) {
        
        let targetBase = baseURL ?? self.baseURL // Default to Flask if not specified
        
        // [Fix] Ensure Endpoint Format (Add '/' if missing, Remove Trailing Slash)
        var safeEndpoint = endpoint
        if !safeEndpoint.hasPrefix("/") { safeEndpoint = "/" + safeEndpoint }
        // Django requires trailing slash usually, Flask doesn't.
        // Django APPEND_SLASH=False setting checks.
        // Safe bet: Do not strip trailing slash if it exists.
        
        // [Standard] RFC 6750 Sec 2.3
        var components = URLComponents(string: targetBase + safeEndpoint)
        
        if requiresAuth, let token = self.token {
            var items = components?.queryItems ?? []
            items.append(URLQueryItem(name: "jwt", value: token))
            components?.queryItems = items
        }
        
        guard let url = components?.url else {
            completion(.failure(NSError(domain: "Invalid URL", code: -1, userInfo: nil)))
            return
        }
        
        var request = URLRequest(url: url)
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("true", forHTTPHeaderField: "ngrok-skip-browser-warning")
        request.httpMethod = method
        
        if let body = body {
            request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        }
        
        if requiresAuth {
            // [Critical Fix] Read token directly from UserDefaults to ensure freshness after login
            if let token = UserDefaults.standard.string(forKey: "serverAuthToken") {
                request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
                self.token = token // Sync local var
            }
        }
        
        print("🚀 [API-OCI] \(method) \(safeEndpoint)")
        if let token = request.value(forHTTPHeaderField: "Authorization") {
             // print("🔑 [API-OCI] Token: \(token.prefix(10))...")
        } else if requiresAuth {
             print("⚠️ [API-OCI] No Auth Token!")
        }
        
        // Use Shared Session
        URLSession.shared.dataTask(with: request) { data, response, error in
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
    func performRequestList(baseURL: String? = nil, endpoint: String, method: String, completion: @escaping (Result<[[String: Any]], Error>) -> Void) {
        let targetBase = baseURL ?? self.baseURL
        
        // [Fix] Ensure Endpoint Format (Add '/' if missing, Remove Trailing Slash)
        var safeEndpoint = endpoint
        if !safeEndpoint.hasPrefix("/") { safeEndpoint = "/" + safeEndpoint }
        // Django expects trailing slashes sometimes, but let's stick to no trailing for consistency unless required.
        // if safeEndpoint.hasSuffix("/") { safeEndpoint = String(safeEndpoint.dropLast()) }
        
        // [Standard] RFC 6750 Sec 2.3: URI Query Parameter
        var components = URLComponents(string: targetBase + safeEndpoint)
        
        if let token = self.token {
            var items = components?.queryItems ?? []
            items.append(URLQueryItem(name: "jwt", value: token))
            components?.queryItems = items
        }
        
        guard let url = components?.url else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("true", forHTTPHeaderField: "ngrok-skip-browser-warning")
        
        // [Critical Fix] Use In-Memory Cached Token
        if let token = self.token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            // Debug Header
            print("🔑 [API-OCI-LIST] Header Set: Bearer \(token.prefix(15))...")
        } else {
            print("⚠️ [API-OCI-LIST] No Token Available (In-Memory/Disk Empty)")
        }
        
        print("🚀 [API-OCI-LIST] \(method) \(safeEndpoint)")
        print("📦 [API-OCI-LIST] Headers: \(request.allHTTPHeaderFields ?? [:])") // Verbose log
        
        URLSession.shared.dataTask(with: request) { data, response, error in
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

        // MARK: - JWT Helper
    private func decodeUserIdFromJWT(token: String) -> String? {
        let segments = token.components(separatedBy: ".")
        guard segments.count > 1 else { return nil }
        
        var base64String = segments[1]
        let requiredLength = (4 * ceil((Double(base64String.count) / 4.0)))
        let nbrPaddings = Int(requiredLength) - base64String.count
        if nbrPaddings > 0 {
            let padding = String(repeating: "=", count: nbrPaddings)
            base64String += padding
        }
        
        base64String = base64String.replacingOccurrences(of: "-", with: "+")
        base64String = base64String.replacingOccurrences(of: "_", with: "/")
        
        guard let decodedData = Data(base64Encoded: base64String, options: .ignoreUnknownCharacters),
              let json = try? JSONSerialization.jsonObject(with: decodedData) as? [String: Any] else {
            return nil
        }
        
        // Try common keys for User ID
        if let sub = json["user_id"] as? Int { return String(sub) }
        if let subStr = json["user_id"] as? String { return subStr }
        if let id = json["id"] as? Int { return String(id) }
        
        
        return nil
    }
    
    // MARK: - SSL Bypass Delegate (Legacy Removed)
    
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
