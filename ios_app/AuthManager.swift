
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
    
    init() {
        self.token = UserDefaults.standard.string(forKey: "authToken")
        self.isAuthenticated = self.token != nil
    }
    
    func login(token: String) {
        self.token = token
    }
    
    func logout() {
        self.token = nil
        UserDefaults.standard.removeObject(forKey: "authToken")
    }
}
