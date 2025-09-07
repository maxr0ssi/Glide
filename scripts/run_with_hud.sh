#!/bin/bash
# Run Glide with native macOS HUD

echo "Starting Glide with native HUD..."
echo ""

# Check if Swift is installed
if ! command -v swift &> /dev/null; then
    echo "Error: Swift is not installed. Please install Xcode Command Line Tools."
    exit 1
fi

# Start Python backend in headless mode
echo "Starting gesture detection backend..."
python -m glide.app.main --headless &
PYTHON_PID=$!

# Give backend time to start
sleep 2

# Build and start Swift HUD
echo "Building and starting HUD..."
cd apps/hud-macos
swift build --configuration release

if [ $? -eq 0 ]; then
    swift run --configuration release &
    HUD_PID=$!
else
    echo "Failed to build HUD"
    kill $PYTHON_PID 2>/dev/null
    exit 1
fi

cd ../..

echo ""
echo "Glide is running!"
echo "- Press CMD+CTRL+G to toggle HUD"
echo "- Click expand button to see camera feed"
echo "- Press Ctrl+C to stop"
echo ""

# Function to cleanup on exit
cleanup() {
    echo "Stopping Glide..."
    kill $PYTHON_PID 2>/dev/null
    kill $HUD_PID 2>/dev/null
    exit 0
}

# Set trap for cleanup
trap cleanup INT TERM

# Wait for processes
wait