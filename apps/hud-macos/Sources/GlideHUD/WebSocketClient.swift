import Foundation

class WebSocketClient: NSObject {
    private var webSocketTask: URLSessionWebSocketTask?
    private let session: URLSession
    private let url: URL
    private var isConnected = false
    private var reconnectTimer: Timer?
    private var reconnectDelay: TimeInterval = 1.0

    init(host: String = "127.0.0.1", port: Int = 8765) {
        self.url = URL(string: "ws://\(host):\(port)/hud")!
        self.session = URLSession(configuration: .default)
        super.init()
    }

    func connect() {
        disconnect()

        webSocketTask = session.webSocketTask(with: url)
        webSocketTask?.delegate = self
        webSocketTask?.resume()

        isConnected = true
        reconnectDelay = 1.0

        print("WebSocket connecting to \(url)")
        receiveMessage()
    }

    func disconnect() {
        reconnectTimer?.invalidate()
        reconnectTimer = nil

        if isConnected {
            webSocketTask?.cancel(with: .goingAway, reason: nil)
            isConnected = false
        }
    }

    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            guard let self = self else { return }

            switch result {
            case .success(let message):
                switch message {
                case .data(let data):
                    self.handleMessage(data)
                case .string(let string):
                    if let data = string.data(using: .utf8) {
                        self.handleMessage(data)
                    }
                @unknown default:
                    break
                }

                // Continue receiving messages
                self.receiveMessage()

            case .failure(let error):
                print("WebSocket receive error: \(error)")
                self.handleDisconnection()
            }
        }
    }

    private func handleMessage(_ data: Data) {
        do {
            let json = try JSONSerialization.jsonObject(with: data, options: []) as? [String: Any]
            guard let type = json?["type"] as? String else { return }

            print("WebSocket received message type: \(type)")

            switch type {
            case "scroll":
                if let vy = json?["vy"] as? Double,
                   let speed = json?["speed"] as? Double {
                    print("Scroll event: vy=\(vy), speed=\(speed)")
                    NotificationCenter.default.post(
                        name: NSNotification.Name("GlideScrollEvent"),
                        object: nil,
                        userInfo: ["vy": vy, "speed": speed]
                    )
                }

            case "hide":
                NotificationCenter.default.post(
                    name: NSNotification.Name("GlideHideEvent"),
                    object: nil
                )

            case "config":
                if let config = json {
                    NotificationCenter.default.post(
                        name: NSNotification.Name("GlideConfigEvent"),
                        object: nil,
                        userInfo: config
                    )
                }

            case "touchproof":
                if let active = json?["active"] as? Bool,
                   let hands = json?["hands"] as? Int {
                    NotificationCenter.default.post(
                        name: NSNotification.Name("GlideTouchProofEvent"),
                        object: nil,
                        userInfo: ["active": active, "hands": hands]
                    )
                }

            case "camera":
                if let frameBase64 = json?["frame"] as? String,
                   let width = json?["width"] as? Int,
                   let height = json?["height"] as? Int,
                   let frameData = Data(base64Encoded: frameBase64) {
                    NotificationCenter.default.post(
                        name: NSNotification.Name("GlideCameraEvent"),
                        object: nil,
                        userInfo: ["frame": frameData, "width": width, "height": height]
                    )
                }

            default:
                print("Unknown message type: \(type)")
            }

        } catch {
            print("Failed to parse WebSocket message: \(error)")
        }
    }

    private func handleDisconnection() {
        isConnected = false
        scheduleReconnect()
    }

    private func scheduleReconnect() {
        guard reconnectTimer == nil else { return }

        print("WebSocket disconnected, reconnecting in \(reconnectDelay)s...")

        reconnectTimer = Timer.scheduledTimer(withTimeInterval: reconnectDelay, repeats: false) { [weak self] _ in
            self?.reconnectTimer = nil
            self?.connect()
        }

        // Exponential backoff
        reconnectDelay = min(reconnectDelay * 2, 30.0)
    }

    func send(message: String) {
        guard isConnected else { return }

        let message = URLSessionWebSocketTask.Message.string(message)
        webSocketTask?.send(message) { error in
            if let error = error {
                print("WebSocket send error: \(error)")
            }
        }
    }

    func sendModeChange(expanded: Bool) {
        let message = "{\"type\": \"mode\", \"expanded\": \(expanded)}"
        send(message: message)
    }

    func sendCameraEnabled(enabled: Bool) {
        let message = "{\"type\": \"camera_enabled\", \"enabled\": \(enabled)}"
        send(message: message)
    }

    deinit {
        disconnect()
    }
}

extension WebSocketClient: URLSessionWebSocketDelegate {
    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didOpenWithProtocol protocol: String?) {
        print("WebSocket connected")
        NotificationCenter.default.post(name: NSNotification.Name("GlideWebSocketConnected"), object: nil)
    }

    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didCloseWith closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        print("WebSocket closed with code: \(closeCode.rawValue)")
        handleDisconnection()
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        if let error = error {
            print("WebSocket error: \(error)")
            handleDisconnection()
        }
    }
}
