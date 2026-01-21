
import SwiftUI

struct MainTabView: View {
    @EnvironmentObject var authManager: AuthManager
    
    var body: some View {
        TabView {
            CalendarView()
                .tabItem {
                    Label("캘린더", systemImage: "calendar")
                }
            
            StatsView()
                .tabItem {
                    Label("통계", systemImage: "chart.bar.fill")
                }
            
            GuideView()
                .tabItem {
                    Label("가이드", systemImage: "book.fill")
                }
            
            VStack {
                Spacer()
                Button(action: {
                    authManager.logout()
                }) {
                    HStack {
                        Text("로그아웃")
                            .fontWeight(.bold)
                        Image(systemName: "arrow.right.circle.fill")
                    }
                    .foregroundColor(.white)
                    .padding()
                    .frame(width: 200)
                    .background(Color.red)
                    .cornerRadius(10)
                    .shadow(radius: 5)
                }
                Spacer()
            }
            .tabItem {
                Label("설정", systemImage: "gearshape.fill")
            }
        }
        .accentColor(.black)
    }
}
