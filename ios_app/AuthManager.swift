
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

    @Published var isPremium: Bool = false {
        didSet {
            UserDefaults.standard.set(isPremium, forKey: "userIsPremium")
        }
    }
    
    init() {
        self.token = UserDefaults.standard.string(forKey: "authToken")
        self.isAuthenticated = self.token != nil
        self.riskLevel = UserDefaults.standard.integer(forKey: "userRiskLevel")
        self.isPremium = UserDefaults.standard.bool(forKey: "userIsPremium")
        if self.riskLevel == 0 { self.riskLevel = 1 } // Default to 1
    }
    
    func login(token: String) {
        self.token = token
    }
    
    func setRiskLevel(_ level: Int) {
        self.riskLevel = level
    }
    
    func setPremium(_ status: Bool) {
        self.isPremium = status
    }
    
    func logout() {
        self.token = nil
        self.riskLevel = 1
        self.isPremium = false
        UserDefaults.standard.removeObject(forKey: "authToken")
        UserDefaults.standard.removeObject(forKey: "userRiskLevel")
        UserDefaults.standard.removeObject(forKey: "userIsPremium")
    }
}
