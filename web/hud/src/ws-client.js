/**
 * WebSocket client for HUD communication
 */

export class WebSocketClient {
  constructor(url = `ws://127.0.0.1:${import.meta.env.VITE_WS_PORT || 8765}/hud`) {
    this.url = url;
    this.ws = null;
    this.reconnectTimer = null;
    this.eventHandlers = new Map();
  }
  
  connect(token) {
    const connectUrl = token ? `${this.url}?token=${token}` : this.url;
    
    try {
      this.ws = new WebSocket(connectUrl);
      
      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.clearReconnectTimer();
      };
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleEvent(data);
        } catch (e) {
          console.error('Failed to parse message:', e);
        }
      };
      
      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.scheduleReconnect();
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (e) {
      console.error('Failed to connect:', e);
      this.scheduleReconnect();
    }
  }
  
  on(event, handler) {
    this.eventHandlers.set(event, handler);
  }
  
  handleEvent(event) {
    const handler = this.eventHandlers.get(event.type);
    if (handler) {
      handler(event);
    }
  }
  
  scheduleReconnect() {
    this.clearReconnectTimer();
    this.reconnectTimer = setTimeout(() => {
      console.log('Attempting to reconnect...');
      this.connect();
    }, 2000);
  }
  
  clearReconnectTimer() {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
  
  disconnect() {
    this.clearReconnectTimer();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}