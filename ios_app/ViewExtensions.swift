
import SwiftUI
import UIKit
import Combine

// MARK: - Keyboard Observer (키보드 높이 실시간 감지)
#if os(iOS)
class KeyboardObserver: ObservableObject {
    @Published var keyboardHeight: CGFloat = 0
    @Published var isKeyboardVisible: Bool = false
    
    private var cancellables = Set<AnyCancellable>()
    private var hideWorkItem: DispatchWorkItem?
    
    init() {
        NotificationCenter.default.publisher(for: UIResponder.keyboardWillShowNotification)
            .compactMap { notification -> CGFloat? in
                (notification.userInfo?[UIResponder.keyboardFrameEndUserInfoKey] as? CGRect)?.height
            }
            .receive(on: DispatchQueue.main)
            .sink { [weak self] height in
                // [Keyboard Fix] 언어 전환 시 Hide→Show 빠른 전환: 대기 중인 Hide 취소
                self?.hideWorkItem?.cancel()
                self?.hideWorkItem = nil
                self?.keyboardHeight = height
                self?.isKeyboardVisible = true
            }
            .store(in: &cancellables)
        
        NotificationCenter.default.publisher(for: UIResponder.keyboardWillHideNotification)
            .receive(on: DispatchQueue.main)
            .sink { [weak self] _ in
                // [Keyboard Fix] 디바운스(0.15s): 키보드 언어 전환 시 Hide→Show 사이클 흡수
                self?.hideWorkItem?.cancel()
                let workItem = DispatchWorkItem { [weak self] in
                    self?.keyboardHeight = 0
                    self?.isKeyboardVisible = false
                    self?.hideWorkItem = nil
                }
                self?.hideWorkItem = workItem
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.15, execute: workItem)
            }
            .store(in: &cancellables)
    }
}
#endif

// MARK: - Global Keyboard Dismiss Utility
#if os(iOS)
func dismissKeyboard() {
    UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
}
#endif

// MARK: - Safe Data Wrapper
// (기존 코드 유지)

extension View {
    @ViewBuilder
    func onChangeCompat<V: Equatable>(of value: V, perform action: @escaping (V) -> Void) -> some View {
        if #available(iOS 17.0, *) {
            self.onChange(of: value) { _, newValue in
                action(newValue)
            }
        } else {
            self.onChange(of: value, perform: action)
        }
    }
    
    // 드래그 시 키보드 닫기 modifier
    #if os(iOS)
    func dismissKeyboardOnDrag() -> some View {
        self.gesture(
            DragGesture(minimumDistance: 20, coordinateSpace: .local)
                .onChanged { _ in
                    dismissKeyboard()
                }
        )
    }
    
    // [Cursor Fix] 빈 영역 탭 시 키보드 닫기 (TextField 포커스를 방해하지 않음)
    // SwiftUI onTapGesture는 TextField의 First Responder 획득을 가로채므로,
    // UIKit UITapGestureRecognizer(cancelsTouchesInView: false)를 사용하여
    // 입력창 터치 시 커서가 정상적으로 나타나면서, 빈 영역 탭 시에만 키보드가 닫히도록 함
    func dismissKeyboardOnTap() -> some View {
        self.background(
            KeyboardDismissTapView()
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        )
    }
    #endif
}

// MARK: - [Cursor Fix] UIKit 기반 키보드 닫기 탭 뷰
// 핵심: UIGestureRecognizerDelegate로 터치 대상을 검사하여
// UITextField/UITextView 위의 터치는 제스처를 아예 무시 → 포커스 방해 없음
// 빈 영역 터치만 제스처 인식 → dismissKeyboard() 호출
#if os(iOS)
struct KeyboardDismissTapView: UIViewRepresentable {
    func makeUIView(context: Context) -> UIView {
        let view = UIView()
        view.backgroundColor = .clear
        
        let tapGesture = UITapGestureRecognizer(target: context.coordinator, action: #selector(Coordinator.handleTap))
        tapGesture.cancelsTouchesInView = false
        tapGesture.delegate = context.coordinator // ⭐️ 핵심: delegate로 터치 필터링
        view.addGestureRecognizer(tapGesture)
        
        return view
    }
    
    func updateUIView(_ uiView: UIView, context: Context) {}
    
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }
    
