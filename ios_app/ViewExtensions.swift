import SwiftUI


extension View {
    // iOS 17+ 호환성 래퍼: Deprecation 경고 방지 및 버전 대응
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
extension Color {
    // Design System Colors
    static let bgMain = Color(hex: "F7F8FA")
    static let cardBg = Color.white
    static let primaryText = Color(hex: "1D1D1F")
    static let secondaryText = Color(hex: "86868B")
    static let accent = Color(hex: "0071E3") // Apple Blue
    
    // Mood Colors
    static let mood1 = Color(hex: "FF6B6B") // Angry
    static let mood2 = Color(hex: "4D96FF") // Sad
    static let mood3 = Color(hex: "A0A0A0") // Neutral
    static let mood4 = Color(hex: "6BCB77") // Calm
    static let mood5 = Color(hex: "FFD93D") // Happy
    
    init(hex: String) {
        let scanner = Scanner(string: hex)
        _ = scanner.scanString("#")
        var rgb: UInt64 = 0
        scanner.scanHexInt64(&rgb)
        let r = Double((rgb >> 16) & 0xFF) / 255.0
        let g = Double((rgb >> 8) & 0xFF) / 255.0
        let b = Double(rgb & 0xFF) / 255.0
        self.init(red: r, green: g, blue: b)
    }
}
