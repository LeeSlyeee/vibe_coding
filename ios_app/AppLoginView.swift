
import SwiftUI

struct AppLoginView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var username = ""
    @State private var password = ""
    @State private var name = "" // [New] 실명
    @State private var centerCode = "" // [New] 기관 코드
    @State private var errorMessage = ""
    @State private var isLoading = false
    @State private var isPasswordVisible = false // 비밀번호 기본 숨김 (눈 아이콘으로 토글)
    
    // ✅ 로컬 모드에서는 서버 URL 불필요
    // let baseURL = "http://150.230.7.76"
    
    init() {}
    
    var body: some View {
        ZStack {
            Color.white.ignoresSafeArea()
            
            ScrollView {
                VStack(spacing: 24) {
                    Spacer().frame(height: 60) // Top spacing
                    
                    VStack(spacing: 8) {
                        Text("🌙")
                            .font(.system(size: 80))
                        Text("마음온(maumON)")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                            .foregroundColor(.primary)
                        Text("로그인 및 시작하기")
                            .font(.caption)
                            .foregroundColor(.gray)
                            .padding(.top, 4)
                    }
                    .padding(.bottom, 20)
                    
                    VStack(spacing: 12) {
                        TextField("이름 (실명)", text: $name)
                            .keyboardType(.default)
                            .padding(.horizontal, 16)
                            .frame(height: 48)
                            .background(Color.gray.opacity(0.1))
                            .cornerRadius(12)
                            .tint(.blue)
                            .shadow(color: Color.black.opacity(0.05), radius: 2, x: 0, y: 1)
                        
                        TextField("아이디 (닉네임)", text: $username)
                            .keyboardType(.default)
                            .padding(.horizontal, 16)
                            .frame(height: 48)
                            .background(Color.gray.opacity(0.1))
                            .cornerRadius(12)
                            .tint(.blue)
                            .shadow(color: Color.black.opacity(0.05), radius: 2, x: 0, y: 1)

                        // [Fix] SecureField을 완전히 제거 → iOS 로그인 폼 감지 방지 → 서드파티 키보드 유지
                        // 비밀번호 마스킹은 시각적 오버레이로 처리
                        HStack {
                            ZStack(alignment: .leading) {
                                TextField("비밀번호", text: $password)
                                    .keyboardType(.default)
                                    .tint(.blue)
                                    .foregroundColor(isPasswordVisible ? .primary : .clear)
                                
                                if !isPasswordVisible && !password.isEmpty {
                                    Text(String(repeating: "●", count: password.count))
                                        .foregroundColor(.primary)
                                        .allowsHitTesting(false)
                                }
                            }
                            
                            Button(action: { isPasswordVisible.toggle() }) {
                                Image(systemName: isPasswordVisible ? "eye.slash" : "eye")
                                    .foregroundColor(.gray)
                            }
                        }
                        .padding(.horizontal, 16)
                        .frame(height: 48)
                        .background(Color.gray.opacity(0.1))
                        .cornerRadius(12)
                        .shadow(color: Color.black.opacity(0.05), radius: 2, x: 0, y: 1)
                            
                        TextField("기관 코드 (선택)", text: $centerCode)
                            .keyboardType(.default)
                            .padding(.horizontal, 16)
                            .frame(height: 48)
                            .background(Color(hexString: "f0fdf4"))
                            .cornerRadius(12)
                            .tint(.blue)
                            .shadow(color: Color.black.opacity(0.05), radius: 2, x: 0, y: 1)
                            .overlay(
                                RoundedRectangle(cornerRadius: 12)
                                    .stroke(Color.green.opacity(0.3), lineWidth: 1)
                            )
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
                    
                }
                .padding(.vertical)
            }
            #if os(iOS)
            .scrollDismissesKeyboard(.interactively)
            #endif
        }
        #if os(iOS)
        .dismissKeyboardOnTap() // [Cursor Fix] UIKit 기반 키보드 닫기 (TextField 포커스 방해 없음)
        #endif
    }
    
    // hideKeyboard() is now a global function in ViewExtensions.swift
    
    func performLogin() {
        guard !username.isEmpty, !password.isEmpty, !name.isEmpty else { return }
        
        #if os(iOS)
        dismissKeyboard()
        #endif
        
        isLoading = true
        errorMessage = ""
        
        // 이름(name)을 포함하여 로그인/가입 요청
        authManager.performLogin(username: username, password: password, name: name, centerCode: centerCode) { success, msg in
            self.isLoading = false
            if !success {
                self.errorMessage = msg
            } else {
                // 성공 시 자동으로 뷰가 전환됨
            }
        }
    }
}