    class Coordinator: NSObject, UIGestureRecognizerDelegate {
        @objc func handleTap() {
            // 사용자가 빈 영역을 탭하여 의도적으로 키보드를 닫음 → 알림 발송
            // AppDiaryWriteView 등에서 이를 수신하여 포커스 재적용을 방지
            NotificationCenter.default.post(name: Notification.Name("UserDismissedKeyboard"), object: nil)
            dismissKeyboard()
        }
        
        // ⭐️ 터치 대상이 텍스트 입력 필드이면 제스처 인식을 거부
        // → TextField/TextEditor 터치 시 dismissKeyboard()가 호출되지 않음
        // → 포커스가 정상적으로 유지됨
        func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer, shouldReceive touch: UITouch) -> Bool {
            // 터치된 뷰의 계층을 순회하여 텍스트 입력 뷰가 있는지 확인
            var currentView = touch.view
            while let view = currentView {
                if view is UITextField || view is UITextView {
                    return false // 텍스트 입력 필드 → 제스처 무시
                }
                currentView = view.superview
            }
            return true // 빈 영역 → 제스처 인식 → 키보드 닫기
        }
    }
}
#endif

// MARK: - Color Extensions
// 🎨 Geist Design System — Vercel-inspired Achromatic Palette
extension Color {
    // --- 배경 (Surface) ---
    static let bgMain = Color(hexString: "FFFFFF")       // Pure White (메인 배경)
    static let cardBg = Color(hexString: "FFFFFF")       // Pure White (카드 배경)
    static let softTan = Color(hexString: "F5F5F5")      // Gray 50 (선택/활성 배경)
    
    // --- 텍스트 ---
    static let primaryText = Color(hexString: "171717")   // Vercel Black (제목)
    static let secondaryText = Color(hexString: "4D4D4D") // Gray 600 (본문/보조)
    static let hintText = Color(hexString: "808080")      // Gray 400 (비활성/힌트)
    
    // --- 브랜드 ---
    static let accent = Color(hexString: "171717")        // Vercel Black (액센트/CTA)
    static let warmBorder = Color(hexString: "EBEBEB")    // Gray 100 (카드 테두리 — 폴백용)
    
    // --- Geist 워크플로 악센트 ---
    static let geistBlue = Color(hexString: "0A72EF")     // Develop Blue
    static let geistPink = Color(hexString: "DE1D8D")     // Preview Pink
    static let geistRed = Color(hexString: "FF5B4F")      // Ship Red
    static let geistLink = Color(hexString: "0072F5")     // Link Blue
    
    // --- Geist Neutral Scale ---
    static let gray50 = Color(hexString: "FAFAFA")
    static let gray100 = Color(hexString: "EBEBEB")
    static let gray400 = Color(hexString: "808080")
    static let gray500 = Color(hexString: "666666")
    static let gray600 = Color(hexString: "4D4D4D")
    static let gray900 = Color(hexString: "171717")
    
    // --- 감정 (Geist-compatible Muted Tones) ---
    static let mood1 = Color(hexString: "EF4444")  // Muted Red (화남)
    static let mood2 = Color(hexString: "6366F1")  // Indigo (우울)
    static let mood3 = Color(hexString: "9CA3AF")  // Cool Gray (보통)
    static let mood4 = Color(hexString: "10B981")  // Emerald (편안)
    static let mood5 = Color(hexString: "F59E0B")  // Amber (행복)
    
    init(hexString: String) {
        let hex = hexString.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (1, 1, 1, 0)
        }

        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue:  Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

// MARK: - 🎨 Geist Typography System
// Three weights: 400 (body/read), 500 (UI/interactive), 600 (headings/emphasis)
// No .rounded design — Geist uses geometric sans-serif
extension Font {
    static let journalTitle   = Font.system(size: 24, weight: .semibold, design: .default)
    static let journalHeading = Font.system(size: 18, weight: .semibold, design: .default)
    static let journalBody    = Font.system(size: 16, weight: .regular, design: .default)
    static let journalCaption = Font.system(size: 12, weight: .medium, design: .default)
    
