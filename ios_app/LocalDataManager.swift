
import Foundation
import Combine

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
        if let idx = diaries.firstIndex(where: { $0.realId == newDiary.realId }) {
            diaries[idx] = newDiary
        } else {
            diaries.append(newDiary)
        }
        
        // Sort by Date Descending
        diaries.sort { ($0.created_at ?? "") > ($1.created_at ?? "") }
        
        saveToDisk()
        completion(true)
    }
    
    func deleteDiary(id: String, completion: @escaping (Bool) -> Void) {
        if let idx = diaries.firstIndex(where: { $0.realId == id }) {
            diaries.remove(at: idx)
            saveToDisk()
            completion(true)
        } else {
            completion(false)
        }
    }
    
    // Helper: Chat History Storage (Simple JSON for now)
    // chat_history.json
}
