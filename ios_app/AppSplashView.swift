
import SwiftUI

struct AppSplashView: View {
    var body: some View {
        ZStack {
            Color(hexString: "6e4cdf").ignoresSafeArea() // Custom Purple Background
            
            VStack(spacing: 24) {
                Spacer()
                
                // Logo Area
                VStack(spacing: 16) {
                    Text("🌙")
                        .font(.system(size: 100))
                        .shadow(color: Color.black.opacity(0.2), radius: 10, x: 0, y: 10)
                    
                    VStack(spacing: 8) {
                        Text("마음 온")
                            .font(.system(size: 40, weight: .bold)) // Korean Title
                            .foregroundColor(.white)
                        
                        Text("maumON")
                            .font(.title3)
                            .fontWeight(.semibold)
                            .foregroundColor(.white.opacity(0.9))
                            
                        Text("당신의 마음을 잇다")
                            .font(.subheadline)
                            .foregroundColor(.white.opacity(0.7))
                            .padding(.top, 4)
                    }
                }
                .scaleEffect(1.1) // Slight scale up for impact
                
                Spacer()
                
                // Loading Indicator
                VStack(spacing: 12) {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .scaleEffect(1.2)
                    
                    Text("마음 준비 중...")
                        .font(.caption)
                        .foregroundColor(.white.opacity(0.8))
                }
                .padding(.bottom, 60)
            }
        }
    }
}

// Preview to check the layout
struct AppSplashView_Previews: PreviewProvider {
    static var previews: some View {
        AppSplashView()
    }
}
