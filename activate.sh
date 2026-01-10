#!/bin/bash
# Activation script for the face recognition system

echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""
echo "Available commands:"
echo "  python3 enroll_face.py --name 'Your Name'  - Enroll a new face"
echo "  python3 main.py                            - Run the main system"
echo "  python3 web_app.py                         - Run the web interface"
echo "  python3 display_attendance.py              - Run the display interface"
echo ""
