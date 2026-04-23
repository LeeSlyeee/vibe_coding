
import SwiftUI

struct AppSplashView: View {
    @State private var logoOpacity: Double = 0
    @State private var logoScale: CGFloat = 0.8
    
    var body: some View {
        ZStack {
            // Geist: Pure White background
            Color.white.ignoresSafeArea()
            
            VStack(spacing: 24) {
                Spacer()
                
                // Logo Area — Geist minimal style
                VStack(spacing: 20) {
                    // Monochrome icon with subtle shadow
                    Image(systemName: "heart.text.clipboard")
                        .font(.system(size: 72, weight: .thin))
                        .foregroundColor(Color.gray900)
                    
                    VStack(spacing: 8) {
                        Text("maumON")
                            .font(.system(size: 28, weight: .semibold, design: .default))
                            .tracking(-1.12) // Geist negative letter-spacing
                            .foregroundColor(Color.gray900)
                            
                        Text("당신의 마음을, 온전히")
                            .font(.system(size: 15, weight: .regular))
                            .foregroundColor(Color.gray500)
                            .padding(.top, 2)
                    }
                }
                .opacity(logoOpacity)
                .scaleEffect(logoScale)
                
                Spacer()
                
                // Loading Indicator — Geist minimal
                VStack(spacing: 12) {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: Color.gray400))
                        .scaleEffect(1.0)
                    
                    Text("마음을 여는 중...")
                        .font(.geistCaption)
                        .foregroundColor(Color.gray400)
                }
                .padding(.bottom, 60)
            }
        }
        .onAppear {
            withAnimation(.easeOut(duration: 0.6)) {
                logoOpacity = 1.0
                logoScale = 1.0
            }
        }
    }
}

// Preview
struct AppSplashView_Previews: PreviewProvider {
    static var previews: some View {
        AppSplashView()
    }
}
