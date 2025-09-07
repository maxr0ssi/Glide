import AppKit

class HUDWindow: NSPanel {
    enum WindowSize {
        case minimized
        case expanded

        var size: NSSize {
            switch self {
            case .minimized: return NSSize(width: 300, height: 150)
            case .expanded: return NSSize(width: 500, height: 400)
            }
        }
    }

    private var currentSize: WindowSize = .minimized
    private var autoHideTimer: Timer?

    init() {
        // Calculate initial window position (center of screen)
        let screenFrame = NSScreen.main?.frame ?? NSRect.zero
        let initialSize = currentSize.size

        let windowFrame = NSRect(
            x: screenFrame.midX - initialSize.width / 2,
            y: screenFrame.midY - initialSize.height / 2,
            width: initialSize.width,
            height: initialSize.height
        )

        super.init(
            contentRect: windowFrame,
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )

        // Configure window for liquid ice aesthetic
        isOpaque = false
        backgroundColor = NSColor.clear
        level = .floating
        collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .ignoresCycle]
        isMovableByWindowBackground = true

        // Enable animations
        animationBehavior = .utilityWindow

        // Set up content view controller
        contentViewController = HUDViewController()

        // Configure for ice aesthetic
        contentView?.wantsLayer = true
        contentView?.layer?.cornerRadius = 12
        contentView?.layer?.masksToBounds = true

        // Ensure the window respects its size
        self.setContentSize(initialSize)
    }

    func toggleVisibility() {
        if isVisible {
            fadeOut()
        } else {
            fadeIn()
        }
    }

    func showActivity() {
        fadeIn()
        // Only auto-hide in minimized mode
        if currentSize == .minimized {
            resetAutoHideTimer()
        }
    }

    private func fadeIn() {
        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }

            if !self.isVisible {
                self.alphaValue = 0
                self.makeKeyAndOrderFront(nil)
                self.center()

            }

            NSAnimationContext.runAnimationGroup({ context in
                context.duration = 0.2
                context.timingFunction = CAMediaTimingFunction(name: .easeOut)
                self.animator().alphaValue = 1.0

                // Subtle scale animation
                let transform = CATransform3DMakeScale(0.95, 0.95, 1.0)
                self.contentView?.layer?.transform = transform
                self.contentView?.animator().layer?.transform = CATransform3DIdentity
            }, completionHandler: nil)

            // Only reset auto-hide timer in minimized mode
            if self.currentSize == .minimized {
                self.resetAutoHideTimer()
            }
        }
    }

    private func fadeOut() {
        NSAnimationContext.runAnimationGroup({ context in
            context.duration = 0.5
            context.timingFunction = CAMediaTimingFunction(name: .easeIn)
            animator().alphaValue = 0.0
        }, completionHandler: { [weak self] in
            self?.orderOut(nil)
        })
    }

    private func resetAutoHideTimer() {
        autoHideTimer?.invalidate()
        autoHideTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: false) { [weak self] _ in
            self?.fadeOut()
        }
    }

    func toggleSize() {
        currentSize = currentSize == .minimized ? .expanded : .minimized

        NSAnimationContext.runAnimationGroup({ context in
            context.duration = 0.3
            context.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)

            var newFrame = frame
            let newSize = currentSize.size
            newFrame.origin.x = frame.midX - newSize.width / 2
            newFrame.origin.y = frame.midY - newSize.height / 2
            newFrame.size = newSize

            animator().setFrame(newFrame, display: true)
        }, completionHandler: nil)

        // Notify view controller of size change
        if let hudVC = contentViewController as? HUDViewController {
            hudVC.windowSizeChanged(to: currentSize)
        }

        // Handle auto-hide timer based on new size
        if currentSize == .expanded {
            // Cancel auto-hide when expanded
            autoHideTimer?.invalidate()
            autoHideTimer = nil
        } else {
            // Reset auto-hide timer when minimized
            resetAutoHideTimer()
        }
    }

    func setSize(_ size: WindowSize) {
        if currentSize != size {
            toggleSize()
        }
    }
}
