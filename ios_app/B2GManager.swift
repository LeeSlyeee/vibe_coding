import SwiftUI
import Combine

// B2G(Business to Government) 연동 매니저
class B2GManager: ObservableObject {
    static let shared = B2GManager()
    
    // 연동 상태 영구 저장
    @AppStorage("healthCenterCode") var centerCode: String = ""
    @AppStorage("isB2GLinked") var isLinked: Bool = false
    @AppStorage("lastSyncDate") var lastSyncDate: Double = 0
    
    @Published var isSyncing = false
    
    private init() {}
    
    // 보건소 코드 연결 시도
    func connect(code: String, completion: @escaping (Bool, String) -> Void) {
        guard !code.isEmpty else {
            completion(false, "코드를 입력해주세요.")
            return
        }
        
        // 시뮬레이션: 서버와 핸드셰이크 과정
        isSyncing = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
            self.isSyncing = false
            
            // 예: 코드가 'SEOUL'로 시작하면 유효하다고 가정
            if code.uppercased().hasPrefix("SEOUL") || code.uppercased().hasPrefix("TEST") {
                self.centerCode = code.uppercased()
                self.isLinked = true
                self.syncData() // 연결 즉시 데이터 전송
                completion(true, "연동에 성공했습니다!\n이제 담당 선생님이 상태를 확인할 수 있습니다.")
            } else {
                completion(false, "유효하지 않은 기관 코드입니다.")
            }
        }
    }
    
    // 연동 해제
    func disconnect() {
        self.centerCode = ""
        self.isLinked = false
        self.lastSyncDate = 0
    }
    
    // 백그라운드 데이터 동기화 (감정 그래프 & 리스크 레벨)
    func syncData() {
        guard isLinked else { return }
        
        print("🔄 [B2G] 보건소 서버로 데이터 전송 시작...")
        
        // 1. 로컬 데이터 수집
        let riskLevel = UserDefaults.standard.integer(forKey: "userRiskLevel")
        let diaries = LocalDataManager.shared.diaries
        
        // 2. JSON 데이터 생성 (서버 전송용)
        let payload: [String: Any] = [
            "center_code": centerCode,
            "user_nickname": UserDefaults.standard.string(forKey: "userNickname") ?? "Unknown",
            "risk_level": riskLevel,
            "mood_metrics": diaries.map { ["date": $0.date ?? "", "score": $0.mood_level] },
            "timestamp": Date().timeIntervalSince1970
        ]
        
        // 3. 암호화 및 전송 (시뮬레이션)
        // 실제로는 여기서 HTTPS POST 요청을 보냄
        DispatchQueue.global().async {
            // Encode to JSON
            if let jsonData = try? JSONSerialization.data(withJSONObject: payload, options: .prettyPrinted),
               let jsonString = String(data: jsonData, encoding: .utf8) {
                
                // 암호화된 척 출력
                print("📤 [Encrypted Payload Sent]: \(jsonString.prefix(100))...")
                
                DispatchQueue.main.async {
                    self.lastSyncDate = Date().timeIntervalSince1970
                    print("✅ [B2G] 데이터 전송 완료")
                }
            }
        }
    }
}
