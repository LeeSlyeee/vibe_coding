import Foundation
import StoreKit

// MARK: - 마음 브릿지 구독 관리 (StoreKit 2)
@MainActor
class SubscriptionManager: ObservableObject {
    static let shared = SubscriptionManager()
    
    // MARK: - Product ID
    /// App Store Connect에서 설정한 구독 상품 ID
    static let mindBridgeProductID = "com.maumon.mindbridge.monthly"
    
    // MARK: - Published State
    @Published var isSubscribed: Bool = false
    @Published var product: Product?
    @Published var purchaseError: String?
    @Published var isLoading: Bool = false
    
    // 구독 상태 상세
    @Published var expirationDate: Date?
    @Published var isInTrialPeriod: Bool = false
    
    private var updateListenerTask: Task<Void, Error>?
    
    // MARK: - Init
    private init() {
        // 앱 시작 시 구독 상태 복원
        updateListenerTask = listenForTransactions()
        
        Task {
            await loadProduct()
            await updateSubscriptionStatus()
        }
    }
    
    deinit {
        updateListenerTask?.cancel()
    }
    
    // MARK: - 상품 로드
    func loadProduct() async {
        do {
            let products = try await Product.products(for: [Self.mindBridgeProductID])
            if let mindBridge = products.first {
                self.product = mindBridge
                print("✅ [Subscription] 상품 로드 완료: \(mindBridge.displayName) - \(mindBridge.displayPrice)")
            } else {
                print("⚠️ [Subscription] 상품을 찾을 수 없음. Product ID 확인 필요: \(Self.mindBridgeProductID)")
            }
        } catch {
            print("❌ [Subscription] 상품 로드 실패: \(error.localizedDescription)")
        }
    }
    
    // MARK: - 구매
    func purchase() async {
        guard let product = product else {
            purchaseError = "상품 정보를 불러올 수 없습니다."
            return
        }
        
        isLoading = true
        purchaseError = nil
        
        do {
            let result = try await product.purchase()
            
            switch result {
            case .success(let verification):
                let transaction = try checkVerified(verification)
                
                // 구독 상태 업데이트
                await updateSubscriptionStatus()
                
                // 트랜잭션 완료 처리
                await transaction.finish()
                
                print("✅ [Subscription] 구매 성공!")
                
            case .userCancelled:
                print("ℹ️ [Subscription] 사용자가 구매를 취소함")
                
            case .pending:
                print("⏳ [Subscription] 구매 승인 대기 중 (가족 공유 등)")
                
            @unknown default:
                print("⚠️ [Subscription] 알 수 없는 구매 결과")
            }
        } catch {
            purchaseError = "구매 중 오류가 발생했습니다: \(error.localizedDescription)"
            print("❌ [Subscription] 구매 오류: \(error)")
        }
        
        isLoading = false
    }
    
    // MARK: - 구독 복원
    func restore() async {
        isLoading = true
        
        do {
            try await AppStore.sync()
            await updateSubscriptionStatus()
            print("✅ [Subscription] 구독 복원 완료")
        } catch {
            purchaseError = "구독 복원에 실패했습니다."
            print("❌ [Subscription] 복원 실패: \(error)")
        }
        
        isLoading = false
    }
    
    // MARK: - 구독 상태 업데이트
    func updateSubscriptionStatus() async {
        var hasActiveSubscription = false
        
        for await result in Transaction.currentEntitlements {
            do {
                let transaction = try checkVerified(result)
                
                if transaction.productID == Self.mindBridgeProductID {
                    // 구독이 취소되지 않았고, 만료되지 않았는지 확인
                    if transaction.revocationDate == nil {
                        hasActiveSubscription = true
                        expirationDate = transaction.expirationDate
                        
                        // 체험 기간 여부 확인
                        if let offerType = transaction.offerType {
                            isInTrialPeriod = (offerType == .introductory)
                        }
                    }
                }
            } catch {
                print("⚠️ [Subscription] 트랜잭션 검증 실패: \(error)")
            }
        }
        
        isSubscribed = hasActiveSubscription
        
        // UserDefaults에도 캐싱 (오프라인 대비)
        UserDefaults.standard.set(hasActiveSubscription, forKey: "mindBridge_subscribed")
        
        print("📊 [Subscription] 상태 업데이트: \(isSubscribed ? "구독 중" : "미구독")")
    }
    
    // MARK: - 트랜잭션 리스너
    private func listenForTransactions() -> Task<Void, Error> {
        return Task.detached {
            for await result in Transaction.updates {
                do {
                    let transaction = try await self.checkVerified(result)
                    await self.updateSubscriptionStatus()
                    await transaction.finish()
                } catch {
                    print("⚠️ [Subscription] 트랜잭션 업데이트 처리 실패: \(error)")
                }
            }
        }
    }
    
    // MARK: - 검증 헬퍼
    private func checkVerified<T>(_ result: VerificationResult<T>) throws -> T {
        switch result {
        case .unverified:
            throw SubscriptionError.verificationFailed
        case .verified(let safe):
            return safe
        }
    }
    
    // MARK: - 편의 프로퍼티
    
    /// 구독 중이거나 B2G 연동(무료 업그레이드)인 경우 true
    var hasMindBridgeAccess: Bool {
        return isSubscribed || B2GManager.shared.isLinked
    }
    
    /// 가격 표시 텍스트
    var priceText: String {
        product?.displayPrice ?? "₩5,500"
    }
    
    /// 구독 만료까지 남은 일수
    var daysUntilExpiry: Int? {
        guard let expiry = expirationDate else { return nil }
        return Calendar.current.dateComponents([.day], from: Date(), to: expiry).day
    }
}

// MARK: - Error
enum SubscriptionError: LocalizedError {
    case verificationFailed
    
    var errorDescription: String? {
        switch self {
        case .verificationFailed:
            return "구독 검증에 실패했습니다."
        }
    }
}
