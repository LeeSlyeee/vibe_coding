import Foundation

// MARK: - Phase 3/4/5: 마음 브릿지 데이터 관리
// 로컬(UserDefaults) + 서버(Flask /api/bridge/*) 하이브리드
//
// 전략: 로컬 우선 저장 → 백그라운드 서버 동기화
// 서버 실패 시 로컬 데이터 유지 (오프라인 안전)

// MARK: - 모델

enum RecipientType: String, Codable, CaseIterable {
    case family = "family"
    case counselor = "counselor"
}

enum ShareSchedule: String, Codable, CaseIterable {
    case daily = "daily"
    case weekly = "weekly"
    case biweekly = "biweekly"
    case manual = "manual"
    
    var displayName: String {
        switch self {
        case .daily: return "매일"
        case .weekly: return "매주"
        case .biweekly: return "격주"
        case .manual: return "수동"
        }
    }
}

struct BridgeRecipient: Identifiable, Codable {
    let id: String
    var serverId: Int?                // 서버 PK (동기화 후 할당)
    var name: String
    var type: RecipientType
    var isActive: Bool
    var shareSchedule: ShareSchedule?
    var createdAt: Date
    
    init(name: String, type: RecipientType, schedule: ShareSchedule? = nil) {
        self.id = UUID().uuidString
        self.serverId = nil
        self.name = name
        self.type = type
        self.isActive = true
        self.shareSchedule = schedule
        self.createdAt = Date()
    }
    
    /// 서버 동기화용 전체 필드 init
    init(id: String, serverId: Int?, name: String, type: RecipientType, isActive: Bool, shareSchedule: ShareSchedule?, createdAt: Date) {
        self.id = id
        self.serverId = serverId
        self.name = name
        self.type = type
        self.isActive = isActive
        self.shareSchedule = shareSchedule
        self.createdAt = createdAt
    }
}

struct DepthSettings: Codable {
    var moodStatus: Bool
    var moodGraph: Bool
    var aiSummary: Bool
    var detailedAnalysis: Bool
    var triggerKeywords: Bool
    
    static let `default` = DepthSettings(
        moodStatus: false,
        moodGraph: false,
        aiSummary: false,
        detailedAnalysis: false,
        triggerKeywords: false
    )
    
    var enabledCount: Int {
        [moodStatus, moodGraph, aiSummary, detailedAnalysis, triggerKeywords].filter { $0 }.count
    }
    
    /// 서버 전송용 Dictionary
    var toServerDict: [String: Bool] {
        [
            "mood_status": moodStatus,
            "mood_graph": moodGraph,
            "ai_summary": aiSummary,
            "detailed_analysis": detailedAnalysis,
            "trigger_keywords": triggerKeywords
        ]
    }
}

struct ShareHistoryEntry: Identifiable, Codable {
    let id: String
    let recipientName: String
    let sharedItems: String
    let date: Date
    var wasViewed: Bool
    
    var formattedDate: String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "ko_KR")
        formatter.dateFormat = "M/d (E) HH:mm"
        return formatter.string(from: date)
    }
    
    init(recipientName: String, sharedItems: String) {
        self.id = UUID().uuidString
        self.recipientName = recipientName
        self.sharedItems = sharedItems
        self.date = Date()
        self.wasViewed = false
    }
}

// MARK: - Manager

class MindBridgeManager: ObservableObject {
    static let shared = MindBridgeManager()
    
    @Published var recipients: [BridgeRecipient] = []
    @Published var depthSettingsMap: [String: DepthSettings] = [:]
    @Published var shareHistory: [ShareHistoryEntry] = []
    
    private let recipientsKey = "mindbridge_recipients"
    private let depthSettingsKey = "mindbridge_depth_settings"
    private let shareHistoryKey = "mindbridge_share_history"
    
    var familyRecipients: [BridgeRecipient] {
        recipients.filter { $0.type == .family }
    }
    
    var counselorRecipients: [BridgeRecipient] {
        recipients.filter { $0.type == .counselor }
    }
    
    private init() {
        loadAll()
        // 앱 시작 시 서버 동기화 시도
        syncFromServer()
    }
    
    // ═══════════════════════════════════════════
    // 수신자 관리 (로컬 + 서버)
    // ═══════════════════════════════════════════
    
