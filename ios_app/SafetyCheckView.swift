
import SwiftUI

struct SafetyCheckView: View {
    let username: String
    @Environment(\.presentationMode) var presentationMode
    @State private var showResult = false
    @State private var resultStatus = ""
    @State private var isLoading = false
    
    var body: some View {
        ZStack {
            // Geist: Pure White background
            Color.white.edgesIgnoringSafeArea(.all)
            
            VStack(spacing: 0) {
                Spacer()
                
                // 아이콘
                ZStack {
                    Circle()
                        .fill(Color.gray50)
                        .frame(width: 120, height: 120)
                    
                    Text("💛")
                        .font(.system(size: 60))
                }
                .padding(.bottom, 32)
                
                // 제목
                Text("안녕하세요, 잘 지내고 계신가요?")
                    .font(.system(size: 24, weight: .semibold))
                    .tracking(-0.5)
                    .foregroundColor(Color.gray900)
                    .multilineTextAlignment(.center)
                
                Text("며칠째 일기가 없어서\n마음온이 걱정하고 있었어요")
                    .font(.system(size: 16))
                    .foregroundColor(Color.gray400)
                    .multilineTextAlignment(.center)
                    .lineSpacing(6)
                    .padding(.top, 12)
                
                Spacer()
                
                // 버튼들
                VStack(spacing: 16) {
                    // 괜찮아요 버튼
                    Button(action: {
                        sendConfirm(status: "ok")
                    }) {
                        HStack(spacing: 12) {
                            Text("👋")
                                .font(.system(size: 24))
                            VStack(alignment: .leading, spacing: 2) {
                                Text("괜찮아요, 잘 지내고 있어요!")
                                    .font(.system(size: 17, weight: .bold))
                                    .foregroundColor(.white)
                                Text("보호자에게 안전 확인 알림을 보내드릴게요")
                                    .font(.system(size: 12))
                                    .foregroundColor(.white.opacity(0.8))
                            }
                            Spacer()
                        }
                        .padding(.horizontal, 24)
                        .padding(.vertical, 20)
                        .background(
                            RoundedRectangle(cornerRadius: 12)
                                .fill(Color.gray900)
                        )
                        .cornerRadius(12)
                    }
                    .disabled(isLoading)
                    
                    // 도움이 필요해요 버튼
                    Button(action: {
                        sendConfirm(status: "need_help")
                    }) {
                        HStack(spacing: 12) {
                            Text("🆘")
                                .font(.system(size: 24))
                            VStack(alignment: .leading, spacing: 2) {
                                Text("도움이 필요해요")
                                    .font(.system(size: 17, weight: .bold))
                                    .foregroundColor(.white)
                                Text("보호자에게 긴급 알림을 보내드릴게요")
                                    .font(.system(size: 12))
                                    .foregroundColor(.white.opacity(0.8))
                            }
                            Spacer()
                        }
                        .padding(.horizontal, 24)
                        .padding(.vertical, 20)
                        .background(
                            RoundedRectangle(cornerRadius: 12)
                                .fill(Color.geistRed)
                        )
                        .cornerRadius(12)
                    }
                    .disabled(isLoading)
                }
                .padding(.horizontal, 24)
                
                // 긴급 연락처
                VStack(spacing: 8) {
                    Text("즉시 도움이 필요하시면")
                        .font(.system(size: 13))
                        .foregroundColor(Color.gray400)
                    
                    HStack(spacing: 20) {
                        emergencyButton(label: "자살예방상담", number: "1393")
                        emergencyButton(label: "정신건강위기", number: "1577-0199")
                        emergencyButton(label: "긴급신고", number: "112")
                    }
                }
                .padding(.top, 24)
                .padding(.bottom, 40)
            }
            
            // 결과 오버레이
            if showResult {
                resultOverlay
            }
            
            // 로딩
            if isLoading {
                Color.black.opacity(0.2)
                    .edgesIgnoringSafeArea(.all)
                ProgressView()
                    .scaleEffect(1.5)
                    .tint(.white)
            }
        }
    }
    
