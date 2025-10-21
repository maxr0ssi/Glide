#!/bin/bash

# Test script for HUD appearance without running full Glide backend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HUD_DIR="$PROJECT_ROOT/apps/hud-macos"

echo "🧪 Building HUD in test mode..."
cd "$HUD_DIR"

# Build the HUD
echo "🔨 Building..."
swift build --configuration debug

echo "🚀 Running HUD in test mode..."
echo ""
echo "Controls:"
echo "  • Press CMD+CTRL+G to toggle HUD"
echo "  • Click expand button (⤢) for expanded mode"
echo "  • Press Ctrl+C to quit"
echo ""
echo "The HUD will show simulated scroll animations"
echo ""

# Run the HUD with test flag
.build/debug/GlideHUD --test
