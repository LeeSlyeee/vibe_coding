import SwiftUI
import Combine

// B2G(Business to Government) 연동 매니저
class B2GManager: ObservableObject {
    static let shared = B2GManager()
    
    // 연동 상태 관리 (Fort Knox Pattern)
    // 1. Access Control: private(set) prevents external modification
    @Published private(set) var centerCode: String = "" {
        didSet {
            if centerCode.isEmpty && !oldValue.isEmpty {
            }
            // [Fix] Auto-Save on Change
            self.saveState()
        }
    }
    @Published private(set) var isLinked: Bool = false
    @Published private(set) var lastSyncDate: Double = 0
    @Published var isSyncing = false
    
    // Explicit Save Helper (Dual Layer)
    private func saveState() {
        UserDefaults.standard.set(centerCode, forKey: "healthCenterCode")
        UserDefaults.standard.set(centerCode, forKey: "healthCenterCode_BACKUP") // Save Backup
        UserDefaults.standard.set(isLinked, forKey: "isB2GLinked")
        UserDefaults.standard.set(lastSyncDate, forKey: "lastSyncDate")
    }
    
    private init() {
        // 2. Auto-Recovery (Self-Healing)
        let mainCode = UserDefaults.standard.string(forKey: "healthCenterCode") ?? ""
        let backupCode = UserDefaults.standard.string(forKey: "healthCenterCode_BACKUP") ?? ""
        
        if !mainCode.isEmpty {
            self.centerCode = mainCode
            // [Fix] Trust the Code: If code exists, ALWAYS treat as linked.
            self.isLinked = true
            
            // If stored boolean was false, correct it now.
            if !UserDefaults.standard.bool(forKey: "isB2GLinked") {
                UserDefaults.standard.set(true, forKey: "isB2GLinked")
            }
        } else if !backupCode.isEmpty {
            self.centerCode = backupCode
            self.isLinked = true
            // Repair Main
            UserDefaults.standard.set(backupCode, forKey: "healthCenterCode")
            UserDefaults.standard.set(true, forKey: "isB2GLinked")
        }
        
        self.lastSyncDate = UserDefaults.standard.double(forKey: "lastSyncDate")
    }
    
    // 보건소 코드 연결 시도 (실제 서버 연동)
    func connect(code: String, completion: @escaping (Bool, String) -> Void) {
        let trimmedCode = code.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedCode.isEmpty else {
            completion(false, "코드를 입력해주세요.")
            return
        }
        
        DispatchQueue.main.async { self.isSyncing = true }
        
        // Use APIService for centralized URL and Header management
        // This also ensures 'user_nickname' is sent (fixed in APIService)
        APIService.shared.verifyCenterCode(trimmedCode) { [weak self] result in
            guard let self = self else { return }
            
            DispatchQueue.main.async {
                self.isSyncing = false // Ensure isSyncing is reset
                
                switch result {
                case .success(let json):
                    if let valid = json["valid"] as? Bool, valid == true {
                        // 성공
                        self.centerCode = trimmedCode.uppercased()
                        self.isLinked = true
                        
                        // [Identity Unification] 
                        // 서버가 계정 통합을 알리면, 앱의 정체성을 갈아끼웁니다.
                        var successMessage = "연동에 성공했습니다!"
                        
                        if let ownerNick = json["owner_nickname"] as? String, !ownerNick.isEmpty {
                            
                            // 1. Update Identity
                            UserDefaults.standard.set(ownerNick, forKey: "userNickname")
                            if let fullUsername = json["owner_username"] as? String {
                                UserDefaults.standard.set(fullUsername, forKey: "app_username") // if needed
                            }
                            
                            // [Fix] B2G 연동 유저는 PHQ-9 검사 건너뛰기 (기관 관리 대상)
                            UserDefaults.standard.set(true, forKey: "hasCompletedAssessment")
                            
                            // 2. Set Message
                            if let msg = json["message"] as? String {
                                successMessage = msg
                            } else {
                                successMessage = "기존 계정(\(ownerNick))과 통합되었습니다."
                            }
                        }
                        
                        // [Fix] Explicit Save
                        self.saveState()
                        
                        // 센터 이름 저장 (옵션)
                        if let center = json["center"] as? [String: Any],
                           let centerName = center["name"] as? String {
                            UserDefaults.standard.set(centerName, forKey: "linkedCenterName")
                        }
                        
                        completion(true, successMessage)
                        
                        // [Critical] Identity Changed -> Must Force Pull All Data
                        self.syncData(force: true) 
                        
                    } else {
                        // 실패 메시지 파싱
                        let msg = json["error"] as? String ?? json["message"] as? String ?? "유효하지 않은 기관 코드입니다."
                        completion(false, msg)
                    }
                case .failure(let error):
                    completion(false, error.localizedDescription)
                }
            }
        }
    }
    
