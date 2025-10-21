import AppKit

@MainActor
class AppDelegate: NSObject, NSApplicationDelegate {

    private var pulseRingWindow: PulseRingWindow?
    private var webSocketClient: WebSocketClient?
    private var statusItem: NSStatusItem?
    private var eventMonitor: Any?
    private var autoHideTimer: Timer?

    // For handling scroll state
    private var lastScrollTime: Date?
    private var scrollResetTimer: Timer?

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Setup status bar icon
        setupStatusBar()

        // Create HUD window
        pulseRingWindow = PulseRingWindow()

        // Load preferences
        loadPreferences()

        // Register global hotkey (CMD + CTRL + G)
        setupGlobalHotkey()

        // Check visibility preference
        let visibility = UserDefaults.standard.string(forKey: "glide.hud.visibility") ?? "always"
        if visibility != "hidden" {
            pulseRingWindow?.show()
        }

        // Initialize WebSocket client
        webSocketClient = WebSocketClient()
        webSocketClient?.connect()

        // Listen for WebSocket events
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleScrollEvent(_:)),
            name: NSNotification.Name("GlideScrollEvent"),
            object: nil
        )

        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleWebSocketConnected),
            name: NSNotification.Name("GlideWebSocketConnected"),
            object: nil
        )
    }

    private func setupStatusBar() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusItem?.button?.title = "◉"

        let menu = NSMenu()
        menu.addItem(NSMenuItem(title: "Toggle HUD", action: #selector(toggleHUD), keyEquivalent: ""))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(NSMenuItem(title: "Quit Glide HUD", action: #selector(terminate), keyEquivalent: "q"))
        statusItem?.menu = menu
    }

    private func setupGlobalHotkey() {
        // Monitor for CMD + CTRL + G
        eventMonitor = NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { [weak self] event in
            let flags = event.modifierFlags.intersection(.deviceIndependentFlagsMask)
            if flags.contains([.command, .control]) && event.keyCode == 5 { // 5 is 'G'
                self?.toggleHUD()
            }
        }

        // Also monitor local events
        NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            let flags = event.modifierFlags.intersection(.deviceIndependentFlagsMask)
            if flags.contains([.command, .control]) && event.keyCode == 5 {
                self?.toggleHUD()
                return nil
            }
            return event
        }
    }

    private func loadPreferences() {
        // Load position preference
        let positionString = UserDefaults.standard.string(forKey: "glide.hud.position") ?? "top-right"
        let position: PulseRingWindow.Position = {
            switch positionString {
            case "top-left": return .topLeft
            case "bottom-right": return .bottomRight
            case "bottom-left": return .bottomLeft
            default: return .topRight
            }
        }()
        pulseRingWindow?.setPosition(position)
    }

    // MARK: - Event Handlers

    @objc private func toggleHUD() {
        guard let window = pulseRingWindow else { return }

        if window.isVisible {
            window.hide()
            UserDefaults.standard.set("hidden", forKey: "glide.hud.visibility")
        } else {
            window.show()
            UserDefaults.standard.set("always", forKey: "glide.hud.visibility")
        }
    }

    @objc private func handleScrollEvent(_ notification: Notification) {
        guard let userInfo = notification.userInfo,
              let vy = userInfo["vy"] as? Double,
              let speed = userInfo["speed"] as? Double,
              let view = pulseRingWindow?.contentView as? PulseRingView else { return }

        DispatchQueue.main.async { [weak self] in
            // Update state based on scroll direction
            if vy > 0.1 {
                view.setState(.scrollingUp)
            } else if vy < -0.1 {
                view.setState(.scrollingDown)
            } else if speed > 0.01 {
                view.setState(.active)
            }

            // Handle auto-hide
            self?.handleAutoHide()

            // Reset to active state after a delay
            self?.scrollResetTimer?.invalidate()
            self?.scrollResetTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: false) { _ in
                DispatchQueue.main.async {
                    if view.currentState == .scrollingUp || view.currentState == .scrollingDown {
                        view.setState(.active)
                    }
                }
            }
        }
    }

    @objc private func handleWebSocketConnected() {
        // Set initial state when connected
        if let view = pulseRingWindow?.contentView as? PulseRingView {
            view.setState(.active)
        }
    }

    private func handleAutoHide() {
        let visibility = UserDefaults.standard.string(forKey: "glide.hud.visibility") ?? "always"
        guard visibility == "autohide" else { return }

        // Show window if hidden
        if pulseRingWindow?.isVisible == false {
            pulseRingWindow?.show()
        }

        // Reset auto-hide timer
        autoHideTimer?.invalidate()
        autoHideTimer = Timer.scheduledTimer(withTimeInterval: 2.0, repeats: false) { [weak self] _ in
            DispatchQueue.main.async {
                self?.pulseRingWindow?.hide()

                // Reset to idle state
                if let view = self?.pulseRingWindow?.contentView as? PulseRingView {
                    view.setState(.idle)
                }
            }
        }
    }

    @objc func terminate() {
        webSocketClient?.disconnect()
        if let monitor = eventMonitor {
            NSEvent.removeMonitor(monitor)
        }
        NSApp.terminate(nil)
    }
}
