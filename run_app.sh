#!/bin/bash
# Launch the GUI application

echo "Starting Face Recognition GUI Application..."
echo ""

# Activate virtual environment
source venv/bin/activate

# Check if DISPLAY is available
if [ -z "$DISPLAY" ]; then
    echo "================================================"
    echo "  ERROR: No display detected"
    echo "================================================"
    echo ""
    echo "  The GUI app requires a display (X11)."
    echo "  You have two options:"
    echo ""
    echo "  1. Use the Web Interface instead:"
    echo "     → ./run_web.sh"
    echo ""
    echo "  2. Enable X11 forwarding if using SSH:"
    echo "     → ssh -X user@hostname"
    echo ""
    echo "================================================"
    exit 1
fi

# Get IP address
IP=$(hostname -I | awk '{print $1}')

echo "================================================"
echo "  Face Recognition Desktop Application"
echo "================================================"
echo ""
echo "  Opening GUI window..."
echo "  Press Ctrl+C to stop"
echo ""
echo "================================================"
echo ""

# Run the GUI app
python3 app.py