    // 연동 해제 (User Action Only)
    // [UNLOCKED] Removed safety guard for immediate disconnect
    func disconnect(force: Bool = false) {
        guard force else {
            return
        }
        
        self.centerCode = ""
        self.isLinked = false
        self.lastSyncDate = 0
        
        UserDefaults.standard.removeObject(forKey: "healthCenterCode")
        UserDefaults.standard.removeObject(forKey: "healthCenterCode_BACKUP") // Clear Backup
        UserDefaults.standard.removeObject(forKey: "isB2GLinked")
        UserDefaults.standard.removeObject(forKey: "linkedCenterName")
        UserDefaults.standard.removeObject(forKey: "lastSyncDate")
        
        // Notify UI
        objectWillChange.send()
    }
    
    // 백그라운드 데이터 동기화 (양방향: Fetch -> Merge -> Push)
    // [Differential Sync] force: true -> Full Sync
    func syncData(force: Bool = false) {
        // [Create Barrier] 이미 동기화 중이면 중복 실행 방지
        if isSyncing {
            return
        }
        
        // [Self-Healing] Before sync, check if we have code but bad state
        if !centerCode.isEmpty && !isLinked {
            DispatchQueue.main.async {
                self.isLinked = true
                self.saveState()
            }
        }
        
        guard isLinked, !centerCode.isEmpty else { return }
        
        DispatchQueue.main.async { self.isSyncing = true }
        
        // 1. Pull (Server -> App)
        APIService.shared.fetchDiaries { [weak self] serverData in
            guard let self = self else { return }
            
            if let data = serverData {
                // Merge Data (Main Thread) -> Then Push
                DispatchQueue.main.async {
                    LocalDataManager.shared.mergeServerDiaries(data) {
                        self.pushData(force: force)
                    }
                }
            } else {
                // Failure case runs on background thread, so dispatch to main
                DispatchQueue.main.async {
                    self.pushData(force: force)
                }
            }
        }
    }
    
