
import SwiftUI

@main
struct MindDiaryApp: App {
    @StateObject private var authManager = AuthManager()
    
    var body: some Scene {
        WindowGroup {
            AppMainTabView()
                .environmentObject(authManager)
                .preferredColorScheme(.light) // Force Light Mode
        }
    }
}
