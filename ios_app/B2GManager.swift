import SwiftUI
import Combine

// B2G(Business to Government) 연동 매니저
class B2GManager: ObservableObject {
    static let shared = B2GManager()
    
    // 연동 상태 관리 (AppStorage 대신 UserDefaults 직접 관리로 변경 - 안정성 확보)
    @Published var centerCode: String = "" {
        didSet {
            UserDefaults.standard.set(centerCode, forKey: "healthCenterCode")
        }
    }
    
    @Published var isLinked: Bool = false {
        didSet {
            UserDefaults.standard.set(isLinked, forKey: "isB2GLinked")
        }
    }
    
    @Published var lastSyncDate: Double = 0 {
        didSet {
            UserDefaults.standard.set(lastSyncDate, forKey: "lastSyncDate")
        }
    }
    
    @Published var isSyncing = false
    
    private init() {
        // Load Saved State
        self.centerCode = UserDefaults.standard.string(forKey: "healthCenterCode") ?? ""
        self.isLinked = UserDefaults.standard.bool(forKey: "isB2GLinked")
        self.lastSyncDate = UserDefaults.standard.double(forKey: "lastSyncDate")
    }
    
    // 보건소 코드 연결 시도 (실제 서버 연동)
    func connect(code: String, completion: @escaping (Bool, String) -> Void) {
        let trimmedCode = code.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedCode.isEmpty else {
            completion(false, "코드를 입력해주세요.")
            return
        }
        
        isSyncing = true
        
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
                        
                        // 센터 이름 저장 (옵션)
                        if let center = json["center"] as? [String: Any],
                           let centerName = center["name"] as? String {
                            UserDefaults.standard.set(centerName, forKey: "linkedCenterName")
                            completion(true, "\(centerName)와 성공적으로 연결되었습니다!")
                        } else {
                            completion(true, "연동에 성공했습니다!")
                        }
                        
                        self.syncData() // 연결 즉시 데이터 전송
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
    
    // 연동 해제
    func disconnect() {
        self.centerCode = ""
        self.isLinked = false
        self.lastSyncDate = 0
    }
    
    // 백그라운드 데이터 동기화 (양방향: Fetch -> Merge -> Push)
    func syncData() {
        guard isLinked, !centerCode.isEmpty else { return }
        
        isSyncing = true
        print("🔄 [B2G] Start Full Sync (Pull + Push)...")
        
        // 1. Pull (Server -> App)
        APIService.shared.fetchDiaries { [weak self] serverData in
            guard let self = self else { return }
            
            if let data = serverData {
                // Merge Data (Main Thread) -> Then Push
                LocalDataManager.shared.mergeServerDiaries(data) {
                    self.pushData()
                }
            } else {
                print("⚠️ [Sync] Fetch failed or no data, skipping merge.")
                // Failure case runs on background thread, so dispatch to main
                DispatchQueue.main.async {
                    self.pushData()
                }
            }
        }
    }
    
    // 기존의 단방향 Push 로직 분리
    func pushData() {
        print("🔄 [B2G] Push Local Data to Server...")
        
        // 1. 로컬 데이터 수집
        // CRITICAL FIX: Must match APIService default ("Guest") to ensure consistent User Identity
        let nickname = UserDefaults.standard.string(forKey: "userNickname") ?? "Guest"
        print("👤 [B2G] Syncing Identity: \(nickname)")
        
        let diaries = LocalDataManager.shared.diaries
        
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
                "ai_prediction": diary.ai_prediction ?? ""
            ]
        }
        
        let body: [String: Any] = [
            "center_code": centerCode,
            "user_nickname": nickname,
            "risk_level": UserDefaults.standard.integer(forKey: "userRiskLevel"),
            "mood_metrics": metrics
        ]
        
        // 3. 백엔드 전송 (APIService 사용)
        APIService.shared.syncCenterData(payload: body) { success in
            DispatchQueue.main.async {
                self.isSyncing = false
                if success {
                    self.lastSyncDate = Date().timeIntervalSince1970
                }
            }
        }
    }
}
