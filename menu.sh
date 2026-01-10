#!/bin/bash
# Attendance System Menu
# Choose which mode to run

cd "$(dirname "$0")"

clear
echo "╔════════════════════════════════════════════╗"
echo "║   ATTENDANCE SYSTEM - MODE SELECTOR        ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "Available Modes:"
echo ""
echo "  1) 🌐 Web App Mode (WiFi required)"
echo "     Browser-based interface"
echo "     Access from any device on network"
echo "     ./run_web.sh"
echo ""
echo "  2) 📱 Offline Mode (No WiFi needed) ⭐"
echo "     ST7789 LCD display + Camera"
echo "     Local storage only"
echo "     ./run_offline.sh"
echo ""
echo "  3) 🖥️  Main App Mode"
echo "     Camera preview window"
echo "     Works with/without WiFi"
echo "     python3 main.py"
echo ""
echo "  4) 📊 Display Attendance (LCD only)"
echo "     Show attendance on ST7789"
echo "     No camera needed"
echo "     ./run_display.sh"
echo ""
echo "  5) 🔧 Test Display"
echo "     Test ST7789 LCD screen"
echo "     python3 test_st7789.py"
echo ""
echo "  6) 🤖 Auto-detect (Smart mode)"
echo "     Auto-choose based on WiFi"
echo "     ./start_attendance.sh"
echo ""
echo "  0) Exit"
echo ""
read -p "Select mode (0-6): " choice

case $choice in
    1)
        echo ""
        echo "Starting Web App Mode..."
        echo "=========================================="
        ./run_web.sh
        ;;
    2)
        echo ""
        echo "Starting Offline Mode..."
        echo "=========================================="
        ./run_offline.sh
        ;;
    3)
        echo ""
        echo "Starting Main App Mode..."
        echo "=========================================="
        python3 main.py --mode attendance
        ;;
    4)
        echo ""
        echo "Starting Display Only..."
        echo "=========================================="
        ./run_display.sh
        ;;
    5)
        echo ""
        echo "Testing Display..."
        echo "=========================================="
        python3 test_st7789.py
        ;;
    6)
        echo ""
        echo "Auto-detecting mode..."
        echo "=========================================="
        ./start_attendance.sh
        ;;
    0)
        echo ""
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo ""
        echo "Invalid choice. Please run again."
        exit 1
        ;;
esac
