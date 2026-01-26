
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
            if let error = error {
                DispatchQueue.main.async {
                    isLoading = false
                    print("❌ 네트워크 에러: \(error)")
                    errorMessage = "네트워크 오류: \(error.localizedDescription)"
                }
                return
            }
            
            guard let data = data else { return }
            
            do {
                if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                    if let token = json["access_token"] as? String {
                        print("✅ 로그인 성공! 토큰: \(token.prefix(10))...")
                        // 1. 토큰 저장
                        DispatchQueue.main.async {
                            authManager.login(token: token)
                            // 2. 사용자 프로필(위험도) 가져오기
                            fetchUserProfile(token: token)
                        }
                    } else {
                        let msg = json["message"] as? String ?? "로그인 실패"
                        DispatchQueue.main.async {
                            isLoading = false
                            errorMessage = msg
                        }
                    }
                } else {
                    DispatchQueue.main.async { isLoading = false; errorMessage = "서버 오류: JSON 파싱 불가" }
                }
            } catch {
                DispatchQueue.main.async { isLoading = false; errorMessage = "응답 해석 오류" }
            }
        }.resume()
    }
    
    func fetchUserProfile(token: String) {
        guard let url = URL(string: "\(baseURL)/api/user/me") else { 
            DispatchQueue.main.async { isLoading = false }
            return 
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        URLSession.shared.dataTask(with: request) { data, _, error in
            DispatchQueue.main.async {
                isLoading = false
            }
            
            if let data = data, let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                // 위험도 동기화 (기본값 1)
                let rLevel = json["risk_level"] as? Int ?? 1
                print("📊 사용자 위험도 로드: Level \(rLevel)")
                
                DispatchQueue.main.async {
                    authManager.setRiskLevel(rLevel)
                    
                    // 만약 위험도 설정이 안 된 신규 유저(0 or nil)라면? 
                    // (But backend defaults to 1 usually)
                    // 필요 시 여기서 가입 직후 진단 화면으로 보내는 로직 추가 가능
                }
            }
        }.resume()
    }
}
