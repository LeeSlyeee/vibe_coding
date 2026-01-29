
import Foundation
import Combine

class APIService {
    static let shared = APIService()
    
    // 로컬 서버 (테스트용) - 실제 배포 시 OCI 주소로 변경 필요
    // [SSH Tunnel] 외부 접속용 URL 사용 (로컬 네트워크 권한 우회)
    // 로컬 서버 (테스트용) - 외부 접속용 Tunnel URL (Verified Active)
    // 실기기 테스트용 (Local Network IP - Updated)
    // iPhone과 Mac이 동일한 Wi-Fi에 있어야 합니다.
    private let baseURL = "http://192.168.0.22:5001/api"

    
    private var token: String? {
        get { UserDefaults.standard.string(forKey: "serverAuthToken") }
        set { UserDefaults.standard.set(newValue, forKey: "serverAuthToken") }
    }
    
    private init() {}
    
    // MARK: - Auth (닉네임 기반 자동 로그인)
    func ensureAuth(completion: @escaping (Bool) -> Void) {
        let nickname = UserDefaults.standard.string(forKey: "userNickname") ?? "Guest"
        // 비밀번호는 로컬 모드 사용자의 편의를 위해 고정값 사용 (보안 강화 필요 시 수정 가능)
        let password = "ios_auto_password_1234" 
        
        // 백엔드 B2G 로직과 통일: "app_" 접두사 사용
        // VerifyCenterCodeView가 "app_{nickname}"으로 유저를 생성하므로, 로그인도 동일하게 수행해야 함.
        let username = "app_" + nickname
        let body: [String: Any] = ["username": username, "password": password]
        
        performRequest(endpoint: "/login", method: "POST", body: body) { result in
            switch result {
            case .success(let response):
                if let accessToken = response["access_token"] as? String {
                    self.token = accessToken
                    print("🌐 [API] Server Login Success: \(nickname)")
                    completion(true)
                } else {
                    completion(false)
                }
            case .failure:
                // 로그인 실패 시 회원가입 시도
                print("🌐 [API] Login failed, trying registration for: \(nickname)")
                self.performRequest(endpoint: "/register", method: "POST", body: body) { regResult in
                    switch regResult {
                    case .success:
                        // 회원가입 성공 후 다시 로그인
                         self.performRequest(endpoint: "/login", method: "POST", body: body) { loginRetry in
                            if case .success(let retryResp) = loginRetry,
                               let accessToken = retryResp["access_token"] as? String {
                                self.token = accessToken
                                completion(true)
                            } else {
                                completion(false)
                            }
                         }
                    case .failure(let err):
                        print("🌐 [API] Registration failed: \(err)")
                        completion(false)
                    }
                }
            }
        }
    }
    
    // MARK: - Diary Sync
    
    // 1. 일기 내용 우선 저장 (분석 전)
    func saveDiaryInitial(_ diary: Diary) {
        ensureAuth { success in
            guard success else { return }
            
            // 매핑: iOS Diary -> Backend Payload
            let payload: [String: Any] = [
                "created_at": diary.date ?? "",
                "event": diary.event ?? "",
                "emotion_desc": diary.emotion_desc ?? "", // 어떤 감정이 들었나요?
                "emotion_meaning": diary.emotion_meaning ?? "",
                "self_talk": diary.self_talk ?? "",
                "mood_level": diary.mood_level,
                "weather": diary.weather ?? "",
                "sleep_condition": diary.sleep_desc ?? ""
            ]
            
            self.performRequest(endpoint: "/diaries", method: "POST", body: payload) { result in
                switch result {
                case .success(let data):
                    print("✅ [API] Diary Initial Saved to Server. ID: \(data["id"] ?? "null")")
                case .failure(let error):
                    print("❌ [API] Save Failed: \(error.localizedDescription)")
                }
            }
        }
    }
    
