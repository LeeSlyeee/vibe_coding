
import SwiftUI

struct AppLoginView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var username = ""
    @State private var password = ""
    @State private var errorMessage = ""
    @State private var isLoading = false
    
    // ✅ 사용자분의 OCI 서버 도메인 (경로 문제 해결!)
    let baseURL = "https://217.142.253.35.nip.io"
    
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
                }
                .padding(.bottom, 20)
                
                VStack(spacing: 16) {
                    TextField("아이디", text: $username)
                        .padding()
                        .frame(height: 50)
                        .background(Color.white)
                        .foregroundColor(.black)
                        .cornerRadius(12)
                        .textInputAutocapitalization(.never)
                        .shadow(color: .black.opacity(0.05), radius: 2, x: 0, y: 1)
                    
                    SecureField("비밀번호", text: $password)
                        .padding()
                        .frame(height: 50)
                        .background(Color.white)
                        .foregroundColor(.black)
                        .cornerRadius(12)
                        .shadow(color: .black.opacity(0.05), radius: 2, x: 0, y: 1)
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
        // ✅ 수정됨: /api/auth/login -> /api/login 으로 변경 (서버 라우트와 일치)
        guard let url = URL(string: "\(baseURL)/api/login") else { return }
        
        isLoading = true
        errorMessage = ""
        
        let body: [String: String] = ["username": username, "password": password]
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        
        print("🚀 로그인 요청 시작: \(url.absoluteString)")
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                isLoading = false
            }
            
            if let error = error {
                DispatchQueue.main.async {
                    print("❌ 네트워크 에러: \(error)")
                    errorMessage = "네트워크 오류: \(error.localizedDescription)"
                }
                return
            }
            
            guard let data = data else { return }
            
            if let str = String(data: data, encoding: .utf8) {
                print("📩 서버 응답(Raw): \(str)")
            }
            
            do {
                if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                    if let token = json["access_token"] as? String {
                        print("✅ 로그인 성공! 토큰: \(token.prefix(10))...")
                        DispatchQueue.main.async {
                            authManager.login(token: token)
                        }
                    } else {
                        let msg = json["message"] as? String ?? "로그인 실패"
                        print("⚠️ 로그인 실패: \(msg)")
                        DispatchQueue.main.async {
                            errorMessage = msg
                        }
                    }
                } else {
                    print("❌ JSON 형식이 아님")
                    DispatchQueue.main.async { errorMessage = "서버 오류: 예상치 못한 응답입니다." }
                }
            } catch {
                print("❌ JSON 파싱 에러: \(error)")
                DispatchQueue.main.async { errorMessage = "응답 해석 오류" }
            }
        }.resume()
    }
}
