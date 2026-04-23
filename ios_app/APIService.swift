
import Foundation
import Combine

// MARK: - Server Configuration (단일 진실 공급원)
// ⚠️ URL 변경 시 이 enum 한 곳만 수정하면 앱 전체에 적용됩니다.
enum ServerConfig {
    #if DEBUG
    /// 로컬 개발 서버 (Xcode 디버그 빌드 전용)
    static let productionHost = "https://217.142.253.35.nip.io"
    #else
    /// 운영 서버 (Archive / TestFlight / App Store 배포)
    static let productionHost = "https://217.142.253.35.nip.io"
    #endif

    static let apiBase    = productionHost + "/api"       // Flask 메인 API
    static let medicalAPI = productionHost + "/api/v1"    // Django 의료 대시보드
}

class APIService: NSObject {
    static let shared = APIService()

    // 모든 URL 참조는 ServerConfig 를 통해서만 접근
    private let baseURL    = ServerConfig.apiBase
    private let medicalURL = ServerConfig.medicalAPI
    private let llmServerURL = ServerConfig.apiBase  // LLM 도 동일 서버 사용

    
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
            completion(false)
            return
        }
        
        // [Fix 2026-04-09] 토큰이 있더라도 만료 여부를 검증
        // 만료된 토큰으로 요청 → 401 → 동기화 실패 연쇄 방지
        if let existingToken = self.token, !existingToken.isEmpty {
            if !isTokenExpired(existingToken) {
                completion(true)
                return
            }
            // 만료된 토큰 → 무효화 후 재로그인 진행
            self.token = nil
        }
        
        // 토큰이 없거나 만료된 경우 재로그인 시도
        // [Fix 2026-04-09] Keychain에서 비밀번호 읽기 (UserDefaults에는 저장된 적 없음)
        guard let password = KeychainHelper.standard.readString(account: "app_password"), !password.isEmpty else {
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
                completion(false)
            }
        }
    }
    
    // [Fix 2026-04-09] JWT 만료 검증 (exp claim 디코딩)
    // 만료 60초 전부터 "만료"로 판단하여 경계 조건 방지
    private func isTokenExpired(_ token: String) -> Bool {
        let segments = token.components(separatedBy: ".")
        guard segments.count > 1 else { return true }
        
        var base64String = segments[1]
        let requiredLength = Int(4 * ceil(Double(base64String.count) / 4.0))
        let nbrPaddings = requiredLength - base64String.count
        if nbrPaddings > 0 {
            base64String += String(repeating: "=", count: nbrPaddings)
        }
        base64String = base64String.replacingOccurrences(of: "-", with: "+")
        base64String = base64String.replacingOccurrences(of: "_", with: "/")
        
        guard let decodedData = Data(base64Encoded: base64String, options: .ignoreUnknownCharacters),
              let json = try? JSONSerialization.jsonObject(with: decodedData) as? [String: Any],
              let exp = json["exp"] as? Double else {
            return true // 디코딩 실패 시 만료로 간주 → 재로그인 유도
        }
        
        // 현재 시각 + 60초 여유로 비교 (네트워크 지연 대비)
        return Date().timeIntervalSince1970 >= (exp - 60)
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
        
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(false)
                return
            }
            
            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                completion(false)
                return
            }
            
            // Success Logic
            if let id = json["id"] as? Int {
                UserDefaults.standard.set(String(id), forKey: "userId")
            } else if let id = json["id"] as? String {
                UserDefaults.standard.set(id, forKey: "userId")
            }
            if let name = json["name"] as? String, !name.isEmpty {
                UserDefaults.standard.set(name, forKey: "realName")
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
        
        ensureAuth { success in
            guard success else {
                completion(false)
                return
            }
            
            // [Revert] Use Flask API for Push Triggers and Sync
            self.performRequest(baseURL: self.baseURL, endpoint: "/diaries/date/\(dateStr)", method: "GET") { result in
                switch result {
                case .success(let data):
                    // Found -> Update (PUT)
                    if let id = data["id"] as? Int {
                        self.updateDiaryOnServer(diaryId: String(id), diary: diary, completion: completion)
                    } else if let id = data["id"] as? String {
                        self.updateDiaryOnServer(diaryId: id, diary: diary, completion: completion)
                    } else {
                         self.createDiaryOnServer(diary, completion: completion)
                    }
                case .failure(let error):
                    // Not Found (404)
                    // [Fix] 이미 동기화된 항목인데 서버에 없다면 → 서버에서 삭제된 것
                    // 재생성하지 않고 로컬에서도 제거
                    if diary.isSynced == true, let sid = diary._id, !sid.isEmpty {
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


    // [Helper] Build Payload (Flask Schema)
    private func buildDiaryPayload(_ diary: Diary) -> [String: Any] {
        var basePayload: [String: Any] = [
            "date": diary.date ?? "",
            "event": diary.event ?? "",
            "mood_level": diary.mood_level,
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
        
        // Flask Endpoint: /diaries (POST)
        performRequest(baseURL: self.baseURL, endpoint: "/diaries", method: "POST", body: payload) { result in
            switch result {
            case .success(let data):
                completion(true)
            case .failure(let error):
                completion(false)
            }
        }
    }
    
    private func updateDiaryOnServer(diaryId: String, diary: Diary, completion: @escaping (Bool) -> Void) {
        var payload = buildDiaryPayload(diary)
        
        // Flask Endpoint: /diaries/{id} (PUT)
        performRequest(baseURL: self.baseURL, endpoint: "/diaries/\(diaryId)", method: "PUT", body: payload) { result in
            switch result {
            case .success:
                completion(true)
            case .failure(let error):
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
                    completion(nil)
                }
            }
        }
    }
    
    // MARK: - Mind Condition (Kick 교차 분석)
    func fetchMyCondition(completion: @escaping ([String: Any]?) -> Void) {
        ensureAuth { success in
            guard success else { completion(nil); return }
            
            // Flask Endpoint: /api/kick/my-condition (JWT Required)
            self.performRequest(baseURL: self.baseURL, endpoint: "/kick/my-condition", method: "GET") { result in
                switch result {
                case .success(let data):
                    completion(data)
                case .failure(let error):
                    completion(nil)
                }
            }
        }
    }
    
    func fetchDiaries(completion: @escaping ([[String: Any]]?) -> Void) {
        ensureAuth { success in
            guard success else { completion(nil); return }
            // Flask Endpoint: /diaries (GET List)
            self.performRequestList(baseURL: self.baseURL, endpoint: "/diaries", method: "GET") { result in
                switch result {
                case .success(let list):
                    completion(list)
                case .failure(let error):
                    completion(nil)
                }
            }
        }
    }
    
    // MARK: - Diary CRUD
    func deleteDiaryOnServer(diaryId: String, completion: @escaping (Bool) -> Void = { _ in }) {
        ensureAuth { success in
            guard success else { completion(false); return }
            
            // Flask Endpoint: /diaries/{id} (DELETE)
            self.performRequest(baseURL: self.baseURL, endpoint: "/diaries/\(diaryId)", method: "DELETE") { result in
                switch result {
                case .success:
                    completion(true)
                case .failure(let error):
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
            
            guard let url = URL(string: llmBaseURL + endpoint) else {
                completion(.failure(NSError(domain: "Invalid URL", code: -1, userInfo: nil)))
                return 
            }
            
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
            
            
            URLSession.shared.dataTask(with: request) { data, response, error in
                if let error = error {
                    completion(.failure(error))
                    return
                }
                
                guard let data = data, let httpResponse = response as? HTTPURLResponse else {
                    completion(.failure(NSError(domain: "Network", code: -1, userInfo: nil)))
                    return
                }
                
                if httpResponse.statusCode != 200 {
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
    
    // MARK: - AI Analysis Report (RunPod → Ollama 서버 체인)
    func requestAnalysisReport(diaries: [[String: Any]], mode: String, completion: @escaping (Result<String, Error>) -> Void) {
        ensureAuth { success in
            guard success else {
                completion(.failure(NSError(domain: "Auth", code: 401, userInfo: [NSLocalizedDescriptionKey: "인증 실패"])))
                return
            }
            
            let endpoint = "/chat/analysis-report"
            guard let url = URL(string: self.llmServerURL + endpoint) else {
                completion(.failure(NSError(domain: "Invalid URL", code: -1, userInfo: nil)))
                return 
            }
            
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.timeoutInterval = 300.0 // RunPod cold start 대비 5분
            
            if let token = self.token {
                request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            }
            
            let payload: [String: Any] = [
                "diaries": diaries,
                "mode": mode
            ]
            
            request.httpBody = try? JSONSerialization.data(withJSONObject: payload)
            
            
            URLSession.shared.dataTask(with: request) { data, response, error in
                if let error = error {
                    completion(.failure(error))
                    return
                }
                
                guard let data = data, let httpResponse = response as? HTTPURLResponse else {
                    completion(.failure(NSError(domain: "Network", code: -1, userInfo: nil)))
                    return
                }
                
                if httpResponse.statusCode != 200 {
                    completion(.failure(NSError(domain: "HTTP", code: httpResponse.statusCode, userInfo: nil)))
                    return
                }
                
                do {
                    if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let report = json["report"] as? String {
                        let source = json["source"] as? String ?? "unknown"
                        completion(.success(report))
                    } else {
                        completion(.failure(NSError(domain: "API", code: -1, userInfo: [NSLocalizedDescriptionKey: "report 필드 없음"])))
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
        request.timeoutInterval = 15.0 // [UX Fix] 60초 기본 대기가 아닌 15초로 단축
        
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
        
        if let token = request.value(forHTTPHeaderField: "Authorization") {
        } else if requiresAuth {
        }
        
        // Use Shared Session
        URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            if let error = error {
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
            
            // [Fix 2026-04-09] 401 자동 복구: 토큰 무효화 → 재인증 → 원래 요청 재시도
            if httpResponse.statusCode == 401, requiresAuth, let self = self {
                self.token = nil // 만료 토큰 폐기
                self.ensureAuth { reAuthSuccess in
                    if reAuthSuccess {
                        // 새 토큰으로 동일 요청 재시도 (1회만)
                        self.performRequest(baseURL: baseURL, endpoint: endpoint, method: method, body: body, requiresAuth: false, completion: completion)
                    } else {
                        completion(.failure(NSError(domain: "HTTP", code: 401, userInfo: [NSLocalizedDescriptionKey: "재인증 실패"])))
                    }
                }
                return
            }
            
            if !(200...299).contains(httpResponse.statusCode) {
                completion(.failure(NSError(domain: "HTTP", code: httpResponse.statusCode, userInfo: nil)))
                return
            } else {
                // Success case logging (Optional, noisy)
            }
            
            do {
                if let json = try JSONSerialization.jsonObject(with: responseData) as? [String: Any] {
                    completion(.success(json))
                } else if let jsonArray = try JSONSerialization.jsonObject(with: responseData) as? [[String: Any]] {
                      // Compatibility
                      completion(.success(["data": jsonArray]))
                } else {
                      if let str = String(data: responseData, encoding: .utf8) {
                      }
                      completion(.failure(NSError(domain: "Invalid Format", code: -1, userInfo: nil)))
                }
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    // Array Response helper
    func performRequestList(baseURL: String? = nil, endpoint: String, method: String, isRetry: Bool = false, completion: @escaping (Result<[[String: Any]], Error>) -> Void) {
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
        
        guard let url = components?.url else {
            completion(.failure(NSError(domain: "Invalid URL", code: -1, userInfo: nil)))
            return 
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("true", forHTTPHeaderField: "ngrok-skip-browser-warning")
        request.timeoutInterval = 15.0 // [UX Fix] 60초 기본 대기가 아닌 15초로 단축
        
        // [Critical Fix] Use In-Memory Cached Token
        if let token = self.token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            // Debug Header
        } else {
        }
        
        
        URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            if let error = error { completion(.failure(error)); return }
            
            guard let httpResponse = response as? HTTPURLResponse else {
                 completion(.failure(NSError(domain: "No Response", code: 0, userInfo: nil)))
                 return
            }
            
            // Should be optional, but if compiler complains, handle gracefully
            let responseData = data ?? Data()
            
            // [Fix 2026-04-09] 401 자동 복구: 토큰 무효화 → 재인증 → 원래 요청 재시도 (1회 제한)
            if httpResponse.statusCode == 401, !isRetry, let self = self {
                self.token = nil // 만료 토큰 폐기
                self.ensureAuth { reAuthSuccess in
                    if reAuthSuccess {
                        // 새 토큰으로 동일 요청 재시도 (isRetry=true로 무한루프 방지)
                        self.performRequestList(baseURL: baseURL, endpoint: endpoint, method: method, isRetry: true, completion: completion)
                    } else {
                        completion(.failure(NSError(domain: "HTTP", code: 401, userInfo: [NSLocalizedDescriptionKey: "재인증 실패"])))
                    }
                }
                return
            }
            
            if !(200...299).contains(httpResponse.statusCode) {
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
                        completion(.failure(NSError(domain: "Server", code: -1, userInfo: ["msg": msg])))
                    } else {
                        completion(.failure(NSError(domain: "Invalid Format", code: -1, userInfo: nil)))
                    }
                } else {
                    completion(.failure(NSError(domain: "API", code: -1, userInfo: nil)))
                }
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }

        // MARK: - JWT Helper
    func decodeUserIdFromJWT(token: String) -> String? {
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
        completion(true)
        
        /*
        performRequest(endpoint: "/maum_on/sync_all/", method: "POST") { result in
            switch result {
            case .success:
                completion(true)
            case .failure(let error):
                completion(false)
            }
        }
        */
    }
    // MARK: - Kick Extensions (AI Weekly Letter & Relational Map)
    
    func fetchMyWeeklyLetters(completion: @escaping ([WeeklyLetter]?) -> Void) {
        ensureAuth { success in
            guard success else { completion(nil); return }
            
            self.performRequest(baseURL: self.baseURL, endpoint: "/kick/my-weekly-letters", method: "GET") { result in
                switch result {
                case .success(let data):
                    // 'data' might be wrapped or an array directly based on your `performRequest` logic.
                    // If it's a flat json dictionary, check for "data" key, or if it comes as dict with list.
                    // Our performRequest wraps lists in {"data": [...]} if the raw response was an array.
                    if let list = data["data"] as? [[String: Any]] {
                        do {
                            let jsonData = try JSONSerialization.data(withJSONObject: list)
                            let letters = try JSONDecoder().decode([WeeklyLetter].self, from: jsonData)
                            completion(letters)
                        } catch {
                            completion(nil)
                        }
                    } else {
                        completion(nil)
                    }
                case .failure(let error):
                    completion(nil)
                }
            }
        }
    }
    
    func fetchWeeklyLetterDetail(letterId: Int, completion: @escaping (WeeklyLetter?) -> Void) {
        ensureAuth { success in
            guard success else { completion(nil); return }
            
            self.performRequest(baseURL: self.baseURL, endpoint: "/kick/my-weekly-letters/\(letterId)", method: "GET") { result in
                switch result {
                case .success(let dict):
                    do {
                        let jsonData = try JSONSerialization.data(withJSONObject: dict)
                        let letter = try JSONDecoder().decode(WeeklyLetter.self, from: jsonData)
                        completion(letter)
                    } catch {
                        completion(nil)
                    }
                case .failure(let error):
                    completion(nil)
                }
            }
        }
    }
    
    func fetchMyRelationalMap(completion: @escaping (RelationalMapResponse?) -> Void) {
        ensureAuth { success in
            guard success else { completion(nil); return }
            
            self.performRequest(baseURL: self.baseURL, endpoint: "/kick/relational/my-map", method: "GET") { result in
                switch result {
                case .success(let dict):
                    do {
                        let jsonData = try JSONSerialization.data(withJSONObject: dict)
                        let mapData = try JSONDecoder().decode(RelationalMapResponse.self, from: jsonData)
                        completion(mapData)
                    } catch {
                        completion(nil)
                    }
                case .failure(let error):
                    completion(nil)
                }
            }
        }
    }
    
    // MARK: - Mind Bridge API (Phase 3/4/5)
    
    /// 서버에서 수신자 목록 조회
    func fetchBridgeRecipients(completion: @escaping ([String: Any]?) -> Void) {
        ensureAuth { success in
            guard success else { completion(nil); return }
            self.performRequest(baseURL: self.baseURL, endpoint: "/bridge/recipients", method: "GET") { result in
                switch result {
                case .success(let data): completion(data)
                case .failure(let error):
                    completion(nil)
                }
            }
        }
    }
    
    /// 서버에 수신자 추가
    func addBridgeRecipient(name: String, type: String, schedule: String, pin: String? = nil, completion: @escaping (Int?) -> Void) {
        ensureAuth { success in
            guard success else { completion(nil); return }
            var body: [String: Any] = [
                "name": name,
                "type": type,
                "share_schedule": schedule
            ]
            if let pin = pin { body["pin"] = pin }
            
            self.performRequest(baseURL: self.baseURL, endpoint: "/bridge/recipients", method: "POST", body: body) { result in
                switch result {
                case .success(let data):
                    if let recipientData = data["recipient"] as? [String: Any],
                       let serverId = recipientData["id"] as? Int {
                        completion(serverId)
                    } else {
                        completion(nil)
                    }
                case .failure(let error):
                    completion(nil)
                }
            }
        }
    }
    
    /// 서버에서 수신자 수정
    func updateBridgeRecipient(serverId: Int, updates: [String: Any], completion: @escaping (Bool) -> Void) {
        ensureAuth { success in
            guard success else { completion(false); return }
            self.performRequest(baseURL: self.baseURL, endpoint: "/bridge/recipients/\(serverId)", method: "PUT", body: updates) { result in
                switch result {
                case .success: completion(true)
                case .failure: completion(false)
                }
            }
        }
    }
    
    /// 서버에서 수신자 삭제
    func deleteBridgeRecipient(serverId: Int, completion: @escaping (Bool) -> Void) {
        ensureAuth { success in
            guard success else { completion(false); return }
            self.performRequest(baseURL: self.baseURL, endpoint: "/bridge/recipients/\(serverId)", method: "DELETE") { result in
                switch result {
                case .success: completion(true)
                case .failure: completion(false)
                }
            }
        }
    }
    
    /// 서버에 공유 깊이 설정 업데이트
    func updateBridgeDepth(serverId: Int, settings: [String: Bool], completion: @escaping (Bool) -> Void) {
        ensureAuth { success in
            guard success else { completion(false); return }
            let body: [String: Any] = ["depth_settings": settings]
            self.performRequest(baseURL: self.baseURL, endpoint: "/bridge/recipients/\(serverId)/depth", method: "PUT", body: body) { result in
                switch result {
                case .success: completion(true)
                case .failure: completion(false)
                }
            }
        }
    }
    
    /// 서버에서 공유 이력 조회
    func fetchBridgeShares(completion: @escaping ([[String: Any]]?) -> Void) {
        ensureAuth { success in
            guard success else { completion(nil); return }
            self.performRequest(baseURL: self.baseURL, endpoint: "/bridge/shares", method: "GET") { result in
                switch result {
                case .success(let data):
                    if let shares = data["shares"] as? [[String: Any]] {
                        completion(shares)
                    } else {
                        completion(nil)
                    }
                case .failure:
                    completion(nil)
                }
            }
        }
    }
    
    /// 서버에서 공유 미리보기 데이터 조회
    func prepareBridgeShare(recipientServerId: Int, completion: @escaping ([String: Any]?) -> Void) {
        ensureAuth { success in
            guard success else { completion(nil); return }
            self.performRequest(baseURL: self.baseURL, endpoint: "/bridge/prepare-share/\(recipientServerId)", method: "GET") { result in
                switch result {
                case .success(let data): completion(data)
                case .failure: completion(nil)
                }
            }
        }
    }
    
    /// 서버에 감정 데이터 공유 생성
    func createBridgeShare(recipientId: Int, startDate: String, endDate: String, data: [String: Any], sharedItems: String, completion: @escaping (Bool) -> Void) {
        ensureAuth { success in
            guard success else { completion(false); return }
            let body: [String: Any] = [
                "recipient_id": recipientId,
                "start_date": startDate,
                "end_date": endDate,
                "data": data,
                "shared_items": sharedItems
            ]
            self.performRequest(baseURL: self.baseURL, endpoint: "/bridge/share", method: "POST", body: body) { result in
                switch result {
                case .success: completion(true)
                case .failure: completion(false)
                }
            }
        }
    }
    
    /// 서버에서 열람 로그 조회
    func fetchBridgeViewLogs(completion: @escaping ([[String: Any]]?) -> Void) {
        ensureAuth { success in
            guard success else { completion(nil); return }
            self.performRequest(baseURL: self.baseURL, endpoint: "/bridge/view-logs", method: "GET") { result in
                switch result {
                case .success(let data):
                    if let logs = data["logs"] as? [[String: Any]] {
                        completion(logs)
                    } else {
                        completion(nil)
                    }
                case .failure:
                    completion(nil)
                }
            }
        }
    }
    
    /// 서버 브릿지 데이터 전체 삭제 (회원 탈퇴)
    func deleteAllBridgeData(completion: @escaping (Bool) -> Void) {
        ensureAuth { success in
            guard success else { completion(false); return }
            self.performRequest(baseURL: self.baseURL, endpoint: "/bridge/delete-all", method: "DELETE") { result in
                switch result {
                case .success: completion(true)
                case .failure: completion(false)
                }
            }
        }
    }
}