    // 2. 분석 데이터 업데이트 (분석 완료 후)
    // 백엔드는 일기 날짜(created_at)를 기준으로 찾거나, ID를 알면 좋음.
    // 여기서는 날짜 기반으로 업데이트하거나(백엔드 로직에 따라), 
    // 혹은 방금 저장한 일기를 다시 POST하면 백엔드가 "같은 날짜면 수정"으로 처리하는지 확인 필요.
    // 현재 백엔드 로직상 같은 날짜 POST는 '새 일기'로 인식될 수 있으므로,
    // iOS에서 Server ID를 관리하거나, 백엔드 검색 API를 사용해야 함.
    // *간소화 전략*: iOS는 Server ID를 모르므로, '날짜'를 기준으로 서버에서 조회 후 업데이트하는 로직이 필요.
    // 하지만 현재 백엔드 API는 PUT /diaries/<id> 만 지원함.
    // -> 따라서, POST 시 반환된 ID를 저장하거나, createDiary를 다시 호출하면 안됨.
    // **해결책**: 백엔드에 '날짜로 일기 찾기' -> 'ID 획득' -> '업데이트' 프로세스 수행
    
    func updateDiaryAnalysis(_ diary: Diary) {
        ensureAuth { success in
            guard success else { return }
            
            // 1. 해당 날짜 일기 ID 조회
            let dateStr = diary.date ?? ""
            self.performRequest(endpoint: "/diaries/date/\(dateStr)", method: "GET") { result in
                switch result {
                case .success(let data):
                    // 이미 존재하는 일기가 있음 -> ID 추출
                    if let id = data["_id"] as? String {
                        self.pushAnalysisUpdate(diaryId: id, diary: diary)
                    } else if let id = data["id"] as? String {
                        self.pushAnalysisUpdate(diaryId: id, diary: diary)
                    }
                case .failure:
                    // 없다면? 아직 저장이 안된 것 -> saveInitial 호출
                    print("⚠️ [API] Diary not found on server, saving as new.")
                    self.saveDiaryInitial(diary)
                }
            }
        }
    }
    
    private func pushAnalysisUpdate(diaryId: String, diary: Diary) {
         let payload: [String: Any] = [
            // 기존 내용 유지 + 분석 내용 추가
            "event": diary.event ?? "",
            "mood_level": diary.mood_level,
            
            // AI Analysis Data
            "ai_comment": diary.ai_comment ?? "",
            "ai_advice": diary.ai_advice ?? "",
            "ai_analysis": diary.ai_analysis ?? "",
            "ai_prediction": diary.ai_prediction ?? ""
        ]
        
        self.performRequest(endpoint: "/diaries/\(diaryId)", method: "PUT", body: payload) { result in
            if case .success = result {
                print("✅ [API] AI Analysis Updated to Server.")
            } else {
                print("❌ [API] Analysis Update Failed.")
            }
        }
    }
    
    // MARK: - B2G Data Sync (Push)
    func syncCenterData(payload: [String: Any], completion: @escaping (Bool) -> Void) {
        // B2G Sync는 Center Code로 인증하므로 JWT 불필요
        performRequest(endpoint: "/v1/centers/sync-data/", method: "POST", body: payload, requiresAuth: false) { result in
            switch result {
            case .success(let json):
                if let success = json["success"] as? Bool, success == true {
                    print("✅ [APIService] Data Sync Success")
                    completion(true)
                } else {
                    print("⚠️ [APIService] Data Sync returned false")
                    completion(false)
                }
            case .failure(let error):
                print("❌ [APIService] Data Sync Error: \(error.localizedDescription)")
                completion(false)
            }
        }
    }
    
    // 1. 기관 코드 문의 (Verification) + 사용자 정보 등록 (Handshake)
    func verifyCenterCode(_ code: String, completion: @escaping (Result<[String: Any], Error>) -> Void) {
        let nickname = UserDefaults.standard.string(forKey: "userNickname") ?? "Guest"
        let payload = [
            "code": code,
            "user_nickname": nickname
        ]
        // B2G 엔드포인트: /v1/centers/verify-code/
        // Public Endpoint이므로 Auth Header를 보내지 않아 401 에러 방지
        performRequest(endpoint: "/v1/centers/verify-code/", method: "POST", body: payload, requiresAuth: false) { result in
            switch result {
            case .success(let data):
                print("✅ [B2G] Center Code Verified: \(data)")
                completion(.success(data))
            case .failure(let error):
                print("❌ [B2G] Verification Failed: \(error)")
                completion(.failure(error))
            }
        }
    }
    
