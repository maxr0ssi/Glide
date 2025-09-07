import AppKit
import Carbon

class AppDelegate: NSObject, NSApplicationDelegate {
    var statusItem: NSStatusItem?
    var hudWindow: HUDWindow?
    var eventMonitor: Any?
    var webSocketClient: WebSocketClient?

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Create status bar item with ice crystal icon
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusItem?.button?.title = "❄️"

        let menu = NSMenu()
        menu.addItem(NSMenuItem(title: "Toggle HUD", action: #selector(toggleHUD), keyEquivalent: ""))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(NSMenuItem(title: "Quit Glide HUD", action: #selector(terminate), keyEquivalent: "q"))
        statusItem?.menu = menu

        // Create HUD window
        hudWindow = HUDWindow()

        // Register global hotkey (CMD + CTRL + G)
        setupGlobalHotkey()

        // Initialize WebSocket client
        webSocketClient = WebSocketClient()
        webSocketClient?.connect()

        // Listen for scroll events to show HUD
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleScrollEvent),
            name: NSNotification.Name("GlideScrollEvent"),
            object: nil
        )
    }

    private func setupGlobalHotkey() {
        // Monitor for CMD + CTRL + G
        eventMonitor = NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { [weak self] event in
            // Check for CMD + CTRL + G
            let flags = event.modifierFlags.intersection(.deviceIndependentFlagsMask)
            if flags.contains([.command, .control]) && event.keyCode == 5 { // 5 is 'G'
                self?.toggleHUD()
            }
        }

        // Also monitor local events (when app is focused)
        NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            let flags = event.modifierFlags.intersection(.deviceIndependentFlagsMask)
            if flags.contains([.command, .control]) && event.keyCode == 5 {
                self?.toggleHUD()
                return nil // Consume the event
            }
            return event
        }
    }

    @objc func toggleHUD() {
        hudWindow?.toggleVisibility()
    }

    @objc func handleScrollEvent() {
        DispatchQueue.main.async { [weak self] in
            self?.hudWindow?.showActivity()
        }
    }

    @objc func terminate() {
        webSocketClient?.disconnect()
        if let monitor = eventMonitor {
            NSEvent.removeMonitor(monitor)
        }
        NSApplication.shared.terminate(nil)
    }

    func applicationWillTerminate(_ notification: Notification) {
        webSocketClient?.disconnect()
        if let monitor = eventMonitor {
            NSEvent.removeMonitor(monitor)
        }
    }
}
