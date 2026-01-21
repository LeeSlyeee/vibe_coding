
import SwiftUI

struct MainTabView: View {
    @EnvironmentObject var authManager: AuthManager
    
    var body: some View {
        TabView {
            Text("캘린더 (구현 예정)")
                .tabItem {
                    Label("캘린더", systemImage: "calendar")
                }
            
            Text("통계 (구현 예정)")
                .tabItem {
                    Label("통계", systemImage: "chart.bar.fill")
                }
            
            Button("로그아웃") {
                authManager.logout()
            }
            .tabItem {
                Label("설정", systemImage: "gearshape.fill")
            }
        }
        .accentColor(.black)
    }
}