    // 2. 기관 연동 확정 (Connection)
    // Supports both Int (Legacy) and String (MongoDB ObjectId)
    func connectToCenter(centerId: Any, completion: @escaping (Bool) -> Void) {
        ensureAuth { success in
            guard success else {
                completion(false)
                return
            }
            
            // Convert to appropriate type for JSON body
            var payload: [String: Any] = [:]
            if let idInt = centerId as? Int {
                payload["center_id"] = idInt
            } else if let idStr = centerId as? String {
                 payload["center_id"] = idStr
            } else {
                print("❌ [APIService] Invalid Center ID Type")
                completion(false)
                return
            }

            // B2G 연동 엔드포인트: /v1/b2g_sync/connect/
            self.performRequest(endpoint: "/v1/b2g_sync/connect/", method: "POST", body: payload) { result in
                switch result {
                case .success:
                    print("✅ [B2G] Successfully Connected to Center.")
                    completion(true)
                case .failure(let error):
                    print("❌ [B2G] Connection Failed: \(error)")
                    completion(false)
                }
            }
        }
    }
    
    
    // 3. 일기 목록 가져오기 (서버 -> 앱)
    func fetchDiaries(completion: @escaping ([ [String: Any] ]?) -> Void) {
        ensureAuth { success in
            guard success else { completion(nil); return }
            
            // GET /diaries returns a JSON Array (List) by default in DRF without pagination
            self.performRequestList(endpoint: "/diaries", method: "GET") { result in
                switch result {
                case .success(let list):
                    completion(list)
                case .failure(let error):
                    print("❌ [API] Fetch Diaries Failed: \(error)")
                    completion(nil)
                }
            }
        }
    }
    
    // MARK: - Chat (Server-based)
    func sendChatMessage(message: String, history: [[String: String]], completion: @escaping (Result<String, Error>) -> Void) {
        ensureAuth { success in
            guard success else {
                completion(.failure(NSError(domain: "Auth", code: 401, userInfo: [NSLocalizedDescriptionKey: "로그인이 필요합니다."])))
                return
            }
            
            let payload: [String: Any] = [
                "message": message,
                "history": history
            ]
            
            // AI Chat Endpoint: /ai/chat (가정) 또는 /chat
            // 백엔드 로그를 볼 수 없으므로, 표준적인 /chat 시도 후 실패 시 /ai/chat 시도 로직은 복잡하니, 우선 /chat으로 통일
            self.performRequest(endpoint: "/chat", method: "POST", body: payload) { result in
                switch result {
                case .success(let data):
                    // 응답 필드: 'response' or 'message' or 'reply'
                    if let reply = data["response"] as? String ?? data["message"] as? String ?? data["reply"] as? String {
                        completion(.success(reply))
                    } else {
                        completion(.failure(NSError(domain: "API", code: -1, userInfo: [NSLocalizedDescriptionKey: "서버 응답 형식을 알 수 없습니다."])))
                    }
                case .failure(let error):
                    completion(.failure(error))
                }
            }
        }
    }
    

