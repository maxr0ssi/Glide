import AppKit

class HUDViewController: NSViewController {
    private var visualEffectView: NSVisualEffectView!
    private var containerView: PassThroughContainerView!
    private var currentWindowSize: HUDWindow.WindowSize = .minimized
    
    // UI Components
    private var upArrowView: ArrowView!
    private var downArrowView: ArrowView!
    private var speedBarView: SpeedBarView!
    private var expandButton: NSButton!
    private var statusLabel: NSTextField!
    
    // Expanded mode components
    private var cameraToggleButton: NSButton?
    private var cameraImageView: NSImageView?
    private var touchProofIndicator: TouchProofIndicatorView?
    
    // Effects
    private var particleEmitter: CAEmitterLayer?
    private var glowLayer: CALayer?
    
    override func loadView() {
        // Create visual effect view with proper frame
        let initialFrame = NSRect(x: 0, y: 0, width: 300, height: 150)
        visualEffectView = NSVisualEffectView(frame: initialFrame)
        visualEffectView.material = .sheet
        visualEffectView.blendingMode = .behindWindow
        visualEffectView.state = .active
        
        // Create container view with ice-white background
        containerView = PassThroughContainerView(frame: initialFrame)
        containerView.wantsLayer = true
        containerView.layer?.backgroundColor = NSColor(white: 1.0, alpha: 0.95).cgColor
        containerView.layer?.cornerRadius = 12
        containerView.layer?.masksToBounds = true
        
        // Add container to visual effect view
        visualEffectView.addSubview(containerView)
        
        // Set as main view
        self.view = visualEffectView
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // Set up constraints
        containerView.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            containerView.topAnchor.constraint(equalTo: view.topAnchor, constant: 8),
            containerView.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 8),
            containerView.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -8),
            containerView.bottomAnchor.constraint(equalTo: view.bottomAnchor, constant: -8)
        ])
        
        // Add frost border after constraints are set
        addFrostBorder()
        
        setupMinimizedUI()
        setupParticleEffects()
        
        // Listen for WebSocket events
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleScrollEvent(_:)),
            name: NSNotification.Name("GlideScrollEvent"),
            object: nil
        )
        
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleHideEvent),
            name: NSNotification.Name("GlideHideEvent"),
            object: nil
        )
        
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleCameraEvent(_:)),
            name: NSNotification.Name("GlideCameraEvent"),
            object: nil
        )
        
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleTouchProofEvent(_:)),
            name: NSNotification.Name("GlideTouchProofEvent"),
            object: nil
        )

        // Send initial mode to backend when WS connects (and on reconnects)
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleWebSocketConnected),
            name: NSNotification.Name("GlideWebSocketConnected"),
            object: nil
        )
    }
    
    private func setupMinimizedUI() {
        // Direction arrows
        upArrowView = ArrowView(direction: .up)
        downArrowView = ArrowView(direction: .down)
        
        // Speed bar
        speedBarView = SpeedBarView()
        
        // Expand button
        expandButton = NSButton()
        expandButton.bezelStyle = .regularSquare
        expandButton.title = currentWindowSize == .minimized ? "⤢" : "⤡"
        expandButton.font = .systemFont(ofSize: 16, weight: .medium)
        expandButton.isBordered = true
        expandButton.wantsLayer = true
        expandButton.layer?.backgroundColor = NSColor(white: 0.95, alpha: 0.8).cgColor
        expandButton.layer?.cornerRadius = 6
        expandButton.layer?.borderColor = NSColor(red: 0.70, green: 0.85, blue: 0.95, alpha: 0.8).cgColor
        expandButton.layer?.borderWidth = 1.5
        expandButton.contentTintColor = NSColor(red: 0.15, green: 0.20, blue: 0.22, alpha: 0.9)
        expandButton.alphaValue = 1.0  // Ensure button starts visible
        expandButton.target = self
        expandButton.action = #selector(toggleSize)
        
        // Add subviews
        for view in [upArrowView, downArrowView, speedBarView, expandButton].compactMap({ $0 }) {
            view.translatesAutoresizingMaskIntoConstraints = false
            containerView.addSubview(view)
        }

        // Allow clicks only on the expand button; pass through other mouse events
        containerView.passThroughAllowedView = expandButton
        
        // Layout
        NSLayoutConstraint.activate([
            // Arrows on the left
            upArrowView.leadingAnchor.constraint(equalTo: containerView.leadingAnchor, constant: 30),
            upArrowView.topAnchor.constraint(equalTo: containerView.topAnchor, constant: 25),
            upArrowView.widthAnchor.constraint(equalToConstant: 40),
            upArrowView.heightAnchor.constraint(equalToConstant: 40),
            
            downArrowView.leadingAnchor.constraint(equalTo: containerView.leadingAnchor, constant: 30),
            downArrowView.bottomAnchor.constraint(equalTo: containerView.bottomAnchor, constant: -25),
            downArrowView.widthAnchor.constraint(equalToConstant: 40),
            downArrowView.heightAnchor.constraint(equalToConstant: 40),
            
            // Speed bar in the center
            speedBarView.leadingAnchor.constraint(equalTo: upArrowView.trailingAnchor, constant: 30),
            speedBarView.centerYAnchor.constraint(equalTo: containerView.centerYAnchor),
            speedBarView.widthAnchor.constraint(equalToConstant: 150),
            speedBarView.heightAnchor.constraint(equalToConstant: 60),
            
            // Expand button on the right
            expandButton.trailingAnchor.constraint(equalTo: containerView.trailingAnchor, constant: -12),
            expandButton.topAnchor.constraint(equalTo: containerView.topAnchor, constant: 12),
            expandButton.widthAnchor.constraint(equalToConstant: 30),
            expandButton.heightAnchor.constraint(equalToConstant: 30)
        ])
        
        // Add hover tracking for expand button
        let trackingArea = NSTrackingArea(
            rect: expandButton.bounds,
            options: [.mouseEnteredAndExited, .activeAlways, .inVisibleRect],
            owner: self,
            userInfo: ["button": "expand"]
        )
        expandButton.addTrackingArea(trackingArea)
    }
    
    override func mouseEntered(with event: NSEvent) {
        if event.trackingArea?.userInfo?["button"] as? String == "expand" {
            NSAnimationContext.runAnimationGroup { context in
                context.duration = 0.2
                expandButton.animator().alphaValue = 1.0
                expandButton.layer?.backgroundColor = NSColor(white: 1.0, alpha: 0.9).cgColor
            }
        }
    }
    
    override func mouseExited(with event: NSEvent) {
        if event.trackingArea?.userInfo?["button"] as? String == "expand" {
            NSAnimationContext.runAnimationGroup { context in
                context.duration = 0.2
                expandButton.animator().alphaValue = 0.9  // Keep it mostly visible
                expandButton.layer?.backgroundColor = NSColor(white: 0.95, alpha: 0.8).cgColor
            }
        }
    }
    
    private func addFrostBorder() {
        let borderLayer = CAShapeLayer()
        borderLayer.fillColor = NSColor.clear.cgColor
        borderLayer.strokeColor = NSColor(red: 0.89, green: 0.95, blue: 0.99, alpha: 0.6).cgColor
        borderLayer.lineWidth = 2
        borderLayer.lineDashPattern = [4, 2]
        
        containerView.layer?.addSublayer(borderLayer)
        
        // Update path when view resizes
        containerView.postsFrameChangedNotifications = true
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(updateFrostBorder),
            name: NSView.frameDidChangeNotification,
            object: containerView
        )
    }
    
    @objc private func updateFrostBorder() {
        guard let borderLayer = containerView.layer?.sublayers?.first(where: { $0 is CAShapeLayer }) as? CAShapeLayer else { return }
        let path = NSBezierPath(roundedRect: containerView.bounds.insetBy(dx: 1, dy: 1), xRadius: 11, yRadius: 11)
        let cgPath = CGMutablePath()
        var points = [CGPoint](repeating: .zero, count: 3)
        for i in 0..<path.elementCount {
            let type = path.element(at: i, associatedPoints: &points)
            switch type {
            case .moveTo:
                cgPath.move(to: points[0])
            case .lineTo:
                cgPath.addLine(to: points[0])
            case .curveTo:
                cgPath.addCurve(to: points[2], control1: points[0], control2: points[1])
            case .closePath:
                cgPath.closeSubpath()
            case .cubicCurveTo:
                cgPath.addCurve(to: points[2], control1: points[0], control2: points[1])
            case .quadraticCurveTo:
                cgPath.addQuadCurve(to: points[1], control: points[0])
            @unknown default:
                break
            }
        }
        borderLayer.path = cgPath
    }
    
    private func setupParticleEffects() {
        particleEmitter = CAEmitterLayer()
        particleEmitter?.emitterPosition = CGPoint(x: containerView.bounds.width / 2, y: containerView.bounds.height)
        particleEmitter?.emitterSize = CGSize(width: containerView.bounds.width, height: 1)
        particleEmitter?.emitterShape = .line
        particleEmitter?.renderMode = .additive
        
        let cell = CAEmitterCell()
        cell.contents = createIceParticleImage()
        cell.birthRate = 0
        cell.lifetime = 3.0
        cell.velocity = -20
        cell.velocityRange = 10
        cell.emissionRange = .pi / 6
        cell.scale = 0.3
        cell.scaleRange = 0.2
        cell.alphaSpeed = -0.3
        
        particleEmitter?.emitterCells = [cell]
        containerView.layer?.addSublayer(particleEmitter!)
    }
    
    private func createIceParticleImage() -> CGImage? {
        let size = CGSize(width: 8, height: 8)
        let image = NSImage(size: size, flipped: false) { rect in
            NSColor(red: 0.89, green: 0.95, blue: 0.99, alpha: 1.0).setFill()
            NSBezierPath(ovalIn: rect).fill()
            return true
        }
        return image.cgImage(forProposedRect: nil, context: nil, hints: nil)
    }
    
    @objc private func handleScrollEvent(_ notification: Notification) {
        guard let userInfo = notification.userInfo,
              let vy = userInfo["vy"] as? Double,
              let speed = userInfo["speed"] as? Double else { return }
        
        DispatchQueue.main.async { [weak self] in
            self?.updateScrollUI(velocity: vy, speed: speed)
            self?.startParticleAnimation()
        }
    }
    
    private func updateScrollUI(velocity: Double, speed: Double) {
        // Update arrows
        if velocity > 0 {
            upArrowView.setActive(true)
            downArrowView.setActive(false)
        } else if velocity < 0 {
            upArrowView.setActive(false)
            downArrowView.setActive(true)
        }
        
        // Update speed bar
        speedBarView.setSpeed(CGFloat(speed))
    }
    
    private func startParticleAnimation() {
        guard let cell = particleEmitter?.emitterCells?.first else { return }
        
        CATransaction.begin()
        CATransaction.setDisableActions(true)
        cell.birthRate = 5
        CATransaction.commit()
        
        // Stop after a short time
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in
            guard let cell = self?.particleEmitter?.emitterCells?.first else { return }
            CATransaction.begin()
            CATransaction.setDisableActions(true)
            cell.birthRate = 0
            CATransaction.commit()
        }
    }
    
    @objc private func handleHideEvent() {
        // Reset UI
        DispatchQueue.main.async { [weak self] in
            self?.upArrowView.setActive(false)
            self?.downArrowView.setActive(false)
            self?.speedBarView.setSpeed(0)
        }
    }
    
    @objc private func toggleSize() {
        if let window = view.window as? HUDWindow {
            window.toggleSize()
        }
    }
    
    @objc private func expandButtonClicked() {
        toggleSize()
    }
    
    func windowSizeChanged(to newSize: HUDWindow.WindowSize) {
        currentWindowSize = newSize
        
        // Update expand button icon
        expandButton.title = newSize == .minimized ? "⤢" : "⤡"
        
        if newSize == .expanded {
            setupExpandedUI()
            // Notify backend about mode change
            if let appDelegate = NSApp.delegate as? AppDelegate {
                appDelegate.webSocketClient?.sendModeChange(expanded: true)
                let enabled = (cameraToggleButton?.state == .on)
                appDelegate.webSocketClient?.sendCameraEnabled(enabled: enabled)
            }
        } else {
            teardownExpandedUI()
            // Notify backend about mode change
            if let appDelegate = NSApp.delegate as? AppDelegate {
                appDelegate.webSocketClient?.sendModeChange(expanded: false)
                appDelegate.webSocketClient?.sendCameraEnabled(enabled: false)
            }
        }
    }
    
    private func setupExpandedUI() {
        // Camera preview
        cameraImageView = NSImageView(frame: NSRect.zero)
        cameraImageView?.imageScaling = .scaleProportionallyUpOrDown
        cameraImageView?.wantsLayer = true
        cameraImageView?.layer?.cornerRadius = 8
        cameraImageView?.layer?.masksToBounds = true
        cameraImageView?.layer?.borderColor = NSColor(red: 0.89, green: 0.95, blue: 0.99, alpha: 0.4).cgColor
        cameraImageView?.layer?.borderWidth = 1
        cameraImageView?.translatesAutoresizingMaskIntoConstraints = false
        
        // TouchProof indicator
        touchProofIndicator = TouchProofIndicatorView(frame: NSRect.zero)
        touchProofIndicator?.translatesAutoresizingMaskIntoConstraints = false
        
        if let cameraImageView = cameraImageView,
           let touchProofIndicator = touchProofIndicator {
            containerView.addSubview(cameraImageView)
            containerView.addSubview(touchProofIndicator)
            if cameraToggleButton == nil {
                cameraToggleButton = NSButton(checkboxWithTitle: "Camera Streaming", target: self, action: #selector(toggleCameraStreaming))
                cameraToggleButton?.state = .on
                cameraToggleButton?.translatesAutoresizingMaskIntoConstraints = false
                containerView.addSubview(cameraToggleButton!)
                containerView.allowedViews.append(cameraToggleButton!)
            }
            
            NSLayoutConstraint.activate([
                // Camera takes most of the space
                cameraImageView.topAnchor.constraint(equalTo: speedBarView.bottomAnchor, constant: 20),
                cameraImageView.leadingAnchor.constraint(equalTo: containerView.leadingAnchor, constant: 20),
                cameraImageView.trailingAnchor.constraint(equalTo: containerView.trailingAnchor, constant: -20),
                cameraImageView.bottomAnchor.constraint(equalTo: touchProofIndicator.topAnchor, constant: -10),
                
                // TouchProof at bottom
                touchProofIndicator.leadingAnchor.constraint(equalTo: containerView.leadingAnchor, constant: 20),
                touchProofIndicator.trailingAnchor.constraint(equalTo: containerView.trailingAnchor, constant: -20),
                touchProofIndicator.bottomAnchor.constraint(equalTo: containerView.bottomAnchor, constant: -20),
                touchProofIndicator.heightAnchor.constraint(equalToConstant: 40)
            ])

            if let cameraToggleButton = cameraToggleButton {
                NSLayoutConstraint.activate([
                    cameraToggleButton.trailingAnchor.constraint(equalTo: containerView.trailingAnchor, constant: -16),
                    cameraToggleButton.topAnchor.constraint(equalTo: containerView.topAnchor, constant: 12)
                ])
            }
        }
    }
    
    private func teardownExpandedUI() {
        cameraImageView?.removeFromSuperview()
        cameraImageView = nil
        cameraToggleButton?.removeFromSuperview()
        cameraToggleButton = nil
        touchProofIndicator?.removeFromSuperview()
        touchProofIndicator = nil
    }
    
    @objc private func handleCameraEvent(_ notification: Notification) {
        guard currentWindowSize == .expanded,
              let userInfo = notification.userInfo,
              let frameData = userInfo["frame"] as? Data,
              let image = NSImage(data: frameData) else { return }
        
        DispatchQueue.main.async { [weak self] in
            self?.cameraImageView?.image = image
        }
    }
    
    @objc private func handleTouchProofEvent(_ notification: Notification) {
        guard let userInfo = notification.userInfo,
              let active = userInfo["active"] as? Bool,
              let hands = userInfo["hands"] as? Int else { return }
        
        DispatchQueue.main.async { [weak self] in
            self?.touchProofIndicator?.updateState(active: active, handsCount: hands)
            
            // Add glow effect when active
            if active {
                self?.addTouchProofGlow()
            } else {
                self?.removeTouchProofGlow()
            }
        }
    }
    
    private func addTouchProofGlow() {
        guard glowLayer == nil else { return }
        
        glowLayer = CALayer()
        glowLayer?.backgroundColor = NSColor(red: 0.70, green: 0.90, blue: 0.98, alpha: 0.3).cgColor
        glowLayer?.cornerRadius = 12
        glowLayer?.frame = containerView.bounds.insetBy(dx: -5, dy: -5)
        
        containerView.layer?.insertSublayer(glowLayer!, at: 0)
        
        // Pulse animation
        let animation = CABasicAnimation(keyPath: "opacity")
        animation.fromValue = 0.3
        animation.toValue = 0.6
        animation.duration = 1.0
        animation.autoreverses = true
        animation.repeatCount = .infinity
        glowLayer?.add(animation, forKey: "pulse")
    }
    
    private func removeTouchProofGlow() {
        glowLayer?.removeFromSuperlayer()
        glowLayer = nil
    }

    @objc private func toggleCameraStreaming(_ sender: NSButton) {
        let enabled = (sender.state == .on)
        if let appDelegate = NSApp.delegate as? AppDelegate {
            appDelegate.webSocketClient?.sendCameraEnabled(enabled: enabled)
        }
    }

    @objc private func handleWebSocketConnected() {
        // Inform backend of current mode upon (re)connection
        let isExpanded = (currentWindowSize == .expanded)
        if let appDelegate = NSApp.delegate as? AppDelegate {
            appDelegate.webSocketClient?.sendModeChange(expanded: isExpanded)
            let enabled = isExpanded && (cameraToggleButton?.state == .on)
            appDelegate.webSocketClient?.sendCameraEnabled(enabled: enabled)
        }
    }
}

