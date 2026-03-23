// StableTextEditor.swift
// UIViewControllerRepresentable 기반 UITextView 래핑
//
// 방어 전략: "Refocus after steal"
//   SwiftUI 렌더 패스 중 resignFirstResponder가 호출되면
//   textViewDidEndEditing에서 즉시 becomeFirstResponder로 포커스를 되찾음
//   → 키보드 dismiss → 즉시 re-show (시각적으로 거의 seamless)

import SwiftUI

#if os(iOS)

// MARK: - UIResponder Current First Responder Extension
// 현재 어떤 뷰가 first responder인지 확인하기 위한 표준 iOS 유틸리티
extension UIResponder {
    private weak static var _currentFirstResponder: UIResponder?
    
    static var currentFirstResponder: UIResponder? {
        _currentFirstResponder = nil
        // sendAction으로 responder chain을 통해 현재 first responder를 찾음
        UIApplication.shared.sendAction(#selector(findFirstResponder(_:)), to: nil, from: nil, for: nil)
        return _currentFirstResponder
    }
    
    @objc private func findFirstResponder(_ sender: Any) {
        UIResponder._currentFirstResponder = self
    }
}


// MARK: - UIViewControllerRepresentable Wrapper
struct StableTextEditor: UIViewControllerRepresentable {
    @Binding var text: String
    var placeholder: String
    var minHeight: CGFloat = 100
    var isFocused: Binding<Bool>?
    
    func makeUIViewController(context: Context) -> StableTextEditorVC {
        let vc = StableTextEditorVC()
        vc.placeholder = placeholder
        vc.text = text
        vc.onTextChange = { newText in
            self.text = newText
        }
        vc.onFocusChange = { focused in
            self.isFocused?.wrappedValue = focused
        }
        return vc
    }
    
    func updateUIViewController(_ vc: StableTextEditorVC, context: Context) {
        if vc.textView.text != text {
            vc.textView.text = text
            vc.updatePlaceholder()
        }
    }
    
    func sizeThatFits(_ proposal: ProposedViewSize, uiViewController: StableTextEditorVC, context: Context) -> CGSize? {
        let width = proposal.width ?? UIScreen.main.bounds.width - 40
        let textSize = uiViewController.textView.sizeThatFits(CGSize(width: width, height: .greatestFiniteMagnitude))
        let height = max(min(textSize.height, 250), 80)
        return CGSize(width: width, height: height)
    }
}

// MARK: - UIViewController
class StableTextEditorVC: UIViewController, UITextViewDelegate {
    let textView = UITextView()
    let placeholderLabel = UILabel()
    
    var placeholder: String = ""
    var text: String = ""
    var onTextChange: ((String) -> Void)?
    var onFocusChange: ((Bool) -> Void)?
    
    /// true인 동안에는 endEditing 시 자동으로 re-focus
    /// 사용자가 명시적으로 키보드를 닫을 때만 false로 설정
    private var shouldMaintainFocus = false
    
    /// 사용자가 의도적으로 키보드를 닫았는지 (빈 영역 탭 등)
    private var userDismissedKeyboard = false
    
    private var keyboardDismissObserver: NSObjectProtocol?
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        view.backgroundColor = .clear
        
        // TextView 설정
        textView.delegate = self
        textView.font = .systemFont(ofSize: 16)
        textView.backgroundColor = .clear
        textView.textContainerInset = UIEdgeInsets(top: 12, left: 8, bottom: 12, right: 8)
        textView.isScrollEnabled = false
        textView.tintColor = .systemBlue
        textView.textColor = .label
        textView.text = text
        
        textView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(textView)
        
        // Placeholder
        placeholderLabel.text = placeholder
        placeholderLabel.font = .systemFont(ofSize: 16)
        placeholderLabel.textColor = .placeholderText
        placeholderLabel.numberOfLines = 0
        placeholderLabel.isHidden = !text.isEmpty
        
        placeholderLabel.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(placeholderLabel)
        
        NSLayoutConstraint.activate([
            textView.topAnchor.constraint(equalTo: view.topAnchor),
            textView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            textView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            textView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
            
            placeholderLabel.topAnchor.constraint(equalTo: view.topAnchor, constant: 12),
            placeholderLabel.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 13),
            placeholderLabel.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -13),
        ])
        
        // "사용자가 키보드를 닫음" 알림 수신
        keyboardDismissObserver = NotificationCenter.default.addObserver(
            forName: Notification.Name("UserDismissedKeyboard"),
            object: nil,
            queue: .main
        ) { [weak self] _ in
            self?.userDismissedKeyboard = true
            self?.shouldMaintainFocus = false
        }
    }
    
    deinit {
        if let observer = keyboardDismissObserver {
            NotificationCenter.default.removeObserver(observer)
        }
    }
    
    func updatePlaceholder() {
        placeholderLabel.isHidden = !textView.text.isEmpty
    }
    
    override var preferredContentSize: CGSize {
        get {
            let width = view.bounds.width > 0 ? view.bounds.width : UIScreen.main.bounds.width - 40
            let textSize = textView.sizeThatFits(CGSize(width: width, height: .greatestFiniteMagnitude))
            let height = max(min(textSize.height, 250), 80)
            return CGSize(width: width, height: height)
        }
        set { super.preferredContentSize = newValue }
    }
    
    // MARK: - UITextViewDelegate
    
    func textViewDidChange(_ textView: UITextView) {
        updatePlaceholder()
        onTextChange?(textView.text)
        view.invalidateIntrinsicContentSize()
    }
    
    func textViewDidBeginEditing(_ textView: UITextView) {
        shouldMaintainFocus = true
        userDismissedKeyboard = false
        onFocusChange?(true)
    }
    
    func textViewDidEndEditing(_ textView: UITextView) {
        if shouldMaintainFocus && !userDismissedKeyboard {
            // [Focus Fix] 다른 UITextView로 포커스가 이동한 경우에는 re-focus 금지
            // → 이것이 textarea간 포커스 쟁탈전(무한 루프)의 근본 원인이었음
            DispatchQueue.main.async { [weak self] in
                guard let self = self else { return }
                
                // 현재 first responder가 다른 UITextView이면 = 사용자가 다른 필드를 탭한 것
                // → 이 경우 re-focus하면 두 필드가 서로 becomeFirstResponder 무한 루프
                if let currentFirst = UIResponder.currentFirstResponder,
                   currentFirst is UITextView,
                   currentFirst !== self.textView {
                    // 다른 입력 필드로 정상 이동 → re-focus 하지 않음
                    self.shouldMaintainFocus = false
                    self.onFocusChange?(false)
                    return
                }
                
                // first responder가 없거나 텍스트 입력 필드가 아님
                // = SwiftUI 렌더 패스에 의한 강제 resign → 되찾기
                if !self.textView.isFirstResponder {
                    self.textView.becomeFirstResponder()
                }
            }
            return // onFocusChange(false) 호출하지 않음
        }
        
        // 사용자가 의도적으로 닫았거나, shouldMaintainFocus가 false인 경우
        shouldMaintainFocus = false
        userDismissedKeyboard = false
        onFocusChange?(false)
    }
}
#endif
