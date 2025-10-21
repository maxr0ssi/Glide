import AppKit

class PulseRingView: NSView {

    // MARK: - State
    enum State {
        case idle
        case active
        case scrollingUp
        case scrollingDown

        var ringColor: NSColor {
            switch self {
            case .idle:
                return NSColor.white.withAlphaComponent(0.2)
            case .active, .scrollingUp, .scrollingDown:
                return NSColor(red: 100/255, green: 200/255, blue: 255/255, alpha: 0.8)
            }
        }
    }

    private(set) var currentState: State = .idle {
        didSet {
            updateAppearance()
        }
    }

    // MARK: - Layers
    private let ringLayer = CAShapeLayer()
    private let upArrowLayer = CAShapeLayer()
    private let downArrowLayer = CAShapeLayer()
    private let closeButton = NSButton()

    // MARK: - Animations
    private var pulseAnimation: CABasicAnimation?
    private var scaleAnimation: CABasicAnimation?

    // MARK: - Properties
    private let ringDiameter: CGFloat = 24
    private let ringStrokeWidth: CGFloat = 3
    private let arrowSize: CGFloat = 8

    // MARK: - Initialization
    override init(frame: NSRect) {
        super.init(frame: frame)
        setupLayers()
        setupCloseButton()
        setupTracking()
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    // MARK: - Setup
    private func setupLayers() {
        wantsLayer = true
        layer?.backgroundColor = NSColor.clear.cgColor

        // Ring setup
        let center = CGPoint(x: bounds.width / 2, y: bounds.height / 2)
        let radius = ringDiameter / 2
        let ringPath = NSBezierPath(ovalIn: NSRect(
            x: center.x - radius,
            y: center.y - radius,
            width: ringDiameter,
            height: ringDiameter
        ))

        ringLayer.path = ringPath.cgPath
        ringLayer.fillColor = NSColor.clear.cgColor
        ringLayer.strokeColor = NSColor.white.withAlphaComponent(0.2).cgColor
        ringLayer.lineWidth = ringStrokeWidth
        ringLayer.lineCap = .round
        layer?.addSublayer(ringLayer)

        // Arrow setup
        setupArrowLayer(upArrowLayer, pointingUp: true)
        setupArrowLayer(downArrowLayer, pointingUp: false)

        layer?.addSublayer(upArrowLayer)
        layer?.addSublayer(downArrowLayer)

        // Initially hide arrows
        upArrowLayer.opacity = 0
        downArrowLayer.opacity = 0
    }

    private func setupArrowLayer(_ layer: CAShapeLayer, pointingUp: Bool) {
        let center = CGPoint(x: bounds.width / 2, y: bounds.height / 2)
        let arrowPath = NSBezierPath()

        if pointingUp {
            arrowPath.move(to: CGPoint(x: center.x, y: center.y - 4))
            arrowPath.line(to: CGPoint(x: center.x - 3, y: center.y + 2))
            arrowPath.line(to: CGPoint(x: center.x + 3, y: center.y + 2))
        } else {
            arrowPath.move(to: CGPoint(x: center.x, y: center.y + 4))
            arrowPath.line(to: CGPoint(x: center.x - 3, y: center.y - 2))
            arrowPath.line(to: CGPoint(x: center.x + 3, y: center.y - 2))
        }
        arrowPath.close()

        layer.path = arrowPath.cgPath
        layer.fillColor = NSColor(red: 100/255, green: 200/255, blue: 255/255, alpha: 0.9).cgColor
        layer.strokeColor = nil
    }

    private func setupCloseButton() {
        closeButton.title = "×"
        closeButton.isBordered = false
        closeButton.bezelStyle = .shadowlessSquare
        closeButton.font = .systemFont(ofSize: 10, weight: .medium)
        closeButton.target = self
        closeButton.action = #selector(closeButtonClicked)
        closeButton.alphaValue = 0

        addSubview(closeButton)
        closeButton.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            closeButton.topAnchor.constraint(equalTo: topAnchor, constant: 2),
            closeButton.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -2),
            closeButton.widthAnchor.constraint(equalToConstant: 12),
            closeButton.heightAnchor.constraint(equalToConstant: 12)
        ])
    }

    private func setupTracking() {
        let trackingArea = NSTrackingArea(
            rect: bounds,
            options: [.mouseEnteredAndExited, .activeAlways, .inVisibleRect],
            owner: self,
            userInfo: nil
        )
        addTrackingArea(trackingArea)
    }

    // MARK: - State Updates
    func setState(_ state: State) {
        currentState = state
    }

    private func updateAppearance() {
        // Update ring color
        CATransaction.begin()
        CATransaction.setAnimationDuration(0.3)
        ringLayer.strokeColor = currentState.ringColor.cgColor
        CATransaction.commit()

        // Handle animations
        switch currentState {
        case .idle:
            stopPulseAnimation()
            hideArrows()
        case .active:
            startPulseAnimation()
            hideArrows()
        case .scrollingUp:
            startPulseAnimation()
            showArrow(upArrowLayer)
            hideArrow(downArrowLayer)
        case .scrollingDown:
            startPulseAnimation()
            showArrow(downArrowLayer)
            hideArrow(upArrowLayer)
        }
    }

    // MARK: - Animations
    private func startPulseAnimation() {
        // Opacity pulse
        let opacityAnimation = CABasicAnimation(keyPath: "opacity")
        opacityAnimation.fromValue = 0.4
        opacityAnimation.toValue = 1.0
        opacityAnimation.duration = 2.0
        opacityAnimation.autoreverses = true
        opacityAnimation.repeatCount = .infinity
        opacityAnimation.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)

        // Scale pulse
        let scaleAnimation = CABasicAnimation(keyPath: "transform.scale")
        scaleAnimation.fromValue = 1.0
        scaleAnimation.toValue = 1.05
        scaleAnimation.duration = 2.0
        scaleAnimation.autoreverses = true
        scaleAnimation.repeatCount = .infinity
        scaleAnimation.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)

        ringLayer.add(opacityAnimation, forKey: "pulseOpacity")
        ringLayer.add(scaleAnimation, forKey: "pulseScale")
    }

    private func stopPulseAnimation() {
        ringLayer.removeAnimation(forKey: "pulseOpacity")
        ringLayer.removeAnimation(forKey: "pulseScale")
        ringLayer.opacity = 1.0
        ringLayer.transform = CATransform3DIdentity
    }

    private func showArrow(_ arrowLayer: CAShapeLayer) {
        CATransaction.begin()
        CATransaction.setAnimationDuration(0.15)
        arrowLayer.opacity = 1.0
        CATransaction.commit()
    }

    private func hideArrow(_ arrowLayer: CAShapeLayer) {
        CATransaction.begin()
        CATransaction.setAnimationDuration(0.3)
        arrowLayer.opacity = 0.0
        CATransaction.commit()
    }

    private func hideArrows() {
        hideArrow(upArrowLayer)
        hideArrow(downArrowLayer)
    }

    // MARK: - Mouse Tracking
    override func mouseEntered(with event: NSEvent) {
        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.2
            closeButton.animator().alphaValue = 1.0

            // Slightly brighten ring on hover
            let currentOpacity = ringLayer.opacity
            ringLayer.opacity = min(currentOpacity * 1.1, 1.0)
        }
    }

    override func mouseExited(with event: NSEvent) {
        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.2
            closeButton.animator().alphaValue = 0.0

            // Restore ring opacity
            ringLayer.opacity = 1.0
        }
    }

    // MARK: - Context Menu
    override func rightMouseDown(with event: NSEvent) {
        let menu = NSMenu()

        // Visibility submenu
        let visibilityItem = NSMenuItem(title: "Visibility", action: nil, keyEquivalent: "")
        let visibilityMenu = NSMenu()

        let alwaysShowItem = NSMenuItem(title: "Always Show", action: #selector(setVisibilityAlways), keyEquivalent: "")
        alwaysShowItem.state = .on
        visibilityMenu.addItem(alwaysShowItem)

        let autoHideItem = NSMenuItem(title: "Auto-hide (2s)", action: #selector(setVisibilityAutoHide), keyEquivalent: "")
        visibilityMenu.addItem(autoHideItem)

        let hiddenItem = NSMenuItem(title: "Hidden", action: #selector(setVisibilityHidden), keyEquivalent: "")
        visibilityMenu.addItem(hiddenItem)

        visibilityItem.submenu = visibilityMenu
        menu.addItem(visibilityItem)

        // Position submenu
        let positionItem = NSMenuItem(title: "Position", action: nil, keyEquivalent: "")
        let positionMenu = NSMenu()

        let topRightItem = NSMenuItem(title: "Top Right", action: #selector(setPositionTopRight), keyEquivalent: "")
        topRightItem.state = .on
        positionMenu.addItem(topRightItem)

        positionMenu.addItem(NSMenuItem(title: "Top Left", action: #selector(setPositionTopLeft), keyEquivalent: ""))
        positionMenu.addItem(NSMenuItem(title: "Bottom Right", action: #selector(setPositionBottomRight), keyEquivalent: ""))
        positionMenu.addItem(NSMenuItem(title: "Bottom Left", action: #selector(setPositionBottomLeft), keyEquivalent: ""))

        positionItem.submenu = positionMenu
        menu.addItem(positionItem)

        menu.addItem(NSMenuItem.separator())
        menu.addItem(NSMenuItem(title: "Quit Glide HUD", action: #selector(quitApp), keyEquivalent: ""))

        menu.popUp(positioning: nil, at: event.locationInWindow, in: self)
    }

    // MARK: - Actions
    @objc private func closeButtonClicked() {
        if let window = window as? PulseRingWindow {
            // Save hidden preference
            UserDefaults.standard.set("hidden", forKey: "glide.hud.visibility")
            window.hide()
        }
    }

    @objc private func setVisibilityAlways() {
        UserDefaults.standard.set("always", forKey: "glide.hud.visibility")
    }

    @objc private func setVisibilityAutoHide() {
        UserDefaults.standard.set("autohide", forKey: "glide.hud.visibility")
    }

    @objc private func setVisibilityHidden() {
        UserDefaults.standard.set("hidden", forKey: "glide.hud.visibility")
        if let window = window as? PulseRingWindow {
            window.hide()
        }
    }

    @objc private func setPositionTopRight() {
        if let window = window as? PulseRingWindow {
            window.setPosition(.topRight)
            UserDefaults.standard.set("top-right", forKey: "glide.hud.position")
        }
    }

    @objc private func setPositionTopLeft() {
        if let window = window as? PulseRingWindow {
            window.setPosition(.topLeft)
            UserDefaults.standard.set("top-left", forKey: "glide.hud.position")
        }
    }

    @objc private func setPositionBottomRight() {
        if let window = window as? PulseRingWindow {
            window.setPosition(.bottomRight)
            UserDefaults.standard.set("bottom-right", forKey: "glide.hud.position")
        }
    }

    @objc private func setPositionBottomLeft() {
        if let window = window as? PulseRingWindow {
            window.setPosition(.bottomLeft)
            UserDefaults.standard.set("bottom-left", forKey: "glide.hud.position")
        }
    }

    @objc private func quitApp() {
        NSApp.terminate(nil)
    }
}

// MARK: - NSBezierPath Extension
extension NSBezierPath {
    var cgPath: CGPath {
        let path = CGMutablePath()
        var points = [CGPoint](repeating: .zero, count: 3)

        for i in 0..<self.elementCount {
            let type = self.element(at: i, associatedPoints: &points)
            switch type {
            case .moveTo:
                path.move(to: points[0])
            case .lineTo:
                path.addLine(to: points[0])
            case .curveTo:
                path.addCurve(to: points[2], control1: points[0], control2: points[1])
            case .closePath:
                path.closeSubpath()
            default:
                break
            }
        }

        return path
    }
}