    func addRecipient(name: String, type: RecipientType, schedule: ShareSchedule?) {
        var recipient = BridgeRecipient(name: name, type: type, schedule: schedule)
        recipients.append(recipient)
        depthSettingsMap[recipient.id] = .default
        saveLocal()
        
        // 서버 동기화
        APIService.shared.addBridgeRecipient(
            name: name,
            type: type.rawValue,
            schedule: schedule?.rawValue ?? "weekly"
        ) { [weak self] serverId in
            guard let self = self, let serverId = serverId else { return }
            DispatchQueue.main.async {
                if let idx = self.recipients.firstIndex(where: { $0.id == recipient.id }) {
                    self.recipients[idx].serverId = serverId
                    self.saveLocal()
                    print("🌉 [MindBridge] 서버 동기화 완료: \(name) (ID: \(serverId))")
                }
            }
        }
    }
    
    func removeRecipient(id: String) {
        let target = recipients.first(where: { $0.id == id })
        recipients.removeAll { $0.id == id }
        depthSettingsMap.removeValue(forKey: id)
        saveLocal()
        
        // 서버에서도 삭제
        if let serverId = target?.serverId {
            APIService.shared.deleteBridgeRecipient(serverId: serverId) { success in
                if success {
                    print("🌉 [MindBridge] 서버 수신자 삭제 완료: \(serverId)")
                }
            }
        }
    }
    
    func updateRecipient(id: String, isActive: Bool, schedule: ShareSchedule?) {
        if let index = recipients.firstIndex(where: { $0.id == id }) {
            recipients[index].isActive = isActive
            if let schedule = schedule {
                recipients[index].shareSchedule = schedule
            }
            saveLocal()
            
            // 서버 동기화
            if let serverId = recipients[index].serverId {
                var updates: [String: Any] = ["is_active": isActive]
                if let schedule = schedule { updates["share_schedule"] = schedule.rawValue }
                APIService.shared.updateBridgeRecipient(serverId: serverId, updates: updates) { _ in }
            }
        }
    }
    
    // ═══════════════════════════════════════════
    // Phase 4: 공유 깊이 설정
    // ═══════════════════════════════════════════
    
    func getDepthSettings(for recipientId: String) -> DepthSettings {
        depthSettingsMap[recipientId] ?? .default
    }
    
    func updateDepthSettings(for recipientId: String, settings: DepthSettings) {
        depthSettingsMap[recipientId] = settings
        saveLocal()
        
        // 서버 동기화
        if let recipient = recipients.first(where: { $0.id == recipientId }),
           let serverId = recipient.serverId {
            APIService.shared.updateBridgeDepth(serverId: serverId, settings: settings.toServerDict) { _ in }
        }
    }
    
    // ═══════════════════════════════════════════
    // Phase 5: 공유 이력
    // ═══════════════════════════════════════════
    
    func addShareHistoryEntry(recipientName: String, sharedItems: String) {
        let entry = ShareHistoryEntry(recipientName: recipientName, sharedItems: sharedItems)
        shareHistory.insert(entry, at: 0)
        
        if shareHistory.count > 100 {
            shareHistory = Array(shareHistory.prefix(100))
        }
        saveLocal()
    }
    
    func markAsViewed(entryId: String) {
        if let index = shareHistory.firstIndex(where: { $0.id == entryId }) {
            shareHistory[index].wasViewed = true
            saveLocal()
        }
    }
    
    // ═══════════════════════════════════════════
    // Phase 5: 회원 탈퇴 데이터 삭제
    // ═══════════════════════════════════════════
    
    func deleteAllData() {
        recipients.removeAll()
        depthSettingsMap.removeAll()
        shareHistory.removeAll()
        
        UserDefaults.standard.removeObject(forKey: recipientsKey)
        UserDefaults.standard.removeObject(forKey: depthSettingsKey)
        UserDefaults.standard.removeObject(forKey: shareHistoryKey)
        
        // 서버 데이터도 삭제
        APIService.shared.deleteAllBridgeData { success in
            if success {
                print("🌉 [MindBridge] 서버 데이터 전체 삭제 완료")
            }
        }
    }
    
