#!/usr/bin/env python3
"""Test WebSocket client for Glide HUD.

Connect to the Glide WebSocket server and display received events.

Usage:
    python test_ws_client.py [token]
    
    If a token is provided, it will be included in the connection URL.
"""

import asyncio
import json
import sys
import websockets
from datetime import datetime


async def test_client(token: str = None):
    """Connect to WebSocket server and display events."""
    uri = "ws://127.0.0.1:8765/hud"
    
    # Add token if provided
    if token:
        uri += f"?token={token}"
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected! Listening for events...\n")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    
                    # Format based on event type
                    if data["type"] == "config":
                        print(f"[{timestamp}] CONFIG: position={data.get('position')}, opacity={data.get('opacity')}")
                    elif data["type"] == "scroll":
                        # Create a simple visual bar for speed
                        speed = data.get("speed", 0)
                        bar_length = int(speed * 20)
                        bar = "█" * bar_length + "░" * (20 - bar_length)
                        direction = "↑" if data.get("vy", 0) < 0 else "↓"
                        print(f"[{timestamp}] SCROLL: {direction} vy={data.get('vy'):6.1f}, speed={speed:.2f} [{bar}]")
                    elif data["type"] == "hide":
                        print(f"[{timestamp}] HIDE")
                    else:
                        print(f"[{timestamp}] {data}")
                        
                except json.JSONDecodeError:
                    print(f"[{timestamp}] Raw message: {message}")
                    
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Connection rejected: {e}")
        if e.status_code == 1008 and token is None:
            print("\n💡 Tip: The server may require a token. Check the Glide output for the session token.")
    except ConnectionRefusedError:
        print("❌ Connection refused. Is Glide running with WebSocket enabled?")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Get token from command line if provided
    token = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("Glide WebSocket Test Client")
    print("===========================")
    print("Press Ctrl+C to exit\n")
    
    try:
        asyncio.run(test_client(token))
    except KeyboardInterrupt:
        print("\n\nGoodbye!")