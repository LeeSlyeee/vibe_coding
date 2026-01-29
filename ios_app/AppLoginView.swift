
import SwiftUI

struct AppLoginView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var username = ""
    @State private var password = ""
    @State private var name = "" // [New] 실명
    @State private var errorMessage = ""
    @State private var isLoading = false
    
    // ✅ 로컬 모드에서는 서버 URL 불필요
    // let baseURL = "https://217.142.253.35.nip.io"
    
    init() {}
    
    var body: some View {
        ZStack {
            Color.white.ignoresSafeArea()
            
            ScrollView {
                VStack(spacing: 24) {
                    SizedBox(height: 60) // Top spacing
                    
                    VStack(spacing: 8) {
                        Text("🌙")
                            .font(.system(size: 80))
                        Text("마음 온(Maum-On)")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                            .foregroundColor(.primary)
                        Text("로그인 및 시작하기")
                            .font(.caption)
                            .foregroundColor(.gray)
                            .padding(.top, 4)
                    }
                    .padding(.bottom, 20)
                    
                    VStack(spacing: 16) {
                        TextField("아이디 (닉네임)", text: $username)
                            .padding()
                            .frame(height: 50)
                            .padding()
                            .background(Color.gray.opacity(0.1))
                            .cornerRadius(12)
                            #if os(iOS)
                            .textInputAutocapitalization(.never)
                            .keyboardType(.emailAddress)
                            #endif
                            .shadow(color: Color.black.opacity(0.05), radius: 2, x: 0, y: 1)
                        
                        TextField("이름 (실명)", text: $name)
                            .padding()
                            .frame(height: 50)
                            .padding()
                            .background(Color.gray.opacity(0.1))
                            .cornerRadius(12)
                            .shadow(color: Color.black.opacity(0.05), radius: 2, x: 0, y: 1)

                        SecureField("비밀번호", text: $password)
                            .padding()
                            .frame(height: 50)
                            .padding()
                            .background(Color.gray.opacity(0.1))
                            .cornerRadius(12)
                            .shadow(color: Color.black.opacity(0.05), radius: 2, x: 0, y: 1)
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
                            Text("로그인 / 회원가입") // 자동 가입이므로
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
                    .disabled(isLoading || username.isEmpty || password.isEmpty || name.isEmpty) // 이름도 필수
                    
                    SizedBox(height: 50) // Bottom spacing
                }
                .padding(.vertical)
            }
            .onTapGesture {
                hideKeyboard()
            }
        }
    }
    
    // Helper for spacing
    func SizedBox(height: CGFloat) -> some View {
        Spacer().frame(height: height)
    }
    
    #if os(iOS)
    func hideKeyboard() {
        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
    }
    #else
    func hideKeyboard() {}
    #endif
    
    func performLogin() {
        guard !username.isEmpty, !password.isEmpty, !name.isEmpty else { return }
        
        isLoading = true
        errorMessage = ""
        
        // 이름(name)을 포함하여 로그인/가입 요청
        authManager.performLogin(username: username, password: password, name: name) { success, msg in
            self.isLoading = false
            if !success {
                self.errorMessage = msg
            } else {
                // 성공 시 자동으로 뷰가 전환됨
            }
        }
    }
}
