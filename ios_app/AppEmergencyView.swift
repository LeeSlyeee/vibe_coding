
import SwiftUI

struct AppEmergencyView: View {
    @Binding var isPresented: Bool
    
    var body: some View {
        ZStack {
            // 배경: 반투명 오버레이 효과 (Sheet의 경우 기본 배경이 있지만 커스텀 느낌을 위해)
            Color.black.opacity(0.4)
                .edgesIgnoringSafeArea(.all)
                .onTapGesture {
                    withAnimation {
                        isPresented = false
                    }
                }
            
            // Safety Card
            VStack(spacing: 0) {
                // Header
                HStack {
                    Text("🆘 긴급 도움 요청")
                        .font(.title3)
                        .fontWeight(.black)
                        .foregroundColor(Color(hexString: "E74C3C")) // 웹: #e74c3c
                    
                    Spacer()
                    
                    Button(action: {
                        withAnimation {
                            isPresented = false
                        }
                    }) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 24))
                            .foregroundColor(Color.gray.opacity(0.5))
                    }
                }
                .padding(24)
                
                // Contacts List
                VStack(spacing: 12) {
                    ContactRow(icon: "📞", name: "자살예방 상담전화", number: "1393", isHighlight: true)
                    ContactRow(icon: "🏥", name: "정신건강 상담전화", number: "1577-0199")
                    ContactRow(icon: "👮", name: "경찰청 (긴급신고)", number: "112")
                }
                .padding(.horizontal, 24)
                
                // Message
                VStack(spacing: 8) {
                    Text("당신은 혼자가 아닙니다.")
                        .fontWeight(.bold)
                    Text("지금 힘든 순간도 반드시 지나갑니다.\n전문가의 도움을 받아보세요.")
                        .multilineTextAlignment(.center)
                        .font(.system(size: 14))
                        .foregroundColor(.gray)
                }
                .padding(24)
                .padding(.top, 10)
                
            }
            .background(Color.white)
            .cornerRadius(24)
            .padding(20)
            .shadow(radius: 20)
        }
        .edgesIgnoringSafeArea(.all)
    }
}

// Sub Component: Contact Row
struct ContactRow: View {
    let icon: String
    let name: String
    let number: String
    var isHighlight: Bool = false
    
    var body: some View {
        Button(action: {
            callNumber(number.replacingOccurrences(of: "-", with: ""))
        }) {
            HStack(spacing: 16) {
                Text(icon)
                    .font(.system(size: 24))
                
                VStack(alignment: .leading, spacing: 2) {
                    Text(name)
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(Color.black.opacity(0.7))
                    Text(number)
                        .font(.system(size: 18, weight: .bold))
                        .foregroundColor(.black)
                }
                
                Spacer()
                
                Text("전화하기")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(.white)
                    .padding(.vertical, 6)
                    .padding(.horizontal, 12)
                    .background(isHighlight ? Color(hexString: "E74C3C") : Color(hexString: "212529")) // 웹 스타일 적용
                    .cornerRadius(20)
            }
            .padding(16)
            .background(isHighlight ? Color(hexString: "FFF5F5") : Color(hexString: "F8F9FA"))
            .cornerRadius(16)
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(isHighlight ? Color(hexString: "FFC9C9") : Color.clear, lineWidth: 1)
            )
        }
    }
    
    func callNumber(_ number: String) {
        guard let url = URL(string: "tel://\(number)") else { return }
        UIApplication.shared.open(url)
    }
}