    // Geist Display (큰 제목용)
    static let geistDisplay   = Font.system(size: 32, weight: .semibold, design: .default)
    static let geistTitle     = Font.system(size: 24, weight: .semibold, design: .default)
    static let geistSubtitle  = Font.system(size: 20, weight: .regular, design: .default)
    static let geistBody      = Font.system(size: 16, weight: .regular, design: .default)
    static let geistBodyMedium = Font.system(size: 16, weight: .medium, design: .default)
    static let geistButton    = Font.system(size: 14, weight: .medium, design: .default)
    static let geistCaption   = Font.system(size: 12, weight: .medium, design: .default)
    static let geistMono      = Font.system(size: 13, weight: .medium, design: .monospaced)
}

// MARK: - 🎨 Geist Card Modifier (Shadow-as-Border)
// Vercel의 시그니처: box-shadow로 border를 대체하는 multi-layer shadow stack
// Level 1: Ring border (rgba(0,0,0,0.08) 0px 0px 0px 1px)
// Level 2: Subtle elevation (rgba(0,0,0,0.04) 0px 2px 2px)
// Inner: #fafafa ring for subtle inner glow
struct WarmCardModifier: ViewModifier {
    var cornerRadius: CGFloat = 12
    
    func body(content: Content) -> some View {
        content
            .background(
                RoundedRectangle(cornerRadius: cornerRadius)
                    .fill(Color.cardBg)
            )
            // Shadow-as-border: Level 1 Ring
            .shadow(color: Color.black.opacity(0.08), radius: 0, x: 0, y: 0)
            // Shadow-as-border: border ring via overlay
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius)
                    .stroke(Color.black.opacity(0.08), lineWidth: 1)
            )
            // Level 2: Subtle elevation
            .shadow(color: Color.black.opacity(0.04), radius: 2, x: 0, y: 2)
            // Level 3: Ambient depth
            .shadow(color: Color.black.opacity(0.04), radius: 8, x: 0, y: -8)
    }
}

extension View {
    func warmCard(cornerRadius: CGFloat = 12) -> some View {
        self.modifier(WarmCardModifier(cornerRadius: cornerRadius))
    }
    
    /// Geist Level 1: 가벼운 ring border만 적용
    func geistRingBorder(cornerRadius: CGFloat = 8) -> some View {
        self
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius)
                    .stroke(Color.black.opacity(0.08), lineWidth: 1)
            )
    }
    
    /// Geist Level 2: Ring + 약간의 elevation
    func geistSubtleCard(cornerRadius: CGFloat = 8) -> some View {
        self
            .background(
                RoundedRectangle(cornerRadius: cornerRadius)
                    .fill(Color.white)
            )
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius)
                    .stroke(Color.black.opacity(0.08), lineWidth: 1)
            )
            .shadow(color: Color.black.opacity(0.04), radius: 2, x: 0, y: 2)
    }
    
    /// Geist Primary Button Style (Dark)
    func geistPrimaryButton() -> some View {
        self
            .font(.geistButton)
            .fontWeight(.medium)
            .foregroundColor(.white)
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(
                RoundedRectangle(cornerRadius: 6)
                    .fill(Color.gray900)
            )
    }
    
    /// Geist Secondary Button Style (White with ring border)
    func geistSecondaryButton() -> some View {
        self
            .font(.geistButton)
            .fontWeight(.medium)
            .foregroundColor(.gray900)
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(
                RoundedRectangle(cornerRadius: 6)
                    .fill(Color.white)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(Color(hexString: "EBEBEB"), lineWidth: 1)
            )
    }
    
    /// Geist Pill Badge
    func geistPillBadge(bgColor: Color = Color(hexString: "EBF5FF"), textColor: Color = Color(hexString: "0068D6")) -> some View {
        self
            .font(.system(size: 12, weight: .medium))
            .foregroundColor(textColor)
            .padding(.horizontal, 10)
            .padding(.vertical, 4)
            .background(
                Capsule()
                    .fill(bgColor)
            )
    }
}


// MARK: - Screenshot Prevention (Stability Fix)

// [Keyboard Fix] First Responder 가로채기 방지: 키보드를 절대 올리지 않는 TextField
private class NonFocusableTextField: UITextField {
    override var canBecomeFirstResponder: Bool { false }
}

class SecureWrapperView<Content: View>: UIView {
    private let textField = NonFocusableTextField()
    private var hostingController: UIHostingController<Content>?
    
    var isProtected: Bool = true {
        didSet {
            textField.isSecureTextEntry = isProtected
        }
    }
    
