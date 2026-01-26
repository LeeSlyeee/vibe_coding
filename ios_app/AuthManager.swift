
import Foundation
import Combine

class AuthManager: ObservableObject {
    @Published var isAuthenticated: Bool = false
    @Published var token: String? {
        didSet {
            UserDefaults.standard.set(token, forKey: "authToken")
            isAuthenticated = token != nil
        }
    }
    
    @Published var riskLevel: Int = 1 {
        didSet {
            UserDefaults.standard.set(riskLevel, forKey: "userRiskLevel")
        }
    }
    
    init() {
        self.token = UserDefaults.standard.string(forKey: "authToken")
        self.isAuthenticated = self.token != nil
        self.riskLevel = UserDefaults.standard.integer(forKey: "userRiskLevel")
        if self.riskLevel == 0 { self.riskLevel = 1 } // Default to 1
    }
    
    func login(token: String) {
        self.token = token
    }
    
    func setRiskLevel(_ level: Int) {
        self.riskLevel = level
    }
    
    func logout() {
        self.token = nil
        self.riskLevel = 1
        UserDefaults.standard.removeObject(forKey: "authToken")
        UserDefaults.standard.removeObject(forKey: "userRiskLevel")
    }
}
