#!/bin/bash
# MediRecord Launcher for Mac/Linux
# Double-click this file to start

# Get the directory where this script is located
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Check Python
if ! command -v python3 &>/dev/null; then
    osascript -e 'display dialog "Python 3 is not installed.\n\nPlease install it from https://www.python.org/downloads/" with title "MediRecord" buttons {"OK"} default button "OK" with icon stop' 2>/dev/null || \
    echo "ERROR: Python 3 not found. Install from https://www.python.org/downloads/"
    exit 1
fi

# Install dependencies silently
python3 -m pip install -r requirements.txt --quiet --disable-pip-version-check 2>/dev/null

# Start app in background
python3 app.py &
APP_PID=$!

# Wait for server to start then open browser
sleep 2
if command -v open &>/dev/null; then
    open http://127.0.0.1:5000      # macOS
elif command -v xdg-open &>/dev/null; then
    xdg-open http://127.0.0.1:5000  # Linux
fi

# Keep running until user closes terminal
echo ""
echo "  MediRecord is running."
echo "  Browser opened at http://127.0.0.1:5000"
echo ""
echo "  To STOP: close this window or press Ctrl+C"
wait $APP_PID