// MARK: - Custom Views

class ArrowView: NSView {
    enum Direction {
        case up, down
    }
    
    private let direction: Direction
    private var isActive = false
    private let arrowLayer = CAShapeLayer()
    
    init(direction: Direction) {
        self.direction = direction
        super.init(frame: .zero)
        setup()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    private func setup() {
        wantsLayer = true
        layer?.addSublayer(arrowLayer)
        
        arrowLayer.fillColor = NSColor(red: 0.15, green: 0.20, blue: 0.22, alpha: 0.3).cgColor
        arrowLayer.strokeColor = NSColor(red: 0.15, green: 0.20, blue: 0.22, alpha: 0.5).cgColor
        arrowLayer.lineWidth = 1.5
    }
    
    override func layout() {
        super.layout()
        
        let path = NSBezierPath()
        let center = CGPoint(x: bounds.width / 2, y: bounds.height / 2)
        
        if direction == .up {
            path.move(to: CGPoint(x: center.x, y: center.y - 12))
            path.line(to: CGPoint(x: center.x - 10, y: center.y + 6))
            path.line(to: CGPoint(x: center.x + 10, y: center.y + 6))
            path.close()
        } else {
            path.move(to: CGPoint(x: center.x, y: center.y + 12))
            path.line(to: CGPoint(x: center.x - 10, y: center.y - 6))
            path.line(to: CGPoint(x: center.x + 10, y: center.y - 6))
            path.close()
        }
        
        let cgPath = CGMutablePath()
        var points = [CGPoint](repeating: .zero, count: 3)
        for i in 0..<path.elementCount {
            let type = path.element(at: i, associatedPoints: &points)
            switch type {
            case .moveTo:
                cgPath.move(to: points[0])
            case .lineTo:
                cgPath.addLine(to: points[0])
            case .closePath:
                cgPath.closeSubpath()
            default:
                break
            }
        }
        arrowLayer.path = cgPath
    }
    
    func setActive(_ active: Bool) {
        isActive = active
        
        if active {
            arrowLayer.fillColor = NSColor(red: 0.70, green: 0.90, blue: 0.98, alpha: 0.8).cgColor
            
            let pulse = CABasicAnimation(keyPath: "opacity")
            pulse.fromValue = 0.8
            pulse.toValue = 1.0
            pulse.duration = 0.3
            pulse.autoreverses = true
            pulse.repeatCount = .infinity
            arrowLayer.add(pulse, forKey: "pulse")
        } else {
            arrowLayer.fillColor = NSColor(red: 0.15, green: 0.20, blue: 0.22, alpha: 0.3).cgColor
            arrowLayer.removeAnimation(forKey: "pulse")
        }
    }
}

class SpeedBarView: NSView {
    private var speed: CGFloat = 0
    private let barLayers: [CALayer] = (0..<5).map { _ in CALayer() }
    
