#!/bin/bash
# Start attendance display on ST7789 screen

cd "$(dirname "$0")"

echo "Starting Attendance Display on ST7789..."
echo "Press Ctrl+C to stop"
echo ""

python3 display_attendance.py
