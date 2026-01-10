#!/bin/bash
# Quick ST7789 Display Test
# Run this to verify your ST7789 display is working

echo "======================================"
echo "ST7789 Display Quick Test"
echo "======================================"
echo ""
echo "This will run 3 tests:"
echo "1. Color test (RED, GREEN, BLUE)"
echo "2. Attendance layout test"
echo "3. High contrast text test"
echo ""
echo "Watch your display during the test!"
echo ""

cd "$(dirname "$0")"
python3 test_display_comparison.py

echo ""
echo "======================================"
echo "If you saw all the tests, your display"
echo "is working correctly!"
echo "======================================"
echo ""
echo "Available commands:"
echo "  ./run_display.sh       - Start attendance display"
echo "  python3 test_st7789.py - Full display test suite"
echo "  python3 diagnose_display.py - Diagnostic tool"
echo ""
