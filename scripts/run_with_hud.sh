#!/bin/bash
# Run Glide with native macOS HUD

set -e  # Exit on error

echo "🚀 Starting Glide with native HUD..."
echo

# Check dependencies
if ! command -v swift &> /dev/null; then
    echo "❌ Error: Swift is not installed. Please install Xcode Command Line Tools:"
    echo "  xcode-select --install"
    exit 1
fi

if ! command -v python3.10 &> /dev/null; then
    echo "❌ Error: Python 3.10 is required but not found"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv", ]; then
    source venv/bin/activate
elif [ -d ".venv310" ]; then
    source .venv310/bin/activate
else
    echo "⚠️  No virtual environment found. Run 'make setup' first."
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n\n🛑 Stopping Glide..."

    # Kill Python backend
    if [ ! -z "$PYTHON_PID" ]; then
        echo "  Stopping backend (PID: $PYTHON_PID)..."
        kill -TERM $PYTHON_PID 2>/dev/null
        sleep 0.5
        kill -9 $PYTHON_PID 2>/dev/null || true
    fi

    # Kill HUD
    if [ ! -z "$HUD_PID" ]; then
        echo "  Stopping HUD (PID: $HUD_PID)..."
        kill -TERM $HUD_PID 2>/dev/null
        sleep 0.5
        kill -9 $HUD_PID 2>/dev/null || true
    fi

    # Kill any process on port 8765
    lsof -ti:8765 | xargs kill -9 2>/dev/null || true

    echo "✓ Cleanup complete"
    exit 0
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Start Python backend in headless mode
echo "🐍 Starting gesture detection backend..."
python -m glide.app.main --headless &
PYTHON_PID=$!
echo "  Backend started (PID: $PYTHON_PID)"

# Give backend time to initialize
sleep 2

# Check if backend is running
if ! ps -p $PYTHON_PID > /dev/null; then
    echo "❌ Backend failed to start"
    exit 1
fi

# Build and start Swift HUD
echo "🖥️  Building and starting HUD..."
cd apps/hud-macos

# Build in debug mode if needed
if [ ! -f .build/debug/GlideHUD ] || [ "$(find Sources -newer .build/debug/GlideHUD 2>/dev/null)" ]; then
    echo "  Building HUD (this may take a moment)..."
    swift build
    if [ $? -ne 0 ]; then
        echo "❌ Failed to build HUD"
        exit 1
    fi
else
    echo "  Using existing HUD build"
fi

# Run the HUD in debug mode for better visibility
swift run &
HUD_PID=$!
echo "  HUD started (PID: $HUD_PID)"

# Give HUD time to initialize window properly
sleep 1

cd ../..

echo
echo "✅ Glide is running!"
echo
echo "📖 Instructions:"
echo "  • Press CMD+CTRL+G to toggle HUD"
echo "  • Click expand button (⤢) for camera feed"
echo "  • Touch index + middle fingers to scroll"
echo "  • Press Ctrl+C to stop"
echo
echo "🔍 Monitoring... (Press Ctrl+C to stop)"

# Wait for processes
wait
