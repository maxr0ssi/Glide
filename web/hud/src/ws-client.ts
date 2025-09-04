/**
 * WebSocket client for HUD communication (Phase 3)
 */

// TODO: Phase 3 - Implement WebSocket client

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectTimer: number | null = null;
  
  constructor(private url: string = 'ws://127.0.0.1:8765/hud') {
    // TODO: Phase 3 - Implement connection logic
  }
  
  connect(): void {
    // TODO: Phase 3 - Connect to WebSocket server
    console.log('WebSocket client - Phase 3 placeholder');
  }
  
  private handleMessage(event: MessageEvent): void {
    // TODO: Phase 3 - Handle scroll/hide/config messages
    // Expected messages:
    // {"type":"scroll","vy":-240.5,"speed":0.62}
    // {"type":"hide"}
    // {"type":"config","position":"bottom-right","opacity":0.85}
  }
  
  private reconnect(): void {
    // TODO: Phase 3 - Implement reconnection logic with backoff
  }
}