    override init(frame: NSRect) {
        super.init(frame: frame)
        setup()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    private func setup() {
        wantsLayer = true
        
        barLayers.forEach { bar in
            bar.backgroundColor = NSColor(red: 0.15, green: 0.20, blue: 0.22, alpha: 0.2).cgColor
            bar.cornerRadius = 2
            layer?.addSublayer(bar)
        }
    }
    
    override func layout() {
        super.layout()
        
        let barWidth = bounds.width / 6
        let barSpacing = barWidth / 5
        
        for (index, bar) in barLayers.enumerated() {
            let height = bounds.height * (0.3 + CGFloat(index) * 0.15)
            let x = CGFloat(index) * (barWidth + barSpacing)
            let y = (bounds.height - height) / 2
            bar.frame = CGRect(x: x, y: y, width: barWidth, height: height)
        }
    }
    
    func setSpeed(_ newSpeed: CGFloat) {
        speed = max(0, min(1, newSpeed))
        
        let activeBars = Int(speed * 5)
        
        for (index, bar) in barLayers.enumerated() {
            if index < activeBars {
                bar.backgroundColor = NSColor(red: 0.70, green: 0.90, blue: 0.98, alpha: 0.9).cgColor
            } else {
                bar.backgroundColor = NSColor(red: 0.15, green: 0.20, blue: 0.22, alpha: 0.2).cgColor
            }
        }
    }
}

class TouchProofIndicatorView: NSView {
    private var isActive = false
    private var handsCount = 0
    private let statusLabel = NSTextField()
    private let handsIcon = CAShapeLayer()
    
