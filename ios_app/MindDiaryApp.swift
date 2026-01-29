
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
            .preferredColorScheme(.light) // Force Light Mode
            .onAppear {
                // 1. 모델 로딩 시작 (Background)
                Task(priority: .userInitiated) {
                    print("🚀 [App Start] Loading AI Model...")
                    await LLMService.shared.loadModel()
                }
                
                // 2. 스플래시 화면 제어 (최소 2초 + 로딩 완료 대기)
                Task {
                    // (A) 로고 감상을 위한 최소 대기 시간 (2초)
                    try? await Task.sleep(nanoseconds: 2 * 1_000_000_000)
                    
                    // (B) 모델이 로드될 때까지 대기 (0.5초 간격 폴링)
                    // LLMService의 isModelLoaded가 true가 될 때까지 기다림
                    while !LLMService.shared.isModelLoaded {
                        print("⏳ Waiting for AI Model to load...")
                        try? await Task.sleep(nanoseconds: 500_000_000) // 0.5s check
                    }
                    
                    print("✅ AI Model Loaded! Dismissing Splash.")
                    
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
struct AppSplashView: View {
    var body: some View {
        ZStack {
            Color.white.ignoresSafeArea()
            
            VStack(spacing: 24) {
                Spacer()
                
                // Logo Area
                VStack(spacing: 16) {
                    Text("🌙")
                        .font(.system(size: 100))
                        .shadow(color: Color.purple.opacity(0.3), radius: 10, x: 0, y: 10)
                    
                    VStack(spacing: 8) {
                        Text("마음 온")
                            .font(.system(size: 40, weight: .bold)) // Korean Title
                            .foregroundColor(.primary)
                        
                        Text("Maum-On")
                            .font(.title3)
                            .fontWeight(.semibold)
                            .foregroundColor(.purple)
                            
                        Text("당신의 마음을 잇다")
                            .font(.subheadline)
                            .foregroundColor(.gray)
                            .padding(.top, 4)
                    }
                }
                .scaleEffect(1.1) // Slight scale up for impact
                
                Spacer()
                
                // Loading Indicator
                VStack(spacing: 12) {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .purple))
                        .scaleEffect(1.2)
                    
                    Text("마음 준비 중...")
                        .font(.caption)
                        .foregroundColor(.gray.opacity(0.8))
                }
                .padding(.bottom, 60)
            }
        }
    }
}