    // MARK: - 결과 오버레이
    
    @ViewBuilder
    var resultOverlay: some View {
        ZStack {
            Color.black.opacity(0.5)
                .edgesIgnoringSafeArea(.all)
            
            VStack(spacing: 24) {
                if resultStatus == "ok" {
                    ZStack {
                        Circle()
                            .fill(Color.green.opacity(0.15))
                            .frame(width: 100, height: 100)
                        Text("✅")
                            .font(.system(size: 50))
                    }
                    
                    Text("안전 확인 완료!")
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    Text("괜찮다는 응답이 전달되었습니다.\n마음온이 항상 곁에 있을게요 💛")
                        .font(.body)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                        .lineSpacing(4)
                    
                } else {
                    ZStack {
                        Circle()
                            .fill(Color.red.opacity(0.15))
                            .frame(width: 100, height: 100)
                        Text("🆘")
                            .font(.system(size: 50))
                    }
                    
                    Text("도움 요청이 전달되었습니다")
                        .font(.title2)
                        .fontWeight(.bold)
                    
                    Text("연결된 보호자에게\n긴급 알림이 발송되었습니다.")
                        .font(.body)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                        .lineSpacing(4)
                    
                    // 1393 전화 버튼
                    Button(action: {
                        if let url = URL(string: "tel://1393") {
                            UIApplication.shared.open(url)
                        }
                    }) {
                        HStack {
                            Image(systemName: "phone.fill")
                            Text("자살예방상담전화 1393")
                        }
                        .font(.headline)
                        .foregroundColor(.white)
                        .padding(.horizontal, 24)
                        .padding(.vertical, 14)
                        .background(Color.red)
                        .cornerRadius(16)
                    }
                }
                
                Button(action: {
                    presentationMode.wrappedValue.dismiss()
                    DeepLinkManager.shared.activeScreen = nil
                }) {
                    Text("닫기")
                        .font(.headline)
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 16)
                        .background(Color.gray900)
                        .cornerRadius(16)
                }
                .padding(.horizontal, 20)
            }
            .padding(.vertical, 40)
            .padding(.horizontal, 24)
            .background(
                RoundedRectangle(cornerRadius: 28)
                    .fill(Color.white)
                    .shadow(color: Color.black.opacity(0.15), radius: 20, x: 0, y: 10)
            )
            .padding(30)
        }
        .transition(.opacity)
    }
    
    // MARK: - 긴급 전화 버튼
    
    func emergencyButton(label: String, number: String) -> some View {
        Button(action: {
            let clean = number.components(separatedBy: CharacterSet.decimalDigits.inverted).joined()
            if let url = URL(string: "tel://\(clean)") {
                UIApplication.shared.open(url)
            }
        }) {
            VStack(spacing: 4) {
                Image(systemName: "phone.fill")
                    .font(.system(size: 14))
                    .foregroundColor(.red)
                Text(label)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(Color.gray500)
                Text(number)
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(Color.geistRed)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(Color.white)
            .cornerRadius(12)
            .shadow(color: Color.black.opacity(0.05), radius: 5, x: 0, y: 2)
        }
    }
    
    // MARK: - 서버 전송
    
    func sendConfirm(status: String) {
        guard !username.isEmpty else { return }
        isLoading = true
        
        guard let url = URL(string: ServerConfig.apiBase + "/safety/quick-confirm") else {
            isLoading = false
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: [
            "username": username,
            "status": status
        ])
        
        URLSession.shared.dataTask(with: request) { _, response, error in
            DispatchQueue.main.async {
                isLoading = false
                resultStatus = status
                withAnimation(.easeInOut(duration: 0.3)) {
                    showResult = true
                }
            }
        }.resume()
    }
}