    override init(frame: NSRect) {
        super.init(frame: frame)
        setup()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    private func setup() {
        wantsLayer = true
        layer?.backgroundColor = NSColor(white: 1.0, alpha: 0.1).cgColor
        layer?.cornerRadius = 20
        
        // Status label
        statusLabel.isEditable = false
        statusLabel.isBordered = false
        statusLabel.backgroundColor = .clear
        statusLabel.textColor = NSColor(red: 0.15, green: 0.20, blue: 0.22, alpha: 0.8)
        statusLabel.font = .systemFont(ofSize: 14, weight: .medium)
        statusLabel.alignment = .center
        statusLabel.stringValue = "TouchProof Off"
        statusLabel.translatesAutoresizingMaskIntoConstraints = false
        
        addSubview(statusLabel)
        
        // Hands icon
        layer?.addSublayer(handsIcon)
        handsIcon.fillColor = NSColor(red: 0.15, green: 0.20, blue: 0.22, alpha: 0.5).cgColor
        
        NSLayoutConstraint.activate([
            statusLabel.centerXAnchor.constraint(equalTo: centerXAnchor),
            statusLabel.centerYAnchor.constraint(equalTo: centerYAnchor)
        ])
    }
    
    override func layout() {
        super.layout()
        
        // Update hands icon position
        let iconSize: CGFloat = 24
        handsIcon.frame = CGRect(x: 10, y: (bounds.height - iconSize) / 2, width: iconSize, height: iconSize)
        updateHandsIcon()
    }
    
    func updateState(active: Bool, handsCount: Int) {
        self.isActive = active
        self.handsCount = handsCount
        
        if active {
            statusLabel.stringValue = "TouchProof Active (\(handsCount) hand\(handsCount == 1 ? "" : "s"))"
            statusLabel.textColor = NSColor(red: 0.70, green: 0.90, blue: 0.98, alpha: 1.0)
            layer?.backgroundColor = NSColor(red: 0.70, green: 0.90, blue: 0.98, alpha: 0.2).cgColor
            handsIcon.fillColor = NSColor(red: 0.70, green: 0.90, blue: 0.98, alpha: 0.8).cgColor
        } else {
            statusLabel.stringValue = "TouchProof Off"
            statusLabel.textColor = NSColor(red: 0.15, green: 0.20, blue: 0.22, alpha: 0.8)
            layer?.backgroundColor = NSColor(white: 1.0, alpha: 0.1).cgColor
            handsIcon.fillColor = NSColor(red: 0.15, green: 0.20, blue: 0.22, alpha: 0.5).cgColor
        }
        
        updateHandsIcon()
    }
    
    private func updateHandsIcon() {
        let path = NSBezierPath()
        let rect = handsIcon.bounds
        
        // Simple hand icon
        let centerX = rect.width / 2
        let centerY = rect.height / 2
        
        // Palm
        path.appendOval(in: NSRect(x: centerX - 6, y: centerY - 4, width: 12, height: 8))
        
        // Fingers (simplified)
        for i in 0..<3 {
            let x = centerX - 4 + CGFloat(i) * 4
            path.appendRect(NSRect(x: x - 1, y: centerY + 3, width: 2, height: 5))
        }
        
        // Convert to CGPath
        let cgPath = CGMutablePath()
        var points = [CGPoint](repeating: .zero, count: 3)
        for i in 0..<path.elementCount {
            let type = path.element(at: i, associatedPoints: &points)
            switch type {
            case .moveTo:
                cgPath.move(to: points[0])
            case .lineTo:
                cgPath.addLine(to: points[0])
            case .curveTo:
                cgPath.addCurve(to: points[2], control1: points[0], control2: points[1])
            case .closePath:
                cgPath.closeSubpath()
            case .cubicCurveTo:
                cgPath.addCurve(to: points[2], control1: points[0], control2: points[1])
            case .quadraticCurveTo:
                cgPath.addQuadCurve(to: points[1], control: points[0])
            @unknown default:
                break
            }
        }
        
        handsIcon.path = cgPath
        
        // Animate if active
        if isActive {
            let pulse = CABasicAnimation(keyPath: "transform.scale")
            pulse.fromValue = 1.0
            pulse.toValue = 1.1
            pulse.duration = 0.5
            pulse.autoreverses = true
            pulse.repeatCount = .infinity
            handsIcon.add(pulse, forKey: "pulse")
        } else {
            handsIcon.removeAnimation(forKey: "pulse")
        }
    }
}

// MARK: - Pass-through container view to avoid intercepting scroll/wheel events
class PassThroughContainerView: NSView {
    weak var passThroughAllowedView: NSView?
    var allowedViews: [NSView] = []

    override func hitTest(_ point: NSPoint) -> NSView? {
        // Primary allowed view (e.g., expand button)
        if let allowed = passThroughAllowedView {
            let localPoint = convert(point, to: allowed)
            if !allowed.isHidden && allowed.bounds.contains(localPoint) {
                // Return the allowed view directly if point is inside bounds
                return allowed
            }
        }
        // Additional allowed views (e.g., camera toggle)
        for view in allowedViews {
            let localPoint = convert(point, to: view)
            if !view.isHidden && view.bounds.contains(localPoint) {
                // Return the view directly if point is inside bounds
                return view
            }
        }
        // Pass through to windows underneath
        return nil
    }
}