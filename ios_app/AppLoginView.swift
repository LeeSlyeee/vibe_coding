
import SwiftUI

struct AppLoginView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var username = ""
    @State private var password = ""
    @State private var name = "" // 실명
    @State private var centerCode = "" // 기관 코드
    @State private var errorMessage = ""
    @State private var isLoading = false
    @State private var isPasswordVisible = false
    
    init() {}
    
    var body: some View {
        ZStack {
            // Geist: Pure White
            Color.white.ignoresSafeArea()
            
            ScrollView {
                VStack(spacing: 28) {
                    Spacer().frame(height: 60)
                    
                    // --- Header ---
                    VStack(spacing: 12) {
                        Image(systemName: "heart.text.clipboard")
                            .font(.system(size: 56, weight: .thin))
                            .foregroundColor(Color.gray900)
                        
                        Text("maumON")
                            .font(.system(size: 32, weight: .semibold))
                            .tracking(-1.28)
                            .foregroundColor(Color.gray900)
                        
                        Text("로그인 및 시작하기")
                            .font(.geistCaption)
                            .foregroundColor(Color.gray400)
                            .padding(.top, 2)
                    }
                    .padding(.bottom, 16)
                    
                    // --- Input Fields ---
                    VStack(spacing: 10) {
                        // Name
                        geistTextField("이름 (실명)", text: $name)
                        
                        // Username
                        geistTextField("아이디 (닉네임)", text: $username)
                        
                        // Password (visual masking)
                        HStack {
                            ZStack(alignment: .leading) {
                                TextField("비밀번호", text: $password)
                                    .keyboardType(.default)
                                    .tint(Color.gray900)
                                    .foregroundColor(isPasswordVisible ? .primary : .clear)
                                
                                if !isPasswordVisible && !password.isEmpty {
                                    Text(String(repeating: "●", count: password.count))
                                        .foregroundColor(Color.gray900)
                                        .allowsHitTesting(false)
                                }
                            }
                            
                            Button(action: { isPasswordVisible.toggle() }) {
                                Image(systemName: isPasswordVisible ? "eye.slash" : "eye")
                                    .foregroundColor(Color.gray400)
                                    .font(.system(size: 15))
                            }
                        }
                        .font(.system(size: 15))
                        .padding(.horizontal, 16)
                        .frame(height: 48)
                        .background(Color.white)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(Color.black.opacity(0.12), lineWidth: 1)
                        )
                        .cornerRadius(8)
                        
                        // Center Code (optional)
                        geistTextField("기관 코드 (선택)", text: $centerCode, isOptional: true)
                    }
                    .padding(.horizontal, 24)
                    
                    // --- Error ---
                    if !errorMessage.isEmpty {
                        HStack(spacing: 6) {
                            Image(systemName: "exclamationmark.circle")
                                .font(.system(size: 13))
                            Text(errorMessage)
                                .font(.geistCaption)
                        }
                        .foregroundColor(Color.geistRed)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                    }
                    
                    // --- Login Button (Geist Primary: dark) ---
                    Button(action: performLogin) {
                        if isLoading {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                .frame(maxWidth: .infinity)
                                .frame(height: 50)
                        } else {
                            Text("로그인 / 회원가입")
                                .font(.system(size: 15, weight: .medium))
                                .frame(maxWidth: .infinity)
                                .frame(height: 50)
                        }
                    }
                    .background(
                        RoundedRectangle(cornerRadius: 8)
                            .fill(Color.gray900)
                    )
                    .foregroundColor(.white)
                    .cornerRadius(8)
                    .padding(.horizontal, 24)
                    .disabled(isLoading || username.isEmpty || password.isEmpty || name.isEmpty)
                    .opacity((isLoading || username.isEmpty || password.isEmpty || name.isEmpty) ? 0.5 : 1.0)
                    
                }
                .padding(.vertical)
            }
        }
        #if os(iOS)
        .dismissKeyboardOnTap()
        #endif
    }
    
    // --- Geist-style TextField Component ---
    @ViewBuilder
    func geistTextField(_ placeholder: String, text: Binding<String>, isOptional: Bool = false) -> some View {
        TextField(placeholder, text: text)
            .keyboardType(.default)
            .font(.system(size: 15))
            .tint(Color.gray900)
            .padding(.horizontal, 16)
            .frame(height: 48)
            .background(Color.white)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(isOptional ? Color.black.opacity(0.06) : Color.black.opacity(0.12), lineWidth: 1)
            )
            .cornerRadius(8)
    }
    
    func performLogin() {
        guard !username.isEmpty, !password.isEmpty, !name.isEmpty else { return }
        
        #if os(iOS)
        dismissKeyboard()
        #endif
        
        isLoading = true
        errorMessage = ""
        
        authManager.performLogin(username: username, password: password, name: name, centerCode: centerCode) { success, msg in
            self.isLoading = false
            if !success {
                self.errorMessage = msg
            }
        }
    }
}
