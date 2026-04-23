import SwiftUI

// MARK: - Premium Modal View
struct PremiumModalView: View {
    @Binding var isPresented: Bool
    var onUpgrade: () -> Void
    @State private var showingAlert = false
    
    var body: some View {
        VStack(spacing: 24) {
            // Close Button
            HStack {
                Spacer()
                Button(action: { isPresented = false }) {
                    Image(systemName: "xmark")
                        .foregroundColor(.hintText)
                        .padding(5)
                }
            }
            
            // Header
            VStack(spacing: 8) {
                Text("마음챙김 플러스 +")
                    .font(.title2)
                    .fontWeight(.bold)
                Text("더 깊은 이해와 치유를 위한 선택")
                    .font(.subheadline)
                    .foregroundColor(.hintText)
            }
            
            // Features
            VStack(alignment: .leading, spacing: 16) {
                FeatureRow(icon: "chart.bar.fill", title: "심층 분석 리포트", desc: "나의 감정 패턴과 원인을 깊이 있게 분석해드려요.")
                FeatureRow(icon: "message.fill", title: "AI 감정 케어", desc: "24시간 언제든 내 마음을 기록하고 따뜻한 위로를 받으세요.")
                FeatureRow(icon: "calendar", title: "월간 감정 통계", desc: "한 달간의 감정 변화를 그래프로 확인하세요.")
            }
            .padding(.vertical)
            
            // ✅ Dobong-gu Notice (Green Box)
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: "building.2.fill").foregroundColor(.accent)
                VStack(alignment: .leading, spacing: 4) {
                    Text("보건소/정신건강복지센터 안내")
                        .font(.system(size: 14, weight: .bold))
                        .foregroundColor(Color.gray900)
                    Text("관할 보건소나 정신건강복지센터에서 서비스를 받으면 무료 업그레이드가 가능합니다.")
                        .font(.system(size: 13))
                        .foregroundColor(Color.gray900)
                        .fixedSize(horizontal: false, vertical: true)
                }
                Spacer()
            }
            .padding(15)
            .background(Color.gray50)
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(Color.gray100, lineWidth: 1)
            )
            
            // Price
            HStack(alignment: .lastTextBaseline, spacing: 8) {
                Text("₩9,900")
                    .font(.callout)
                    .strikethrough()
                    .foregroundColor(.hintText)
                
                Text("₩4,900")
                    .font(.title)
                    .fontWeight(.bold)
                    .foregroundColor(.primary)
                
                Text("/월")
                    .font(.caption)
                    .foregroundColor(.hintText)
                
                Text("런칭 특가 50%")
                    .font(.caption)
                    .fontWeight(.bold)
                    .padding(4)
                    .background(Color.red.opacity(0.1))
                    .foregroundColor(.red)
                    .cornerRadius(4)
            }
            
            Button(action: { showingAlert = true }) {
                Text("지금 시작하기")
                .fontWeight(.bold)
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.accent)
                .foregroundColor(.white)
                .cornerRadius(14)
            }
            .alert(isPresented: $showingAlert) {
                Alert(
                    title: Text("결제 확인"),
                    message: Text("4,900원을 결제하시겠습니까? (테스트)"),
                    primaryButton: .default(Text("결제하기"), action: onUpgrade),
                    secondaryButton: .cancel()
                )
            }
            
            Text("언제든 해지 가능합니다.")
                .font(.caption)
                .foregroundColor(.hintText)
        }
        .padding(24)
        .background(Color.white)
        .cornerRadius(24)
        .shadow(radius: 20)
        .padding(20)
    }
}

struct FeatureRow: View {
    let icon: String
    let title: String
    let desc: String
    
    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 20))
                .foregroundColor(.black)
                .frame(width: 40, height: 40)
                .background(Color.white)
                .cornerRadius(10)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.bold)
                Text(desc)
                    .font(.caption)
                    .foregroundColor(.hintText)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }
}