    init(content: Content, isProtected: Bool) {
        self.isProtected = isProtected
        super.init(frame: .zero)
        setupUI(content: content)
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    private func setupUI(content: Content) {
        // 1. TextField 설정
        // [Fix] 폰트 크기를 적절히 유지하여 레이아웃 왜곡 방지
        textField.isSecureTextEntry = isProtected
        textField.backgroundColor = .clear
        textField.textColor = .clear // 텍스트만 숨김
        textField.tintColor = .clear
        textField.isUserInteractionEnabled = true // 터치 관통 준비
        
        // 공백 텍스트 유지 (CanvasView 활성화용)
        textField.text = "                       " 
        
        // 2. HostingController
        let hc = UIHostingController(rootView: content)
        hc.view.backgroundColor = .clear
        hc.view.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        self.hostingController = hc
        
        addSubview(textField)
        
        // 3. 뷰 주입 (딜레이로 안정성 확보)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) { [weak self] in
            self?.setupSecureLayer()
        }
    }
    
    private func setupSecureLayer() {
        guard let hcView = hostingController?.view else { return }
        
        // 투명화 (흰 화면 방지)
        makeSubviewsClear(view: textField)
        
        // Secure Layer 찾기
        if let secureLayer = findSecureLayer(in: textField) {
            // [중요] 이미 추가되어 있다면 중복 추가 방지 (상위 계층 확인)
            if hcView.superview != secureLayer {
                secureLayer.addSubview(hcView)
            }
            // 초기 프레임 설정
            hcView.frame = secureLayer.bounds
        } else {
            // 못 찾으면 TextField 자체에
            if hcView.superview != textField {
                textField.addSubview(hcView)
            }
        }
    }
    
    // 재귀적으로 투명하게 만들기
    private func makeSubviewsClear(view: UIView) {
        view.backgroundColor = .clear
        view.isOpaque = false // 중요
        for subview in view.subviews {
            makeSubviewsClear(view: subview)
        }
    }
    
    // CanvasView 찾기
    private func findSecureLayer(in view: UIView) -> UIView? {
        let typeName = String(describing: type(of: view))
        if typeName.contains("CanvasView") || typeName.contains("TextLayout") {
            return view
        }
        for subview in view.subviews {
            if let found = findSecureLayer(in: subview) {
                return found
            }
        }
        return nil
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        
        // 1. TextField를 Wrapper에 맞춤
        textField.frame = self.bounds
        
        // 2. Secure Layer(Canvas)를 TextField에 맞춤 (안 그러면 작아짐)
        if let secureLayer = findSecureLayer(in: textField) {
            secureLayer.frame = textField.bounds
            
            // [Fix] 차트 왜곡 원인이었던 'forceExpandSubviews' 제거
            // 대신 SecureLayer 직계 자식인 HCView만 맞춤
            if let hcView = hostingController?.view {
                hcView.frame = secureLayer.bounds
            }
        }
    }
    
    func updateContent(_ content: Content) {
        hostingController?.rootView = content
        setNeedsLayout()
    }
    
    override func hitTest(_ point: CGPoint, with event: UIEvent?) -> UIView? {
        if let hcView = hostingController?.view {
             let convertedPoint = convert(point, to: hcView)
            if let hitView = hcView.hitTest(convertedPoint, with: event) {
                return hitView
            }
        }
        
        // TextField 영역 터치 무시 (키보드 방지)
        let result = super.hitTest(point, with: event)
        if result == textField || textField.subviews.contains(where: { $0 == result }) {
            return nil
        }
        return result
    }
}


struct ScreenshotPreventView<Content: View>: UIViewRepresentable {
    let content: Content
    let isProtected: Bool
    
    init(isProtected: Bool, content: Content) {
        self.isProtected = isProtected
        self.content = content
    }
    
    func makeUIView(context: Context) -> SecureWrapperView<Content> {
        return SecureWrapperView(content: content, isProtected: isProtected)
    }
    
    func updateUIView(_ uiView: SecureWrapperView<Content>, context: Context) {
        uiView.isProtected = isProtected
        uiView.updateContent(content)
    }
}

struct GlobalScreenshotPreventModifier: ViewModifier {
    @AppStorage("isScreenshotPreventionOn") private var isScreenshotPreventionOn: Bool = false
    
    func body(content: Content) -> some View {
        ScreenshotPreventView(isProtected: isScreenshotPreventionOn, content: content)
    }
}

extension View {
    func screenshotProtected() -> some View {
        self.modifier(GlobalScreenshotPreventModifier())
    }
}