    // ═══════════════════════════════════════════
    // 서버 동기화 (앱 시작 시 호출)
    // ═══════════════════════════════════════════
    
    func syncFromServer() {
        // 수신자 목록 동기화
        APIService.shared.fetchBridgeRecipients { [weak self] data in
            guard let self = self, let data = data else { return }
            guard let recipientsList = data["recipients"] as? [[String: Any]] else { return }
            
            let serverRecipients: [BridgeRecipient] = recipientsList.compactMap { map in
                guard let serverId = map["id"] as? Int,
                      let name = map["name"] as? String else { return nil }
                
                let typeStr = map["type"] as? String ?? "family"
                let type: RecipientType = typeStr == "counselor" ? .counselor : .family
                let active = map["is_active"] as? Bool ?? true
                let schedStr = map["share_schedule"] as? String ?? "weekly"
                let schedule = ShareSchedule(rawValue: schedStr)
                
                // 기존 로컬 ID 매칭
                let localId = self.recipients.first(where: { $0.serverId == serverId })?.id ?? UUID().uuidString
                
                // depth 설정 복원
                if let depthMap = map["depth_settings"] as? [String: Any] {
                    let settings = DepthSettings(
                        moodStatus: depthMap["mood_status"] as? Bool ?? false,
                        moodGraph: depthMap["mood_graph"] as? Bool ?? false,
                        aiSummary: depthMap["ai_summary"] as? Bool ?? false,
                        detailedAnalysis: depthMap["detailed_analysis"] as? Bool ?? false,
                        triggerKeywords: depthMap["trigger_keywords"] as? Bool ?? false
                    )
                    DispatchQueue.main.async {
                        self.depthSettingsMap[localId] = settings
                    }
                }
                
                
                return BridgeRecipient(
                    id: localId, serverId: serverId, name: name, type: type,
                    isActive: active, shareSchedule: schedule, createdAt: Date()
                )
            }
            
            if !serverRecipients.isEmpty {
                DispatchQueue.main.async {
                    self.recipients = serverRecipients
                    self.saveLocal()
                    print("🌉 [MindBridge] 서버 수신자 동기화 완료: \(serverRecipients.count)명")
                }
            }
        }
        
        // 공유 이력 동기화
        APIService.shared.fetchBridgeShares { [weak self] shares in
            guard let self = self, let shares = shares else { return }
            
            let serverHistory: [ShareHistoryEntry] = shares.compactMap { map in
                let name = map["recipient_name"] as? String ?? "알 수 없음"
                let items = map["shared_items"] as? String ?? ""
                let viewed = map["is_viewed"] as? Bool ?? false
                var entry = ShareHistoryEntry(recipientName: name, sharedItems: items)
                entry.wasViewed = viewed
                return entry
            }
            
            if !serverHistory.isEmpty {
                DispatchQueue.main.async {
                    self.shareHistory = serverHistory
                    self.saveLocal()
                }
            }
        }
    }
    
    // ═══════════════════════════════════════════
    // 로컬 Persistence
    // ═══════════════════════════════════════════
    
    private func saveLocal() {
        let encoder = JSONEncoder()
        
        if let data = try? encoder.encode(recipients) {
            UserDefaults.standard.set(data, forKey: recipientsKey)
        }
        
        if let data = try? encoder.encode(depthSettingsMap) {
            UserDefaults.standard.set(data, forKey: depthSettingsKey)
        }
        
        if let data = try? encoder.encode(shareHistory) {
            UserDefaults.standard.set(data, forKey: shareHistoryKey)
        }
    }
    
    private func loadAll() {
        let decoder = JSONDecoder()
        
        if let data = UserDefaults.standard.data(forKey: recipientsKey),
           let decoded = try? decoder.decode([BridgeRecipient].self, from: data) {
            recipients = decoded
        }
        
        if let data = UserDefaults.standard.data(forKey: depthSettingsKey),
           let decoded = try? decoder.decode([String: DepthSettings].self, from: data) {
            depthSettingsMap = decoded
        }
        
        if let data = UserDefaults.standard.data(forKey: shareHistoryKey),
           let decoded = try? decoder.decode([ShareHistoryEntry].self, from: data) {
            shareHistory = decoded
        }
    }
}
