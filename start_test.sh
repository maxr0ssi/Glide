#!/bin/bash

echo "Starting Glide backend and HUD test..."

# Function to cleanup processes on exit
cleanup() {
    echo -e "\n\nCleaning up..."
    
    # Kill processes
    if [ ! -z "$GLIDE_PID" ]; then
        echo "Stopping Glide backend (PID: $GLIDE_PID)..."
        kill -TERM $GLIDE_PID 2>/dev/null
        sleep 1
        kill -9 $GLIDE_PID 2>/dev/null
    fi
    
    if [ ! -z "$HUD_PID" ]; then
        echo "Stopping HUD app (PID: $HUD_PID)..."
        kill -TERM $HUD_PID 2>/dev/null
        sleep 1
        kill -9 $HUD_PID 2>/dev/null
    fi
    
    # Also kill any orphaned processes
    pkill -f "python.*main.py.*headless" 2>/dev/null
    pkill -f "GlideHUD" 2>/dev/null
    
    # Kill any process using port 8765
    lsof -ti:8765 | xargs kill -9 2>/dev/null
    
    echo "Cleanup complete!"
    exit 0
}

# Set trap to cleanup on script exit (including Ctrl+C)
trap cleanup EXIT INT TERM

# Start Glide backend in background
echo "Starting Glide backend..."
cd /Users/maxrossi/Documents/Glide
python main.py --headless &
GLIDE_PID=$!
echo "Glide backend started with PID: $GLIDE_PID"

# Wait for backend to initialize
sleep 3

# Start HUD app
echo "Starting HUD app..."
cd /Users/maxrossi/Documents/Glide/apps/hud-macos
GLIDE_HUD_DEV=1 .build/debug/GlideHUD &
HUD_PID=$!
echo "HUD app started with PID: $HUD_PID"

echo ""
echo "Both services are running!"
echo "- Glide backend on PID: $GLIDE_PID"
echo "- HUD app on PID: $HUD_PID"
echo ""
echo "Use CMD+CTRL+G to toggle the HUD"
echo "Perform hand gestures to see scroll events in the HUD"
echo ""
echo "Press Ctrl+C to stop both services..."

# Wait indefinitely until interrupted
wait