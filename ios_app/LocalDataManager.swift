
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
        } catch {
            
            // [Safety] Load 실패 시 원본 파일 백업 (덮어쓰기 방지)
            let backupURL = fileURL.deletingPathExtension().appendingPathExtension("bak_\(Int(Date().timeIntervalSince1970)).json")
            try? FileManager.default.copyItem(at: fileURL, to: backupURL)
        }
    }
    
    private func saveToDisk() {
        do {
            let data = try JSONEncoder().encode(diaries)
            try data.write(to: fileURL, options: .atomic)
        } catch {
        }
    }
    
    // [Public] 서버에서 삭제된 일기를 로컬에서도 제거
    func removeServerDeletedDiary(serverId: String?, dateStr: String?) {
        self.diaries.removeAll { $0._id == serverId || $0.date == dateStr }
        self.saveToDisk()
        NotificationCenter.default.post(name: NSNotification.Name("RefreshDiaries"), object: nil)
    }
    
    // [New] Auto-Recovery for Diaries stuck in "Re-analyzing..." state (Crash Recovery)
    // [Auto-Recovery]
    // [Fix] Smart Recovery: Reset status first to unblock UI, then Lazy Load Model.
    private func recoverStuckAnalysis() {
        let stuckDiaries = self.diaries.filter { $0.ai_prediction == "재분석 중..." }
        
        if !stuckDiaries.isEmpty {
            
            // 1. UI Unblocking (Immediate)
            DispatchQueue.main.async {
                for (index, _) in self.diaries.enumerated() {
                    if self.diaries[index].ai_prediction == "재분석 중..." {
                        self.diaries[index].ai_prediction = nil 
                        self.diaries[index].ai_analysis = nil 
                    }
                }
                self.saveToDisk()
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
            }
        }
    }
    
    // MARK: - Server Sync
    
    // [Smart Sync] Push First -> Pull -> Merge
    // "Medical Staff Dashboard as Standard" Implementation
    func syncWithServer(force: Bool = false) {
        // [Standard Architecture] Strict Auth Check
        guard let username = UserDefaults.standard.string(forKey: "authUsername"), !username.isEmpty else {
            print("🔴 [SYNC] authUsername 없음 - Push/Pull 건너뜀")
            return
        }
        
        print("🟡 [SYNC] syncWithServer 시작 (force=\(force), diaries=\(diaries.count)개)")
        
        APIService.shared.ensureAuth { [weak self] authSuccess in
            guard let self = self else { print("🔴 [SYNC] self nil"); return }
            if !authSuccess { print("🔴 [SYNC] ensureAuth 실패"); return }
            
            // 1. Push Phase: Identify & Upload Dirty Items
            // We push BEFORE fetching to ensure we don't overwrite our own recent changes with stale server data.
            let outputGroup = DispatchGroup()
            let itemsToPush = self.diaries.filter { $0.isSynced == false || force }
            
            print("🟢 [SYNC] Push 대상: \(itemsToPush.count)개 (전체 \(self.diaries.count)개, force=\(force))")
            
            if !itemsToPush.isEmpty {
                outputGroup.enter()
                
                // [Fix] 순차 실행: 동시에 24개 요청 → 네트워크 병목 방지
                func pushNext(index: Int) {
                    guard index < itemsToPush.count else {
                        print("🟢 [SYNC] Push 완료: \(itemsToPush.count)개 전송 시도")
                        outputGroup.leave()
                        return
                    }
                    let diary = itemsToPush[index]
                    print("📤 [SYNC] Push \(index+1)/\(itemsToPush.count): date=\(diary.date ?? "nil"), med=\(diary.medication_taken)")
                    APIService.shared.syncDiary(diary) { success in
                        if success {
                            DispatchQueue.main.async {
                                if let idx = self.diaries.firstIndex(where: { $0.id == diary.id }) {
                                    self.diaries[idx].isSynced = true
                                }
                            }
                        }
                        // 다음 항목 처리
                        pushNext(index: index + 1)
                    }
                }
                pushNext(index: 0)
            } else {
            }
            
            // 2. Pull Phase: Fetch Latest Server State (After Push)
            outputGroup.notify(queue: .main) {
                APIService.shared.fetchDiaries { [weak self] serverData in
                    guard let self = self, let finalServerItems = serverData else {
                        return 
                    }
                    
                    // 3. Merge Phase: Apply Server Data to Local
                    self.mergeServerDiaries(finalServerItems, ignoreTombstones: force) {
                    }
                }
            }
        }
    }
    
    // 서버 데이터를 로컬에 병합 (서버 우선 / Server Authority)
    func mergeServerDiaries(_ serverData: [[String: Any]], ignoreTombstones: Bool = false, completion: @escaping () -> Void = {}) {
        DispatchQueue.main.async {
            var updatedCount = 0
            var newCount = 0
            
            for item in serverData {
                let id = "\(item["id"] ?? "")"
                let dateRaw = (item["date"] as? String) ?? (item["created_at"] as? String) ?? "Unknown"
                
                // [Tombstone] 사용자가 삭제한 ID라면 병합 제외 (단, 강제 동기화 시 복구 및 차단 해제)
                if self.deletedDiaryIds.contains(id) {
                    if ignoreTombstones {
                        // [Recovery] 사용자가 강제 복구를 요청했으므로, 차단 목록에서 영구 제거 (Standard: Restore)
                        self.deletedDiaryIds.removeAll { $0 == id }
                    } else {
                        continue
                    }
                }
                
                guard let createdAt = item["created_at"] as? String else { continue }
                
                // [Critical Fix] Prefer explicitly mapped 'date' field
                let serverDateRaw = (item["date"] as? String) ?? createdAt
                let dateStr = String(serverDateRaw.prefix(10))
                
                // [Tombstone] 날짜 차단 확인 (단, 강제 동기화 시 복구 및 차단 해제)
                if self.deletedDiaryDates.contains(dateStr) {
                    if ignoreTombstones {
                        // [Recovery] 강제 복구 시 날짜 차단도 해제
                        self.deletedDiaryDates.removeAll { $0 == dateStr }
                    } else {
                        continue
                    }
                }
                
                // [Fix] mood_level(1~5 원본)을 우선 사용, mood_score(10점 환산)는 fallback
                // 무한증식 방지: mood_score를 mood_level로 저장 → Push → 다시 ×2 = 무한 루프
                var moodScore = 3
                if let ml = item["mood_level"] as? Int {
                    moodScore = ml > 5 ? max(1, min(5, ml / 2)) : ml  // 비정상값 클램프
                } else if let ms = item["mood_score"] as? Int {
                    moodScore = ms > 5 ? max(1, min(5, ms / 2)) : ms  // 10점 → 5점 변환
                }
                
                var content = ""
                if let c = item["content"] as? String { content = c }
                else if let e = item["event"] as? String { content = e }
                
                // AI Fields Parsing
                let analysisMap = item["analysis_result"] as? [String: Any]
                let aiComment = (item["ai_comment"] as? String) ?? (analysisMap?["ai_comment"] as? String) ?? (analysisMap?["comment"] as? String)
                let aiAnalysis = (item["ai_analysis"] as? String) ?? (analysisMap?["ai_analysis"] as? String) ?? (analysisMap?["analysis"] as? String)
                let aiAdvice = (item["ai_advice"] as? String) ?? (analysisMap?["ai_advice"] as? String) ?? (analysisMap?["advice"] as? String)
                let aiPrediction = (item["ai_prediction"] as? String) ?? (item["ai_emotion"] as? String) ?? (analysisMap?["ai_prediction"] as? String) ?? (analysisMap?["prediction"] as? String) ?? (analysisMap?["emotion"] as? String)
                
                let sleepDesc = (item["sleep_condition"] as? String) ?? (item["sleep_desc"] as? String) ?? (analysisMap?["sleep_condition"] as? String) ?? (analysisMap?["sleep_desc"] as? String)
                let weather = (item["weather"] as? String) ?? (analysisMap?["weather"] as? String)
                let emotionDesc = (item["emotion_desc"] as? String) ?? (analysisMap?["emotion_desc"] as? String)
                let emotionMeaning = (item["emotion_meaning"] as? String) ?? (analysisMap?["emotion_meaning"] as? String)
                let selfTalk = (item["self_talk"] as? String) ?? (analysisMap?["self_talk"] as? String)
                
                // [New] Extended Fields Parsing
                let temperature = (item["temperature"] as? Double) ?? (analysisMap?["temperature"] as? Double)
                let gratitudeNote = (item["gratitude_note"] as? String) ?? (analysisMap?["gratitude_note"] as? String) ?? (analysisMap?["gratitude"] as? String)
                let medicationTaken = (item["medication_taken"] as? Bool) ?? (analysisMap?["medication_taken"] as? Bool) ?? (analysisMap?["medication"] as? Bool)
                let medicationDesc = (item["medication_desc"] as? String) ?? (analysisMap?["medication_desc"] as? String)
                let symptoms = (analysisMap?["symptoms"] as? [String]) ?? []

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
                    temperature: temperature,
                    sleep_condition: nil,
                    ai_prediction: aiPrediction,
                    ai_comment: aiComment,
                    ai_analysis: aiAnalysis,
                    ai_advice: aiAdvice,
                    created_at: createdAt,
                    medication: medicationTaken,
                    medication_desc: medicationDesc,
                    symptoms: symptoms,
                    gratitude_note: gratitudeNote
                )
                serverDiary.isSynced = true
                
                if let index = self.diaries.firstIndex(where: {
                    if let sid = $0._id, sid == id { return true }
                    if let date = $0.date, date == dateStr { return true }
                    return false
                }) {
                    // Update Existing
                    var existing = self.diaries[index]
                    
                    // [Server Authority]
                    // We REMOVED the "Dirty Check" here.
                    // If Server provides data, it overrides Local even if Local was unsynced.
                    // (But since we Pushed first, Local changes should already be on Server if valid)
                    
                    // Preserve Local UUID
                    let localUUID = existing.id
                    
                    // [Data Safety] Preserve AI Analysis if Server value is missing but Local has it
                    // This prevents overwriting valid AI data with empty/null from server (e.g. partial response)
                    if (serverDiary.ai_prediction == nil || serverDiary.ai_prediction?.isEmpty == true) {
                        if let existingPred = existing.ai_prediction, !existingPred.isEmpty {
                            serverDiary.ai_prediction = existingPred
                        }
                    }
                    if (serverDiary.ai_comment == nil || serverDiary.ai_comment?.isEmpty == true) {
                        if let existingCom = existing.ai_comment, !existingCom.isEmpty {
                             serverDiary.ai_comment = existingCom
                        }
                    }

                    self.diaries[index] = serverDiary
                    self.diaries[index].id = localUUID
                    self.diaries[index].isSynced = true
                    
                    updatedCount += 1
                } else {
                    // New Entry
                    self.diaries.append(serverDiary)
                    newCount += 1
                }
            } // End Loop
            
            // [Standard] 서버에 없는 로컬 항목 정리
            // 서버 ID 목록을 수집하여, 로컬에만 남아있는 "이미 동기화된" 항목을 제거
            // (isSynced=false인 항목은 아직 Push 전이므로 보존)
            let serverIds = Set(serverData.compactMap { "\($0["id"] ?? "")" })
            let beforeCount = self.diaries.count
            self.diaries.removeAll { diary in
                guard diary.isSynced == true,             // 이미 동기화된 항목만 대상
                      let sid = diary._id,               // 서버 ID가 있는 항목만
                      !sid.isEmpty,
                      !serverIds.contains(sid)           // 서버에 없으면 제거
                else { return false }
                return true
            }
            let removedCount = beforeCount - self.diaries.count
            
            self.diaries.sort { ($0.created_at ?? "") > ($1.created_at ?? "") }
            self.saveToDisk()
            
            
            // [Fix] Broadcast Update
            NotificationCenter.default.post(name: NSNotification.Name("RefreshDiaries"), object: nil)
            
            completion()
        } // End Dispatch
    }
} // End Class
