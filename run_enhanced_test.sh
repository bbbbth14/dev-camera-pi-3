#!/bin/bash
# Enhanced Attendance System - Complete Test and Demo

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Enhanced Attendance System with User IDs and Monthly Stats   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Get current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "📋 New Features:"
echo "  • Random User IDs for each person"
echo "  • Monthly summary with total working hours"
echo "  • Automatic late time and overtime tracking"
echo "  • Per-user monthly sheets with statistics"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "  Running Enhanced Attendance Test..."
echo "════════════════════════════════════════════════════════════════"
echo ""

python3 "$DIR/test_enhanced_attendance.py"

TEST_EXIT=$?

if [ $TEST_EXIT -eq 0 ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                    ✅ TEST SUCCESSFUL                          ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📁 Generated Files:"
    echo "  • data/attendance.xlsx     - Main attendance file"
    echo "  • data/user_ids.csv        - User ID mappings"
    echo "  • data/status_log.csv      - Status change log"
    echo ""
    echo "📊 Excel Structure:"
    echo "  Each user gets their own monthly sheet with:"
    echo "    - User name and unique ID in header"
    echo "    - Daily attendance for entire month"
    echo "    - Monthly summary statistics at bottom:"
    echo "      * Total working days"
    echo "      * Total hours worked"
    echo "      * Days late and total late time"
    echo "      * Days with overtime and total OT"
    echo ""
    echo "🎯 Next Steps:"
    echo "  1. View attendance.xlsx to see the format"
    echo "  2. Check user_ids.csv for ID mappings"
    echo "  3. Run the GUI app: ./run_app.sh"
    echo "  4. Run the Web app: ./run_web.sh"
    echo ""
else
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                    ❌ TEST FAILED                              ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Please check the error messages above."
    echo ""
fi
