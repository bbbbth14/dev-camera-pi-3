#!/bin/bash
# Smart Attendance Launcher
# Auto-detects WiFi and runs appropriate mode

cd "$(dirname "$0")"

clear
echo "=========================================="
echo "  SMART ATTENDANCE LAUNCHER"
echo "=========================================="
echo ""

# Check WiFi connection
echo "Checking network connectivity..."
if ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then
    # WiFi Available - Run Web Mode
    IP=$(hostname -I | awk '{print $1}')
    SSID=$(iwgetid -r 2>/dev/null || echo "Connected")
    
    echo "✓ Network: ONLINE"
    echo "  WiFi: $SSID"
    echo "  IP: $IP"
    echo ""
    echo "=========================================="
    echo "  Starting WEB MODE"
    echo "=========================================="
    echo ""
    echo "Access at: http://$IP:5000"
    echo ""
    sleep 1
    
    ./run_web.sh
    
else
    # No WiFi - Run Offline Mode
    echo "✗ Network: OFFLINE"
    echo ""
    echo "=========================================="
    echo "  Starting OFFLINE MODE"
    echo "=========================================="
    echo ""
    echo "Camera display with face recognition"
    echo "Press 'q' to quit"
    echo ""
    sleep 1
    
    python3 offline_attendance.py --no-display
fi

echo ""
echo "Data saved to: data/attendance.xlsx"
