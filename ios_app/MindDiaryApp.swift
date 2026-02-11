
import SwiftUI

@main
struct MindDiaryApp: App {
    @StateObject private var authManager = AuthManager()
    @State private var showSplash = true
    
    var body: some Scene {
        WindowGroup {
            ZStack {
                if showSplash {
                    AppSplashView()
                        .transition(AnyTransition.opacity)
                        .zIndex(1)
                } else {
                    AppMainTabView()
                        .environmentObject(authManager)
                        .transition(AnyTransition.opacity)
                        .zIndex(0)
                }
            }
            .screenshotProtected(isProtected: true) // 스크린샷 방지 적용 (검은 화면 처리)
            .ignoresSafeArea() // [Fix] 전체 화면 꽉 차게 (스플래시 상하 여백 제거)
            .preferredColorScheme(.light) // Force Light Mode
            .onAppear {
                // 2. 스플래시 화면 제어 (최소 2초)
                Task {
                    // (A) 로고 감상을 위한 최소 대기 시간 (2초)
                    try? await Task.sleep(nanoseconds: 2 * 1_000_000_000)
                    
                    print("✅ Splash Time Completed. Dismising Splash.")
                    
                    // (C) 메인 화면 전환
                    await MainActor.run {
                        withAnimation(.easeOut(duration: 0.5)) {
                            self.showSplash = false
                        }
                    }
                }
            }
        }
    }
}

// MARK: - Splash View

