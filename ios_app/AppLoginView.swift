
import SwiftUI

struct AppLoginView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var username = ""
    @State private var password = ""
    @State private var errorMessage = ""
    @State private var isLoading = false
    
    // ✅ 로컬 모드에서는 서버 URL 불필요
    // let baseURL = "https://217.142.253.35.nip.io"
    
    init() {}
    
    var body: some View {
        ZStack {
            Color.white.ignoresSafeArea()
            
            VStack(spacing: 24) {
                Spacer()
                
                VStack(spacing: 8) {
                    Text("🌙")
                        .font(.system(size: 80))
                    Text("마음 온(Maum-On)")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                        .foregroundColor(.primary)
                    Text("On-Device Mode")
                        .font(.caption)
                        .foregroundColor(.gray)
                        .padding(.top, 4)
                }
                .padding(.bottom, 20)
                
                VStack(spacing: 16) {
                    TextField("닉네임 (로컬 프로필)", text: $username)
                        .padding()
                        .frame(height: 50)
                        .padding()
                        .background(Color.gray.opacity(0.1))
                        .cornerRadius(12)
                        #if os(iOS)
                        .textInputAutocapitalization(.never)
                        #endif
                        .shadow(color: Color.black.opacity(0.05), radius: 2, x: 0, y: 1)
                    
                    // 로컬 모드에서는 비밀번호 불필요
                    // SecureField("비밀번호", text: $password) ...
                }
                .padding(.horizontal, 24)
                
                if !errorMessage.isEmpty {
                    Text(errorMessage)
                        .foregroundColor(.red)
                        .font(.caption)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }
                
                Button(action: performLogin) {
                    if isLoading {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                    } else {
                        Text("로그인")
                            .font(.headline)
                            .fontWeight(.bold)
                            .frame(maxWidth: .infinity)
                            .frame(height: 50)
                    }
                }
                .background(Color.blue)
                .foregroundColor(.white)
                .cornerRadius(12)
                .padding(.horizontal, 24)
                .disabled(isLoading || username.isEmpty)
                
                Spacer()
            }
        }
    }
    
    func performLogin() {
        // 로컬 로그인 (단순 프로필 설정)
        guard !username.isEmpty else { return }
        
        isLoading = true
        
        // Simulate minor delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            isLoading = false
            print("✅ 로컬 로그인 성공: \(username)")
            
            // Generate a dummy token for local session
            let dummyToken = "local_token_\(UUID().uuidString)"
            authManager.login(token: dummyToken)
            
            // Set default risk level if not set
            if UserDefaults.standard.object(forKey: "userRiskLevel") == nil {
                authManager.setRiskLevel(1)
            }
        }
    }
    
    // fetchUserProfile is removed in Local Mode
}
