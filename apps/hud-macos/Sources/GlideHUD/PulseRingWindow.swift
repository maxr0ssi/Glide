import AppKit

class PulseRingWindow: NSPanel {

    init() {
        // Get screen bounds
        let screen = NSScreen.main ?? NSScreen.screens[0]
        let screenFrame = screen.frame

        // Window size and position (top-right corner)
        let windowSize = CGSize(width: 32, height: 32)
        let windowOrigin = CGPoint(
            x: screenFrame.maxX - windowSize.width - 20,  // 20px from right
            y: screenFrame.maxY - windowSize.height - 20  // 20px from top
        )
        let windowFrame = NSRect(origin: windowOrigin, size: windowSize)

        super.init(
            contentRect: windowFrame,
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )

        // Configure window
        isOpaque = false
        backgroundColor = .clear
        level = .floating
        collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .ignoresCycle]
        isMovableByWindowBackground = false
        hasShadow = false

        // Enable animations
        animationBehavior = .none  // We'll handle our own animations

        // Set up content view
        let pulseRingView = PulseRingView(frame: NSRect(origin: .zero, size: windowSize))
        contentView = pulseRingView
    }

    // MARK: - Position Management

    enum Position {
        case topRight
        case topLeft
        case bottomRight
        case bottomLeft

        func origin(for screenFrame: NSRect, windowSize: CGSize) -> CGPoint {
            let margin: CGFloat = 20

            switch self {
            case .topRight:
                return CGPoint(
                    x: screenFrame.maxX - windowSize.width - margin,
                    y: screenFrame.maxY - windowSize.height - margin
                )
            case .topLeft:
                return CGPoint(
                    x: screenFrame.minX + margin,
                    y: screenFrame.maxY - windowSize.height - margin
                )
            case .bottomRight:
                return CGPoint(
                    x: screenFrame.maxX - windowSize.width - margin,
                    y: screenFrame.minY + margin
                )
            case .bottomLeft:
                return CGPoint(
                    x: screenFrame.minX + margin,
                    y: screenFrame.minY + margin
                )
            }
        }
    }

    func setPosition(_ position: Position) {
        guard let screen = NSScreen.main ?? NSScreen.screens.first else { return }
        let origin = position.origin(for: screen.frame, windowSize: frame.size)
        setFrameOrigin(origin)
    }

    // MARK: - Visibility

    func show() {
        alphaValue = 0
        makeKeyAndOrderFront(nil)

        NSAnimationContext.runAnimationGroup { context in
            context.duration = 0.3
            context.timingFunction = CAMediaTimingFunction(name: .easeOut)
            animator().alphaValue = 1.0
        }
    }

    func hide() {
        NSAnimationContext.runAnimationGroup({ context in
            context.duration = 0.5
            context.timingFunction = CAMediaTimingFunction(name: .easeIn)
            animator().alphaValue = 0.0
        }, completionHandler: { [weak self] in
            self?.orderOut(nil)
        })
    }
}
