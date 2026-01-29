
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
    
    func loadDiaries() {
        guard FileManager.default.fileExists(atPath: fileURL.path) else { return }
        
        do {
            let data = try Data(contentsOf: fileURL)
            let loaded = try JSONDecoder().decode([Diary].self, from: data)
            DispatchQueue.main.async { self.diaries = loaded }
            print("📁 [Local] Loaded \(loaded.count) diaries from \(fileURL.lastPathComponent)")
        } catch {
            print("❌ [Local] Load Error: \(error)")
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
    
    // MARK: - CRUD
    
    func fetchDiaries(completion: @escaping ([Diary]) -> Void) {
        // Return immediately as we have in-memory cache
        completion(self.diaries)
    }
    
    func saveDiary(_ diary: Diary, completion: @escaping (Bool) -> Void) {
        DispatchQueue.main.async {
            var newDiary = diary
            
            // Ensure ID
            if newDiary.id == nil && newDiary._id == nil {
                newDiary.id = UUID().uuidString
            }
            
            // Ensure Created At (ISO8601)
            if newDiary.created_at == nil {
                let formatter = ISO8601DateFormatter()
                formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
                newDiary.created_at = formatter.string(from: Date())
            }
            
            // Update or Add
            // realId 사용 대신 명시적 ID 비교로 안전성 확보
            if let idx = self.diaries.firstIndex(where: { 
                if let sid = $0._id, let nid = newDiary._id, sid == nid { return true }
                if let lid = $0.id, let nlid = newDiary.id, lid == nlid { return true }
                return false
            }) {
                self.diaries[idx] = newDiary
            } else {
                self.diaries.append(newDiary)
            }
            
            // Sort by Date Descending
            self.diaries.sort { ($0.created_at ?? "") > ($1.created_at ?? "") }
            
            self.saveToDisk()
            
            // [OCI Sync] 서버 동기화 로직
            if (newDiary.ai_comment?.isEmpty == false || newDiary.ai_analysis?.isEmpty == false) {
                print("📤 [Sync] Uploading Analysis Results...")
                APIService.shared.updateDiaryAnalysis(newDiary)
            } else {
                print("📤 [Sync] Uploading Initial Diary Content...")
                APIService.shared.saveDiaryInitial(newDiary)
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
                self.diaries.remove(at: idx)
                self.saveToDisk()
                completion(true)
            } else {
                completion(false)
            }
        }
    }
    
    // MARK: - Server Sync
    
    // [New] Pull from Server & Merge
    func syncWithServer() {
        print("🔄 [LocalDataManager] Syncing with server...")
        APIService.shared.fetchDiaries { [weak self] serverData in
            guard let self = self, let data = serverData else {
                print("⚠️ [LocalDataManager] Sync Failed or No Data")
                return
            }
            
            self.mergeServerDiaries(data) {
                print("✅ [LocalDataManager] Sync Complete.")
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
                guard let createdAt = item["created_at"] as? String else { continue }
                
                let dateStr = String(createdAt.prefix(10))
                
                // [Robust Parsing] Field Name Fallbacks
                var moodScore = 3
                if let ms = item["mood_score"] as? Int { moodScore = ms }
                else if let ml = item["mood_level"] as? Int { moodScore = ml }
                
                var content = ""
                if let c = item["content"] as? String { content = c }
                else if let e = item["event"] as? String { content = e }
                
                // AI Fields: Check nested 'analysis_result' OR top-level fields
                let analysisMap = item["analysis_result"] as? [String: Any]
                
                let aiComment = (item["ai_comment"] as? String) 
                    ?? (analysisMap?["comment"] as? String)
                
                let aiAnalysis = (item["ai_analysis"] as? String) 
                    ?? (analysisMap?["analysis"] as? String)
                    ?? (analysisMap?["advice"] as? String)
                
                let aiAdvice = (item["ai_advice"] as? String) // Top-level only usually
                let aiPrediction = (item["ai_prediction"] as? String) // Top-level only
                let sleepDesc = (item["sleep_condition"] as? String) ?? (item["sleep_desc"] as? String)
                let weather = (item["weather"] as? String)
                let emotionDesc = (item["emotion_desc"] as? String)
                let emotionMeaning = (item["emotion_meaning"] as? String)
                let selfTalk = (item["self_talk"] as? String)
                
                // 기존 로컬 데이터 확인 (날짜 기준)
                if let idx = self.diaries.firstIndex(where: { ($0.date ?? "").prefix(10) == dateStr }) {
                    // Update
                    var existing = self.diaries[idx]
                    existing.mood_level = moodScore
                    existing._id = id // Server ID binding
                    
                    // Fields Update
                    if (existing.event == nil || existing.event?.isEmpty == true) { existing.event = content }
                    if (existing.emotion_desc?.isEmpty ?? true) { existing.emotion_desc = emotionDesc }
                    if (existing.emotion_meaning?.isEmpty ?? true) { existing.emotion_meaning = emotionMeaning }
                    if (existing.self_talk?.isEmpty ?? true) { existing.self_talk = selfTalk }
                    if (existing.sleep_desc?.isEmpty ?? true) { existing.sleep_desc = sleepDesc }
                    if (existing.weather?.isEmpty ?? true) { existing.weather = weather }
                    
                    // AI Result Sync (Overwrite if server has data)
                    if let c = aiComment { existing.ai_comment = c }
                    if let a = aiAnalysis { existing.ai_analysis = a }
                    if let d = aiAdvice { existing.ai_advice = d }
                    if let p = aiPrediction { existing.ai_prediction = p }
                    
                    self.diaries[idx] = existing
                    updatedCount += 1
                } else {
                    // Insert New (구조체 초기화 순서 엄수)
                    let newDiary = Diary(
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
                        sleep_condition: nil, // Legacy Field explicit nil
                        ai_prediction: aiPrediction,
                        ai_comment: aiComment,
                        ai_analysis: aiAnalysis, // Advice or Analysis
                        ai_advice: aiAdvice,
                        created_at: createdAt
                    )
                    self.diaries.append(newDiary)
                    newCount += 1
                }
            }
            
            self.diaries.sort { ($0.created_at ?? "") > ($1.created_at ?? "") }
            self.saveToDisk()
            
            print("📥 [Sync] Merge Complete. New: \(newCount), Updated: \(updatedCount)")
            completion()
        }
    }
}