    // [Differential Sync] force: true -> Full Upload, force: false -> Delta Upload
    func pushData(force: Bool = false) {
        
        // 1. 로컬 데이터 수집
        // [Fix] Single Source of Truth: authUsername 우선 사용
        guard let nickname = UserDefaults.standard.string(forKey: "authUsername")
            ?? UserDefaults.standard.string(forKey: "app_username")
            ?? UserDefaults.standard.string(forKey: "userNickname") else {
            DispatchQueue.main.async { self.isSyncing = false }
            return
        }
        
        var diaries = LocalDataManager.shared.diaries
        
        // [Optimized] Filter only Dirty Items unless Force Sync
        if !force {
            diaries = diaries.filter { $0.isSynced != true }
        }
        
        if diaries.isEmpty {
            DispatchQueue.main.async { self.isSyncing = false }
            return
        }
        
        
        // 2. 일기 데이터를 심플한 포맷으로 변환 -> 상세 내용 포함으로 강화
        let metrics = diaries.map { diary -> [String: Any] in
            return [
                "created_at": diary.created_at ?? diary.date ?? "", // Precise timestamp
                "date": diary.date ?? "",
                "score": diary.mood_level,
                "event": diary.event ?? "",
                "emotion": diary.emotion_desc ?? "",
                "meaning": diary.emotion_meaning ?? "",
                "selftalk": diary.self_talk ?? "",
                "sleep": diary.sleep_desc ?? "",
                // AI Data
                "ai_comment": diary.ai_comment ?? "",
                "ai_advice": diary.ai_advice ?? "",
                "ai_analysis": diary.ai_analysis ?? "",
                "ai_prediction": diary.ai_prediction ?? "",
                
                // [New] Rich Data Fields
                "weather": diary.weather ?? "",
                "medication_taken": diary.medication_taken,
                "symptoms": diary.symptoms ?? [], // Array of strings
                "gratitude": diary.gratitude_note ?? "",
                "temperature": diary.temperature ?? 0.0,
                "medication_desc": diary.medication_desc ?? ""
            ]
        }
        
        let body: [String: Any] = [
            "center_code": centerCode,
            "user_nickname": nickname,
            "risk_level": UserDefaults.standard.integer(forKey: "userRiskLevel"),
            "mood_metrics": metrics
        ]
        
        // 3. 백엔드 전송 (APIService 사용)
        APIService.shared.syncCenterData(payload: body) { success, errorMsg in
            // [Sync Chain] Trigger 217 Web Sync immediately after B2G Sync
            if success {
                
                // [Optimization] Mark these specific diaries as Synced locally
                let sentIds = diaries.compactMap { $0.id }
                LocalDataManager.shared.markAsSynced(ids: sentIds)
                
                // [Fix] Save Sync Date Explicitly
                DispatchQueue.main.async { 
                    self.lastSyncDate = Date().timeIntervalSince1970 
                    self.saveState() 
                }
                
                // Trigger Legacy Web Sync (if needed)
                APIService.shared.triggerBulkSync { _ in 
                }
            }
            
            DispatchQueue.main.async {
                self.isSyncing = false
                if success {
                    self.lastSyncDate = Date().timeIntervalSince1970
                } else if let msg = errorMsg {
                     // 센터 코드가 만료되었거나 삭제된 경우 -> 연결 해제
                     
                     // [CRITICAL SAFETY]
                     // 절대 자동으로 연결을 해제하지 않음.
                     // 사용자가 직접 끊기 전까지는 코드를 유지함.
                     if msg.contains("유효하지 않은 센터 코드") {
                     }
                }
            }
        }
    }
    
    // [New] Pull Only Mode (User Request)
    // 서버 데이터만 강제로 내려받아 덮어쓰기/병합
    func pullDataFromServer(completion: @escaping (Bool, String) -> Void) {
        if isSyncing {
            completion(false, "이미 동기화 작업이 진행 중입니다.")
            return
        }
        
        DispatchQueue.main.async { self.isSyncing = true }
        
        APIService.shared.fetchDiaries { [weak self] serverData in
            guard let self = self else { return }
            
            if let data = serverData {
                DispatchQueue.main.async {
                    // 병합 로직 수행
                    LocalDataManager.shared.mergeServerDiaries(data) {
                        self.isSyncing = false
                        self.lastSyncDate = Date().timeIntervalSince1970
                        self.saveState()
                        completion(true, "서버에서 \(data.count)개의 데이터를 가져왔습니다.")
                    }
                }
            } else {
                DispatchQueue.main.async {
                    self.isSyncing = false
                    completion(false, "데이터를 가져오지 못했습니다. (서버 응답 없음)")
                }
            }
        }
    }

    
    // [Dev] Force Link Helper
    func forceLink(code: String) {
        self.centerCode = code
        self.isLinked = true
        self.saveState()
    }
}
