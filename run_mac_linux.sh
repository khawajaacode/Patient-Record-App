#!/bin/bash
<<<<<<< HEAD
echo "========================================"
echo "  MediRecord - Patient Record System"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 is not installed."
    echo "Install from https://python.org"
    exit 1
fi

echo "Installing required packages..."
pip3 install -r requirements.txt --quiet

echo ""
echo "Starting server..."
echo "Open your browser at: http://127.0.0.1:5000"
echo "Press CTRL+C to stop."
echo ""
=======
echo "MediRecord - Starting..."
pip3 install -r requirements.txt --quiet
>>>>>>> feature
python3 app.py
