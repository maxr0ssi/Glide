# Glide HUD

Web-based HUD for Glide gesture control.

## Development

1. Install dependencies:
   ```bash
   npm install
   ```

2. Run development server:
   ```bash
   npm run dev
   ```

3. The HUD will open in your browser and attempt to connect to the WebSocket server.

## Configuration

- `VITE_WS_PORT`: WebSocket port (default: 8765)

## Testing with Glide

1. Start Glide with WebSocket enabled:
   ```bash
   python -m glide.app.main
   ```

2. Run the HUD dev server:
   ```bash
   npm run dev
   ```

3. Perform scroll gestures to see the HUD in action

## Features

- **Direction arrows**: Show scroll direction (up/down)
- **Speed bars**: Visual representation of scroll speed
- **Fade in/out**: Automatic fade when scrolling starts/stops
- **Auto-reconnect**: Reconnects if WebSocket connection is lost
- **Position support**: Can be positioned via config events