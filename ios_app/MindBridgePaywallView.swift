import SwiftUI
import StoreKit

// MARK: - 마음 브릿지 페이월 뷰
struct MindBridgePaywallView: View {
    @Binding var isPresented: Bool
    @StateObject private var subscriptionManager = SubscriptionManager.shared
    
    // 애니메이션 상태
    @State private var appearAnimation = false
    @State private var showFeatures = false
    
    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // 닫기 버튼
                HStack {
                    Spacer()
                    Button(action: { isPresented = false }) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.title2)
                            .foregroundColor(.gray.opacity(0.6))
                    }
                }
                .padding(.top, 8)
                
                // MARK: - 헤더
                VStack(spacing: 12) {
                    // 아이콘
                    ZStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [Color(hexString: "6366f1"), Color(hexString: "8b5cf6")],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 80, height: 80)
                            .shadow(color: Color(hexString: "6366f1").opacity(0.3), radius: 12, x: 0, y: 6)
                        
                        Image(systemName: "heart.text.clipboard")
                            .font(.system(size: 36))
                            .foregroundColor(.white)
                    }
                    .scaleEffect(appearAnimation ? 1.0 : 0.5)
                    .opacity(appearAnimation ? 1.0 : 0)
                    .animation(.spring(response: 0.6, dampingFraction: 0.7), value: appearAnimation)
                    
                    Text("마음 브릿지")
                        .font(.title)
                        .fontWeight(.bold)
                    
                    Text("소중한 사람에게\n내 마음을 안전하게 전해보세요")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                }
                
                // MARK: - 기능 목록
                VStack(spacing: 0) {
                    BridgeFeatureRow(
                        icon: "person.2.fill",
                        iconColor: Color(hexString: "6366f1"),
                        title: "가족/보호자 안심 공유",
                        description: "매일 또는 매주, 감정 상태를 카카오톡으로 안전하게 전달",
                        delay: 0.1
                    )
                    
                    Divider().padding(.leading, 56)
                    
                    BridgeFeatureRow(
                        icon: "stethoscope",
                        iconColor: Color(hexString: "10b981"),
                        title: "상담사 전용 대시보드",
                        description: "AI 분석 리포트를 상담사에게 공유, 더 깊은 상담 가능",
                        delay: 0.2
                    )
                    
                    Divider().padding(.leading, 56)
                    
                    BridgeFeatureRow(
                        icon: "slider.horizontal.3",
                        iconColor: Color(hexString: "f59e0b"),
                        title: "공유 깊이 직접 설정",
                        description: "누구에게, 어디까지 보여줄지 내가 직접 결정",
                        delay: 0.3
                    )
                    
                    Divider().padding(.leading, 56)
                    
                    BridgeFeatureRow(
                        icon: "lock.shield.fill",
                        iconColor: Color(hexString: "ef4444"),
                        title: "일기 원문은 절대 공유 안 됨",
                        description: "AI가 분석한 결과만 공유, 프라이버시 100% 보장",
                        delay: 0.4
                    )
                }
                .padding(.vertical, 8)
                .background(Color(.systemBackground))
                .cornerRadius(16)
                .shadow(color: .black.opacity(0.05), radius: 8, x: 0, y: 2)
                
                // MARK: - B2G 안내
                HStack(alignment: .top, spacing: 10) {
                    Text("🏥")
                    VStack(alignment: .leading, spacing: 4) {
                        Text("보건소/정신건강복지센터 안내")
                            .font(.system(size: 14, weight: .bold))
                            .foregroundColor(Color(hexString: "15803d"))
                        Text("관할 보건소나 정신건강복지센터에서 서비스를 받으면 무료 업그레이드가 가능합니다.")
                            .font(.system(size: 13))
                            .foregroundColor(Color(hexString: "15803d"))
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    Spacer()
                }
                .padding(15)
                .background(Color(hexString: "f0fdf4"))
                .cornerRadius(12)
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(Color(hexString: "dcfce7"), lineWidth: 1)
                )
                
                // MARK: - 가격 & 구매
                VStack(spacing: 12) {
                    // 무료 체험 배지
                    Text("7일 무료 체험")
                        .font(.caption)
                        .fontWeight(.bold)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(Color(hexString: "6366f1").opacity(0.1))
                        .foregroundColor(Color(hexString: "6366f1"))
                        .cornerRadius(20)
                    
                    // 가격
                    HStack(alignment: .lastTextBaseline, spacing: 4) {
                        Text(subscriptionManager.priceText)
                            .font(.title)
                            .fontWeight(.bold)
                            .foregroundColor(.primary)
                        
                        Text("/월")
                            .font(.subheadline)
                            .foregroundColor(.gray)
                    }
                    
                    // 구매 버튼
                    Button(action: {
                        Task {
                            await subscriptionManager.purchase()
                            if subscriptionManager.isSubscribed {
                                isPresented = false
                            }
                        }
                    }) {
                        HStack {
                            if subscriptionManager.isLoading {
                                ProgressView()
                                    .tint(.white)
                                    .padding(.trailing, 4)
                            }
                            Text(subscriptionManager.isLoading ? "처리 중..." : "무료 체험 시작하기")
                                .fontWeight(.bold)
                                .font(.system(size: 17))
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 16)
                        .background(
                            LinearGradient(
                                colors: [Color(hexString: "6366f1"), Color(hexString: "8b5cf6")],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .foregroundColor(.white)
                        .cornerRadius(14)
                        .shadow(color: Color(hexString: "6366f1").opacity(0.3), radius: 8, x: 0, y: 4)
                    }
                    .disabled(subscriptionManager.isLoading)
                    
                    // 에러 메시지
                    if let error = subscriptionManager.purchaseError {
                        Text(error)
                            .font(.caption)
                            .foregroundColor(.red)
                            .multilineTextAlignment(.center)
                    }
                    
                    // 구독 복원
                    Button(action: {
                        Task {
                            await subscriptionManager.restore()
                        }
                    }) {
                        Text("이전 구독 복원하기")
                            .font(.caption)
                            .foregroundColor(.gray)
                    }
                    
                    // 안내 문구
                    Text("언제든 해지 가능합니다. 무료 체험 기간 내 해지 시 과금되지 않습니다.")
                        .font(.caption2)
                        .foregroundColor(.gray)
                        .multilineTextAlignment(.center)
                }
            }
            .padding(24)
        }
        .background(Color(.systemGroupedBackground))
        .onAppear {
            withAnimation {
                appearAnimation = true
            }
        }
    }
}

// MARK: - 기능 행
struct BridgeFeatureRow: View {
    let icon: String
    let iconColor: Color
    let title: String
    let description: String
    let delay: Double
    
    @State private var appeared = false
    
    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 20))
                .foregroundColor(iconColor)
                .frame(width: 40, height: 40)
                .background(iconColor.opacity(0.1))
                .cornerRadius(10)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.bold)
                Text(description)
                    .font(.caption)
                    .foregroundColor(.gray)
                    .fixedSize(horizontal: false, vertical: true)
            }
            
            Spacer()
        }
        .padding(.vertical, 12)
        .padding(.horizontal, 16)
        .opacity(appeared ? 1.0 : 0)
        .offset(x: appeared ? 0 : 20)
        .onAppear {
            withAnimation(.easeOut(duration: 0.4).delay(delay)) {
                appeared = true
            }
        }
    }
}
