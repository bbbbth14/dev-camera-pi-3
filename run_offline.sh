#!/bin/bash
# Run Offline Attendance System
# Works without WiFi - all data stored locally

cd "$(dirname "$0")"

echo "=========================================="
echo "OFFLINE ATTENDANCE SYSTEM"
echo "=========================================="
echo ""
echo "Features:"
echo "  ✓ Face recognition check-in/check-out"
echo "  ✓ ST7789 LCD real-time display"
echo "  ✓ Local data storage (no WiFi needed)"
echo "  ✓ Excel attendance reports"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the offline attendance system
python3 offline_attendance.py

echo ""
echo "System stopped."
echo "Data saved to: data/attendance.xlsx"
