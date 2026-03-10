
import SwiftUI

struct AppEmergencyView: View {
    // Removed Binding as it is now a main tab view
    
    var body: some View {
        NavigationView { // Wrap in NavigationView for title support if needed, or just ZStack
            ZStack {
                Color(hexString: "F5F5F7").edgesIgnoringSafeArea(.all)
                
                ScrollView {
                    VStack(spacing: 20) {
                        // Header Message
                        VStack(spacing: 10) {
                            Text("당신은 혼자가 아닙니다.")
                                .font(.title2)
                                .fontWeight(.bold)
                            Text("지금 힘든 순간도 반드시 지나갑니다.\n전문가의 도움을 받아보세요.")
                                .multilineTextAlignment(.center)
                                .font(.system(size: 15))
                                .foregroundColor(.secondary)
                        }
                        .padding(.top, 30)
                        .padding(.bottom, 10)
                        
                        // Contacts List
                        VStack(spacing: 16) {
                            ContactRow(icon: "", name: "자살예방 상담전화", number: "1393", isHighlight: true)
                            ContactRow(icon: "", name: "정신건강 상담전화", number: "1577-0199")
                            ContactRow(icon: "", name: "경찰청 (긴급신고)", number: "112")
                            
                            // 정신건강복지센터 찾기 링크
                            Button(action: {
                                if let url = URL(string: "https://www.mentalhealth.go.kr") {
                                    #if os(iOS)
                                    UIApplication.shared.open(url)
                                    #endif
                                }
                            }) {
                                HStack {
                                    Image(systemName: "magnifyingglass")
                                        .font(.title2)
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text("가까운 정신건강복지센터 찾기")
                                            .font(.subheadline)
                                            .fontWeight(.medium)
                                            .foregroundColor(.blue)
                                        Text("mentalhealth.go.kr")
                                            .font(.caption)
                                            .foregroundColor(.gray)
                                    }
                                    Spacer()
                                    Image(systemName: "arrow.up.right.square")
                                        .foregroundColor(.blue)
                                }
                                .padding()
                                .background(Color.blue.opacity(0.05))
                                .cornerRadius(14)
                            }
                        }
                        .padding(.horizontal, 20)
                        
                        Spacer()
                    }
                    .padding(.bottom, 30)
                }
            }
            .navigationTitle("긴급 도움")
            .navigationBarTitleDisplayMode(.inline)
        }
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
                    .font(.system(size: 28))
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(name)
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(Color.black.opacity(0.8))
                    Text(number)
                        .font(.system(size: 20, weight: .bold))
                        .foregroundColor(.black)
                }
                
                Spacer()
                
                Text("전화하기")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white)
                    .padding(.vertical, 8)
                    .padding(.horizontal, 16)
                    .background(isHighlight ? Color(hexString: "E74C3C") : Color(hexString: "212529")) // 웹 스타일 적용
                    .cornerRadius(20)
            }
            .padding(20)
            .background(Color.white)
            .cornerRadius(20)
            .shadow(color: Color.black.opacity(0.05), radius: 10, x: 0, y: 5)
            .overlay(
                RoundedRectangle(cornerRadius: 20)
                    .stroke(isHighlight ? Color(hexString: "FFC9C9") : Color.clear, lineWidth: 1)
            )
        }
    }
    
    func callNumber(_ number: String) {
        let cleanNumber = number.filter("0123456789".contains)
        guard let url = URL(string: "tel://\(cleanNumber)") else { return }
        UIApplication.shared.open(url)
    }
}
