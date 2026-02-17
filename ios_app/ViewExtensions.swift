
import SwiftUI
import UIKit

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
}

// MARK: - Color Extensions
// (Color Extension 코드는 유지)
extension Color {
    static let bgMain = Color(hexString: "F7F8FA")
    static let cardBg = Color.white
    static let primaryText = Color(hexString: "1D1D1F")
    static let secondaryText = Color(hexString: "86868B")
    static let accent = Color(hexString: "0071E3")
    static let mood1 = Color(hexString: "FF6B6B")
    static let mood2 = Color(hexString: "4D96FF")
    static let mood3 = Color(hexString: "A0A0A0")
    static let mood4 = Color(hexString: "6BCB77")
    static let mood5 = Color(hexString: "FFD93D")
    
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


// MARK: - Screenshot Prevention (Stability Fix)

class SecureWrapperView<Content: View>: UIView {
    private let textField = UITextField()
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

extension View {
    func screenshotProtected(isProtected: Bool = true) -> some View {
        ScreenshotPreventView(isProtected: isProtected, content: self)
    }
}
