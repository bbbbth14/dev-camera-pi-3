#!/bin/bash

# Quick start script for Face Recognition System

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Face Recognition System - Quick Start"
echo "====================================="
echo ""
echo "Choose an option:"
echo "1. Enroll a new face"
echo "2. Run attendance system (check-in/check-out)"
echo "3. Run access control system (door/box unlock)"
echo "4. Show today's summary"
echo "5. List enrolled faces"
echo "6. Test camera"
echo "7. Exit"
echo ""
read -p "Enter your choice (1-7): " choice

case $choice in
    1)
        read -p "Enter person's name: " name
        python3 enroll_face.py --name "$name"
        ;;
    2)
        echo "Starting attendance system..."
        echo "Press 'q' to quit, 's' to show summary"
        python3 main.py --mode attendance
        ;;
    3)
        echo "Starting access control system..."
        echo "Press 'q' to quit"
        python3 main.py --mode access
        ;;
    4)
        python3 main.py --summary
        ;;
    5)
        python3 enroll_face.py --list
        ;;
    6)
        echo "Testing camera... (testing face detection)"
        python3 face_detector.py
        ;;
    7)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
