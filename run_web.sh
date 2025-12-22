#!/bin/bash
# Launch the Web-based application

echo "Starting Face Recognition Web Interface..."
echo ""

# Activate virtual environment
source venv/bin/activate

# Install Flask if not installed
pip install flask > /dev/null 2>&1

# Get IP address
IP=$(hostname -I | awk '{print $1}')

echo "================================================"
echo "  Face Recognition Web Interface"
echo "================================================"
echo ""
echo "  Access from this device:"
echo "    → http://localhost:5000"
echo ""
echo "  Access from other devices on network:"
echo "    → http://$IP:5000"
echo ""
echo "  Press Ctrl+C to stop"
echo ""
echo "================================================"
echo ""

# Run the web app
python3 web_app.py
