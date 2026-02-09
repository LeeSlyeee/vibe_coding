
import Foundation
import Combine
import SwiftUI

class LocalDataManager: ObservableObject {
    static let shared = LocalDataManager()
    
    @Published var diaries: [Diary] = []
    private let fileName = "local_diaries.json"
    
    private var fileURL: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0].appendingPathComponent(fileName)
    }
    
    init() {
        loadDiaries()
    }
    
    // MARK: - Save & Load
    
    // [Tombstone] 삭제된 일기가 부활하지 않도록 관리
    private var deletedDiaryIds: [String] {
        get { UserDefaults.standard.stringArray(forKey: "deleted_diary_ids") ?? [] }
        set { UserDefaults.standard.set(newValue, forKey: "deleted_diary_ids") }
    }
    
    // [Tombstone] 날짜 기준 삭제 기록 (1일 1일기 규칙 가정)
    private var deletedDiaryDates: [String] {
        get { UserDefaults.standard.stringArray(forKey: "deleted_diary_dates") ?? [] }
        set { UserDefaults.standard.set(newValue, forKey: "deleted_diary_dates") }
    }
    
    func loadDiaries() {
        guard FileManager.default.fileExists(atPath: fileURL.path) else { return }
        
        do {
            let data = try Data(contentsOf: fileURL)
            let loaded = try JSONDecoder().decode([Diary].self, from: data)
            DispatchQueue.main.async { 
                self.diaries = loaded 
                self.syncWithServer()
                self.recoverStuckAnalysis() // [Auto-Recovery]
            }
            print("📁 [Local] Loaded \(loaded.count) diaries from \(fileURL.lastPathComponent)")
        } catch {
            print("❌ [Local] Load Error: \(error)")
            
            // [Safety] Load 실패 시 원본 파일 백업 (덮어쓰기 방지)
            let backupURL = fileURL.deletingPathExtension().appendingPathExtension("bak_\(Int(Date().timeIntervalSince1970)).json")
            try? FileManager.default.copyItem(at: fileURL, to: backupURL)
            print("🛡 [Local] Emergency backup created at: \(backupURL.lastPathComponent)")
        }
    }
    
    private func saveToDisk() {
        do {
            let data = try JSONEncoder().encode(diaries)
            try data.write(to: fileURL, options: .atomic)
            print("💾 [Local] Saved \(diaries.count) diaries.")
        } catch {
            print("❌ [Local] Save Error: \(error)")
        }
    }
    
    // [New] Auto-Recovery for Diaries stuck in "Re-analyzing..." state (Crash Recovery)
    private func recoverStuckAnalysis() {
        let stuckDiaries = self.diaries.filter { $0.ai_prediction == "재분석 중..." }
        
        if !stuckDiaries.isEmpty {
            print("🚑 [Recovery] Found \(stuckDiaries.count) diaries stuck in analysis. Restarting queue slowly...")
            
            // [Throttle] Enqueue one by one with 10s delay to prevent OOM loop
            for (index, diary) in stuckDiaries.enumerated() {
                let delay = Double(index) * 10.0 + 3.0 // Start after 3s, then every 10s
                DispatchQueue.main.asyncAfter(deadline: .now() + delay) {
                    print("🚑 [Recovery] Re-queueing stuck diary: \(diary.date ?? "")")
                    _ = LLMService.shared.tryEnqueueDiaryAnalysis(diary)
                }
            }
        }
    }
    
    // MARK: - CRUD
    
    func fetchDiaries(completion: @escaping ([Diary]) -> Void) {
        // Return immediately as we have in-memory cache
        completion(self.diaries)
    }
    
    func saveDiary(_ diary: Diary, completion: @escaping (Bool) -> Void) {
        var newDiary = diary
        
        // Ensure Created At (ISO8601)
        if newDiary.created_at == nil {
            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            newDiary.created_at = formatter.string(from: Date())
        }
        
        DispatchQueue.main.async {
            // [Tombstone] 사용자가 '작성' 했으므로, 해당 날짜의 차단 해제 (새로 쓰기 허용)
            if let date = newDiary.date {
                let dateKey = String(date.prefix(10))
                var blockedDates = self.deletedDiaryDates
                if let idx = blockedDates.firstIndex(of: dateKey) {
                    blockedDates.remove(at: idx)
                    self.deletedDiaryDates = blockedDates
                    print("🔓 [Tombstone] Unblocked date: \(dateKey) (User wrote new diary)")
                }
            }
            
            // [Sync] Mark as Dirty (Needs Sync)
            newDiary.isSynced = false
            
            // Generate UUID if missing
            if newDiary.id == nil { newDiary.id = UUID().uuidString }
            
            // Insert or Update
            if let index = self.diaries.firstIndex(where: { 
                if let sid = $0._id, let nid = newDiary._id, sid == nid { return true }
                return $0.id == newDiary.id 
            }) {
                self.diaries[index] = newDiary
            } else {
                self.diaries.append(newDiary)
            }
            
            // Sort by Date Descending
            self.diaries.sort { ($0.created_at ?? "") > ($1.created_at ?? "") }
            
            self.saveToDisk()
            
            // [OCI Sync] Upload to Server
            print("📤 [Sync] Uploading Diary to Server...")
            APIService.shared.syncDiary(newDiary) { success in
                if success {
                    // Mark as Synced on Success
                    DispatchQueue.main.async {
                        if let index = self.diaries.firstIndex(where: { $0.id == newDiary.id }) {
                            self.diaries[index].isSynced = true
                            self.saveToDisk()
                        }
                    }
                }
            }
            
            completion(true)
        }
    }
    
    func deleteDiary(id: String, completion: @escaping (Bool) -> Void) {
        DispatchQueue.main.async {
            if let idx = self.diaries.firstIndex(where: { 
                if let sid = $0._id, sid == id { return true }
                if let lid = $0.id, lid == id { return true }
                return false
            }) {
                // [OCI Sync] Delete on Server if _id exists
                let diaryToDelete = self.diaries[idx]
                if let serverId = diaryToDelete._id {
                     // [Tombstone] 즉시 차단 목록에 추가
                     var deleted = self.deletedDiaryIds
                     if !deleted.contains(serverId) {
                         deleted.append(serverId)
                         self.deletedDiaryIds = deleted
                     }
                     
                     APIService.shared.deleteDiaryOnServer(diaryId: serverId)
                }
                
                // [Tombstone] 날짜도 차단 (ID가 없는 경우 대비)
                if let date = diaryToDelete.date {
                    var deletedDates = self.deletedDiaryDates
                    let dateKey = String(date.prefix(10))
                    if !deletedDates.contains(dateKey) {
                        deletedDates.append(dateKey)
                        self.deletedDiaryDates = deletedDates
                    }
                }
                
                self.diaries.remove(at: idx)
                self.saveToDisk()
                completion(true)
            } else {
                completion(false)
            }
        }
    }
    
    // [Optimization] Bulk update sync status after successful B2G upload
    func markAsSynced(ids: [String]) {
        DispatchQueue.main.async {
            var updated = false
            for id in ids {
                if let index = self.diaries.firstIndex(where: { $0.id == id }) {
                    if self.diaries[index].isSynced != true {
                        self.diaries[index].isSynced = true
                        updated = true
                    }
                }
            }
            if updated {
                self.saveToDisk()
                print("✅ [Local] Marked \(ids.count) diaries as synced.")
            }
        }
    }
    
    // MARK: - Server Sync
    
    // [Smart Sync] Pull First -> Diff -> Push Missing -> Merge
    // 효율적이고 정확한 동기화: 서버에 없는 데이터만 골라서 전송
    func syncWithServer() {
        print("🧠 [SmartSync] Starting Integrity Check...")
        
        // 1. Fetch Server State First
        APIService.shared.fetchDiaries { [weak self] serverData in
            guard let self = self, let serverItems = serverData else {
                print("⚠️ [SmartSync] Server unreachable. Fallback to offline mode.")
                return
            }
            
            // 2. Build Server Inventory (Dates & IDs)
            let serverDates = Set(serverItems.compactMap { ($0["created_at"] as? String)?.prefix(10).description })
            let serverIDs = Set(serverItems.compactMap { $0["id"] as? String })
            
            print("📋 [SmartSync] Server has \(serverItems.count) items.")
            
            let group = DispatchGroup()
            
            // 3. Identify Missing Items (Local has it, Server doesn't)
            // Condition: (isSynced == false) OR (Date missing on Server)
            let itemsToPush = self.diaries.filter { diary in
                // 1. Explicitly dirty (User just wrote it)
                if diary.isSynced == false { return true }
                
                // 2. Server missing check (Integrity Repair)
                if let date = diary.date {
                    let dateKey = String(date.prefix(10))
                    if !serverDates.contains(dateKey) {
                        print("🚑 [SmartSync] Found missing item on server: \(dateKey)")
                        return true
                    }
                }
                
                return false
            }
            
            if itemsToPush.isEmpty {
                print("✅ [SmartSync] Server and Local are in sync. No upload needed.")
            } else {
                print("📤 [SmartSync] Uploading \(itemsToPush.count) missing/dirty items...")
                for diary in itemsToPush {
                    group.enter()
                    APIService.shared.syncDiary(diary) { success in
                        if success {
                            DispatchQueue.main.async {
                                if let index = self.diaries.firstIndex(where: { $0.id == diary.id }) {
                                    self.diaries[index].isSynced = true
                                }
                            }
                        }
                        group.leave()
                    }
                }
            }
            
            // 4. After Push, Merge Server Updates (Two-way Sync)
            group.notify(queue: .main) {
                print("🔄 [SmartSync] Push done. Merging server updates...")
                self.saveToDisk() // Save 'isSynced' status
                self.mergeServerDiaries(serverItems) {
                    print("✅ [SmartSync] Synchronization Complete.")
                }
            }
        }
    }
    
    
    // 서버 데이터를 로컬에 병합 (서버 우선)
    func mergeServerDiaries(_ serverData: [[String: Any]], completion: @escaping () -> Void = {}) {
        DispatchQueue.main.async {
            var updatedCount = 0
            var newCount = 0
            
            for item in serverData {
                let id = "\(item["id"] ?? "")"
                
                // [Tombstone] 사용자가 삭제한 ID라면 병합 제외
                if self.deletedDiaryIds.contains(id) { continue }
                
                guard let createdAt = item["created_at"] as? String else { continue }
                
                // [Critical Fix] Prefer explicitly mapped 'date' field if available, else derive from created_at
                // 서버가 'date' 필드를 보내주지 않는 경우, created_at(UTC)이 한국 시간과 달라 날짜가 밀리는 현상 방지
                let serverDateRaw = (item["date"] as? String) ?? createdAt
                let dateStr = String(serverDateRaw.prefix(10))
                
                // [Tombstone] 날짜 차단 확인
                if self.deletedDiaryDates.contains(dateStr) { continue }
                
                // ... (Parsing logic omitted for brevity, stick to current impl) ...
                // [Robust Parsing] Field Name Fallbacks
                var moodScore = 3
                if let ms = item["mood_score"] as? Int { moodScore = ms }
                else if let ml = item["mood_level"] as? Int { moodScore = ml }
                
                var content = ""
                if let c = item["content"] as? String { content = c }
                else if let e = item["event"] as? String { content = e }
                
                // AI Fields Parsing
                let analysisMap = item["analysis_result"] as? [String: Any]
                let aiComment = (item["ai_comment"] as? String) ?? (analysisMap?["ai_comment"] as? String) ?? (analysisMap?["comment"] as? String)
                let aiAnalysis = (item["ai_analysis"] as? String) ?? (analysisMap?["ai_analysis"] as? String) ?? (analysisMap?["analysis"] as? String)
                let aiAdvice = (item["ai_advice"] as? String) ?? (analysisMap?["ai_advice"] as? String) ?? (analysisMap?["advice"] as? String)
                let aiPrediction = (item["ai_prediction"] as? String) ?? (analysisMap?["ai_prediction"] as? String) ?? (analysisMap?["prediction"] as? String)
                
                let sleepDesc = (item["sleep_condition"] as? String) ?? (item["sleep_desc"] as? String) ?? (analysisMap?["sleep_condition"] as? String) ?? (analysisMap?["sleep_desc"] as? String)
                let weather = (item["weather"] as? String) ?? (analysisMap?["weather"] as? String)
                let emotionDesc = (item["emotion_desc"] as? String) ?? (analysisMap?["emotion_desc"] as? String)
                let emotionMeaning = (item["emotion_meaning"] as? String) ?? (analysisMap?["emotion_meaning"] as? String)
                let selfTalk = (item["self_talk"] as? String) ?? (analysisMap?["self_talk"] as? String)
                
                var serverDiary = Diary(
                    id: UUID().uuidString,
                    _id: id,
                    date: dateStr,
                    mood_level: moodScore,
                    event: content,
                    emotion_desc: emotionDesc,
                    emotion_meaning: emotionMeaning,
                    self_talk: selfTalk,
                    sleep_desc: sleepDesc,
                    weather: weather,
                    temperature: nil,
                    sleep_condition: nil,
                    ai_prediction: aiPrediction,
                    ai_comment: aiComment,
                    ai_analysis: aiAnalysis,
                    ai_advice: aiAdvice,
                    created_at: createdAt,
                    medication: nil,
                    medication_desc: nil
                )
                serverDiary.isSynced = true
                
                // [Safety Merge] 날짜 매칭 시 ID 충돌 검사
                if let index = self.diaries.firstIndex(where: { 
                    // 1. ID가 일치하면 무조건 업데이트 (가장 안전)
                    if let existingId = $0._id, existingId == id { return true }
                    
                    // 2. 날짜가 일치하는 경우
                    if ($0.date ?? "").prefix(10) == dateStr.prefix(10) {
                        // [Critical Guard]
                        // 로컬 일기가 이미 "다른 Server ID"를 가지고 있다면? -> 충돌! 덮어쓰지 않음.
                        if let existingId = $0._id, !existingId.isEmpty, existingId != id {
                            print("🛡️ [Sync] Conflict Detected! Date matches (\(dateStr)) but IDs differ (Local: \(existingId) vs Server: \(id)). Keeping Local.")
                            return false
                        }
                        return true
                    }
                    return false
                }) {
                    // [Conflict Check] unsynced local data preservation
                    if self.diaries[index].isSynced == false {
                        print("🛡️ [Sync] Preserving Unsynced Local Data (Date: \(dateStr))")
                        continue
                    }
                    
                    serverDiary.id = self.diaries[index].id
                    self.diaries[index] = serverDiary
                    updatedCount += 1
                } else {
                    self.diaries.append(serverDiary)
                    newCount += 1
                }
            } // End Loop
            
            self.diaries.sort { ($0.created_at ?? "") > ($1.created_at ?? "") }
            self.saveToDisk()
            
            print("📥 [Sync] Merge Complete. New: \(newCount), Updated: \(updatedCount)")
            
            // [Fix] Broadcast Update explicitly to force UI Refresh
            NotificationCenter.default.post(name: NSNotification.Name("RefreshDiaries"), object: nil)
            
            completion()
        } // End Dispatch
    }
} // End Class
