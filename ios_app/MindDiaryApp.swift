
import SwiftUI

@main
struct MindDiaryApp: App {
    @StateObject private var authManager = AuthManager()
    
    var body: some Scene {
        WindowGroup {
            if authManager.isAuthenticated {
                AppMainTabView()
                    .environmentObject(authManager)
                    .preferredColorScheme(.light) // Force Light Mode
            } else {
                AppLoginView()
                    .environmentObject(authManager)
                    .preferredColorScheme(.light) // Force Light Mode
            }
        }
    }
}