    // MARK: - Core Networking
    private func performRequest(endpoint: String, method: String, body: [String: Any]? = nil, requiresAuth: Bool = true, completion: @escaping (Result<[String: Any], Error>) -> Void) {
        guard let url = URL(string: baseURL + endpoint) else {
            completion(.failure(NSError(domain: "Invalid URL", code: -1, userInfo: nil)))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148", forHTTPHeaderField: "User-Agent")
        request.setValue("true", forHTTPHeaderField: "Bypass-Tunnel-Reminder")
        request.setValue("true", forHTTPHeaderField: "ngrok-skip-browser-warning")
        
        if requiresAuth, let token = self.token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        if let body = body {
            request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        }
        
        // Debug Log
        print("🚀 [API] \(method) \(endpoint)")
        if let body = body { print("   Body: \(body)") }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("❌ [API] Connection Error: \(error.localizedDescription)")
                completion(.failure(error))
                return
            }
            
            guard let data = data, let httpResponse = response as? HTTPURLResponse else {
                completion(.failure(NSError(domain: "No Data", code: -1, userInfo: nil)))
                return
            }
            
            // Raw Response Debugging (Status Code 확인)
            print("📡 [API] Response: \(httpResponse.statusCode)")
            
            // HTTP Status Code Check (200~299만 성공 처리)
            guard (200...299).contains(httpResponse.statusCode) else {
                var errorMsg = "서버 에러 (\(httpResponse.statusCode))"
                
                // 에러 본문을 읽어서 상세 메시지 추출 시도
                if let str = String(data: data, encoding: .utf8) {
                    // Try to parse error message from JSON
                    if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                        let serverMsg = json["detail"] as? String 
                            ?? json["message"] as? String 
                            ?? json["error"] as? String
                        
                        if let validMsg = serverMsg {
                            errorMsg = validMsg
                        }
                    } else {
                        // JSON 파싱 실패 시 원본 텍스트 일부 표시 (HTML일 수 있음)
                        if str.contains("<html") {
                            errorMsg += " - 잘못된 응답 형식 (HTML)"
                        } else {
                            errorMsg += " - \(str.prefix(50))"
                        }
                    }
                }
                
                completion(.failure(NSError(domain: "HTTPError", code: httpResponse.statusCode, userInfo: [NSLocalizedDescriptionKey: errorMsg])))
                return
            }
            
            // Raw String Check
            /*
            if let rawString = String(data: data, encoding: .utf8) {
               // print("📩 [API] Raw Response Body: \(rawString)")
            }
            */
            
            do {
                if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                    completion(.success(json))
                } else if let jsonArray = try JSONSerialization.jsonObject(with: data) as? [[String: Any]] {
                     // Array handling if needed locally or wrap it
                     completion(.success(["data": jsonArray]))
                } else {
                    // JSON 형식이지만 Dictionary가 아닌 경우
                     print("⚠️ [API] Unexpected JSON Format")
                     completion(.failure(NSError(domain: "Invalid JSON Format", code: -1, userInfo: nil)))
                }
            } catch {
                print("❌ [API] JSON Decode Error: \(error.localizedDescription)")
                
                var debugMsg = "데이터 형식이 올바르지 않습니다."
                if let str = String(data: data, encoding: .utf8) {
                    print("   👉 Received Data: \(str)")
                    if str.contains("<html") {
                        debugMsg = "서버 URL 오류 (HTML 페이지가 반환됨)"
                    } else {
                        debugMsg += " (원본: \(str.prefix(30))...)"
                    }
                }
                completion(.failure(NSError(domain: "JSONError", code: -2, userInfo: [NSLocalizedDescriptionKey: debugMsg])))
            }
        }.resume()
    }
    
    // Array Response helper
    private func performRequestList(endpoint: String, method: String, completion: @escaping (Result<[[String: Any]], Error>) -> Void) {
        guard let url = URL(string: baseURL + endpoint) else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148", forHTTPHeaderField: "User-Agent")
        request.setValue("true", forHTTPHeaderField: "Bypass-Tunnel-Reminder")
        request.setValue("true", forHTTPHeaderField: "ngrok-skip-browser-warning")
        
        if let token = self.token {
            request.addValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else { return }
            
            do {
                if let json = try JSONSerialization.jsonObject(with: data) as? [[String: Any]] {
                    completion(.success(json))
                } else {
                    print("❌ [API] Expected Array but got something else.")
                    if let raw = String(data: data, encoding: .utf8) {
                        print("   👉 Raw Response: \(raw)")
                    }
                    completion(.failure(NSError(domain: "API", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid JSON format (Not Array)"])))
                }
            } catch {
                print("❌ [API] JSON Decode Error: \(error.localizedDescription)")
                if let raw = String(data: data, encoding: .utf8) {
                    print("   👉 Raw Response (Caused Error): \(raw)")
                }
                completion(.failure(error))
            }
        }.resume()
    }
}
