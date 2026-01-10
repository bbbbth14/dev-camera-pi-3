#!/bin/bash
# Run Offline Attendance with Camera Display
# For local desktop use (not SSH)

cd "$(dirname "$0")"

echo "=========================================="
echo "OFFLINE ATTENDANCE - CAMERA MODE"
echo "=========================================="
echo ""
echo "Features:"
echo "  ✓ Live camera display"
echo "  ✓ Face recognition overlay"
echo "  ✓ Automatic check-in/check-out"
echo "  ✓ No WiFi needed"
echo ""
echo "Controls:"
echo "  Press 'q' to quit"
echo ""
echo "Starting in 2 seconds..."
sleep 2

python3 offline_attendance.py --no-display

echo ""
echo "Attendance data saved to: data/attendance.xlsx"
