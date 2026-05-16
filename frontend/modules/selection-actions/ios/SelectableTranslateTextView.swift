import ExpoModulesCore
import UIKit

// A UITextView subclass that adds a "Translate" item to the OS text selection menu.
// Copy is preserved as the default OS action.
final class SelectableTranslateTextView: ExpoView {
  let onTranslate = EventDispatcher()

  fileprivate let textView = TranslateTextView()

  required init(appContext: AppContext? = nil) {
    super.init(appContext: appContext)

    textView.isEditable = false
    textView.isSelectable = true
    textView.isScrollEnabled = false
    textView.backgroundColor = .clear
    textView.textContainerInset = .zero
    textView.textContainer.lineFragmentPadding = 0
    textView.dataDetectorTypes = []
    textView.translatesAutoresizingMaskIntoConstraints = false
    textView.font = UIFont.systemFont(ofSize: 15)
    textView.translateHandler = { [weak self] selected, full, start, end in
      self?.onTranslate([
        "text": selected,
        "fullText": full,
        "start": start,
        "end": end,
      ])
    }
    addSubview(textView)

    NSLayoutConstraint.activate([
      textView.topAnchor.constraint(equalTo: topAnchor),
      textView.bottomAnchor.constraint(equalTo: bottomAnchor),
      textView.leadingAnchor.constraint(equalTo: leadingAnchor),
      textView.trailingAnchor.constraint(equalTo: trailingAnchor),
    ])
  }

  override func layoutSubviews() {
    super.layoutSubviews()
    guard bounds.width > 0 else { return }
    textView.textContainer.size = CGSize(width: bounds.width, height: .greatestFiniteMagnitude)
    textView.invalidateIntrinsicContentSize()
    invalidateIntrinsicContentSize()
  }

  override var intrinsicContentSize: CGSize {
    let fitting = textView.sizeThatFits(
      CGSize(width: bounds.width > 0 ? bounds.width : UIScreen.main.bounds.width * 0.85,
             height: .greatestFiniteMagnitude))
    let h = ceil(fitting.height)
    return CGSize(width: UIView.noIntrinsicMetric, height: h.isFinite ? h : 0)
  }

  func setText(_ value: String) {
    if textView.text != value {
      textView.text = value
    }
    textView.invalidateIntrinsicContentSize()
    invalidateIntrinsicContentSize()
  }

  func setFontSize(_ value: Double) {
    let currentSize = textView.font?.pointSize ?? 15
    if Double(currentSize) != value {
      textView.font = UIFont.systemFont(ofSize: CGFloat(value))
      textView.invalidateIntrinsicContentSize()
      invalidateIntrinsicContentSize()
    }
  }

  func setTextColorHex(_ hex: String?) {
    guard let hex = hex, let color = UIColor(hexString: hex) else { return }
    textView.textColor = color
  }

  func setTranslateLabel(_ label: String) {
    textView.translateLabel = label
  }
}

// UITextView that injects "Translate" into the edit menu.
private final class TranslateTextView: UITextView {
  var translateLabel: String = "Translate"
  var translateHandler: ((_ selected: String, _ full: String, _ start: Int, _ end: Int) -> Void)?

  override init(frame: CGRect, textContainer: NSTextContainer?) {
    super.init(frame: frame, textContainer: textContainer)
    NotificationCenter.default.addObserver(
      self,
      selector: #selector(menuWillShow(_:)),
      name: UIMenuController.willShowMenuNotification,
      object: nil
    )
  }

  required init?(coder: NSCoder) {
    fatalError("init(coder:) has not been implemented")
  }

  deinit {
    NotificationCenter.default.removeObserver(self)
  }

  @objc private func menuWillShow(_ notification: Notification) {
    let menu = UIMenuController.shared
    let translateItem = UIMenuItem(title: translateLabel, action: #selector(translateAction(_:)))
    let existing = menu.menuItems?.filter { $0.action != #selector(translateAction(_:)) } ?? []
    menu.menuItems = existing + [translateItem]
  }

  override func canPerformAction(_ action: Selector, withSender sender: Any?) -> Bool {
    if action == #selector(translateAction(_:)) {
      return selectedRange.length > 0
    }
    return super.canPerformAction(action, withSender: sender)
  }

  @objc func translateAction(_ sender: Any?) {
    guard selectedRange.length > 0, let attributed = attributedText else { return }
    let nsText = attributed.string as NSString
    let range = selectedRange
    guard range.location + range.length <= nsText.length else { return }
    let selected = nsText.substring(with: range)
    translateHandler?(selected, nsText as String, range.location, range.location + range.length)

    // Dismiss the menu and deselect after firing.
    selectedRange = NSRange(location: range.location + range.length, length: 0)
    UIMenuController.shared.hideMenu(from: self)
  }
}

private extension UIColor {
  convenience init?(hexString: String) {
    var hex = hexString.trimmingCharacters(in: .whitespacesAndNewlines)
    if hex.hasPrefix("#") {
      hex.removeFirst()
    }
    guard hex.count == 6 || hex.count == 8 else { return nil }
    var value: UInt64 = 0
    guard Scanner(string: hex).scanHexInt64(&value) else { return nil }
    let r, g, b, a: CGFloat
    if hex.count == 8 {
      r = CGFloat((value & 0xFF000000) >> 24) / 255
      g = CGFloat((value & 0x00FF0000) >> 16) / 255
      b = CGFloat((value & 0x0000FF00) >> 8) / 255
      a = CGFloat(value & 0x000000FF) / 255
    } else {
      r = CGFloat((value & 0xFF0000) >> 16) / 255
      g = CGFloat((value & 0x00FF00) >> 8) / 255
      b = CGFloat(value & 0x0000FF) / 255
      a = 1
    }
    self.init(red: r, green: g, blue: b, alpha: a)
  }
}
