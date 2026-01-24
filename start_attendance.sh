#!/bin/bash
# Enhanced Smart Attendance Launcher
# Auto-detects WiFi and runs appropriate mode
# Features: User IDs, Monthly Summaries, Total Working Time

cd "$(dirname "$0")"

DISPLAY_PID=""

start_lcd_display() {
    if [ -x "./run_display.sh" ]; then
        # Avoid starting multiple display processes.
        if pgrep -f "python3 .*display_attendance\.py" >/dev/null 2>&1; then
            echo "🖥️  LCD display already running"
            return 0
        fi

        echo "🖥️  Starting LCD display (ST7789)..."
        ./run_display.sh >/tmp/attendance_display.log 2>&1 &
        DISPLAY_PID=$!
        sleep 1
        return 0
    fi

    echo "⚠️  run_display.sh not executable; skipping LCD display"
    echo "   Fix with: chmod +x run_display.sh"
}

stop_lcd_display() {
    if [ -n "$DISPLAY_PID" ] && kill -0 "$DISPLAY_PID" >/dev/null 2>&1; then
        echo "🛑 Stopping LCD display..."
        kill "$DISPLAY_PID" >/dev/null 2>&1 || true
    fi
}

trap stop_lcd_display EXIT INT TERM

clear
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     ENHANCED ATTENDANCE SYSTEM - SMART LAUNCHER              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 NEW FEATURES:"
echo "  ✓ Random User IDs for each person"
echo "  ✓ Monthly summary with total working hours"
echo "  ✓ Automatic late time and overtime tracking"
echo "  ✓ Per-user monthly sheets with statistics"
echo ""

# Check WiFi connection
echo "🔍 Checking network connectivity..."
if ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then
    # WiFi Available - Run Web Mode
    IP=$(hostname -I | awk '{print $1}')
    SSID=$(iwgetid -r 2>/dev/null || echo "Connected")
    
    echo "✓ Network: ONLINE"
    echo "  📡 WiFi: $SSID"
    echo "  🌐 IP: $IP"
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  🌐 Starting WEB MODE"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "🔗 Access Points:"
    echo "  • Local:   http://localhost:5000"
    echo "  • Network: http://$IP:5000"
    echo ""
    echo "📊 Web Features:"
    echo "  • Live camera feed"
    echo "  • Face enrollment"
    echo "  • Check-in/Check-out"
    echo "  • View attendance records"
    echo "  • Monthly statistics with User IDs"
    echo ""
    sleep 2

    # Web mode: also show status on the ST7789 LCD.
    start_lcd_display

    # Avoid SPI contention: web_app.py has an optional internal LCD driver.
    export DISABLE_WEB_LCD=1
    
    ./run_web.sh
    
else
    # No WiFi - Run Offline Mode
    echo "✗ Network: OFFLINE"
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  📷 Starting OFFLINE MODE"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "📋 Offline Features:"
    echo "  • Camera display with face recognition"
    echo "  • Local check-in/check-out tracking"
    echo "  • Data saved to Excel with User IDs"
    echo "  • Monthly summaries auto-calculated"
    echo ""
    echo "⌨️  Press 'q' to quit"
    echo ""
    sleep 2

    # Attendance mode: also show status on the ST7789 LCD.
    start_lcd_display

    python3 offline_attendance.py --no-display
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  💾 DATA SAVED"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📁 Files Updated:"
echo "  • data/attendance.xlsx  - Monthly sheets with User IDs"
echo "  • data/user_ids.csv     - User ID mappings"
echo "  • data/status_log.csv   - Status change log"
echo ""
echo "📊 Each Excel sheet includes:"
echo "  • Daily attendance for entire month"
echo "  • User name and unique ID in header"
echo "  • Monthly summary with:"
echo "    - Total working days"
echo "    - Total hours worked"
echo "    - Days late and total late time"
echo "    - Days with overtime and total OT"
echo ""
echo "✅ Session complete!"
echo ""
