# Attendance Excel Format - Updated to Monthly Per-User Format

## What Changed

The Excel attendance tracking format has been updated from a single-sheet format to a **monthly per-user format**.

### Old Format (Before)
- **Single sheet** named "Attendance"
- **One row per person per day**
- All users mixed together in one sheet
- Columns: Name, Day, Time In, Time Out, Total, Status, Time Late, Time OT

### New Format (Current)
- **One sheet per user per month**
- Sheet names: `{UserName}_{Month}_{Year}` (e.g., "Linh_January_2026")
- **Pre-filled calendar** with all days of the month
- Each day has: Date, Day, First In, Last Out, Total Hours, Status, Late, OT

## Benefits

1. **Better Organization**: Each person has their own dedicated sheet
2. **Monthly View**: See the entire month at a glance
3. **Easy Tracking**: Quickly identify attendance patterns, late days, overtime
4. **Historical Data**: Each month gets a new sheet (e.g., Linh_January_2026, Linh_February_2026)
5. **Visual Clarity**: Weekends are highlighted in gray
6. **Pre-filled**: All days are already present, making it easy to see missing attendance

## File Structure

### Example Excel File
```
attendance.xlsx
├── Template (hidden)           # Template for new user sheets
├── Linh_January_2026          # Linh's attendance for January 2026
│   ├── Header: "Linh - January 2026"
│   ├── Columns: Date, Day, First In, Last Out, Total Hours, Status, Late, OT
│   └── Rows: 1-31 (all days of January)
├── John_January_2026          # John's attendance for January 2026
└── Mary_January_2026          # Mary's attendance for January 2026
```

### Sheet Layout
```
Row 1: User Name and Month (merged header)
       Example: "Linh - January 2026"

Row 2: Column Headers
       Date | Day | First In | Last Out | Total Hours | Status | Late | OT

Row 3+: Daily attendance (pre-filled for entire month)
       2026-01-01 | Wed | 08:15:00 | 17:30:00 | 9h 15m | ON TIME | 0m | 30m
       2026-01-02 | Thu | 08:45:00 | 17:00:00 | 8h 15m | LATE    | 15m | 0m
       2026-01-03 | Fri |          |          |        |         |     |
       ...
       2026-01-31 | Fri | 08:20:00 | 18:00:00 | 9h 40m | ON TIME | 0m | 1h 0m
```

## Attendance Logic

### Check-In
- Records **first check-in** of the day only
- Determines if LATE (after 8:30 AM) or ON TIME
- Calculates late time in hours/minutes
- If already checked in and checked out, clears checkout to toggle status back to IN

### Check-Out
- Records **last check-out** of the day (always updates)
- Calculates total hours worked (First In to Last Out)
- Calculates overtime (after 5:00 PM)
- Updates Total Hours, OT columns

### Status Display
- **ON TIME**: Green text (checked in before 8:30 AM)
- **LATE**: Red text (checked in after 8:30 AM)
- **Overtime**: Orange text (worked after 5:00 PM)

## How It Works with the System

### When a user checks in/out:
1. System recognizes face → identifies user name
2. Looks for user's sheet for current month (e.g., "Linh_January_2026")
3. If sheet doesn't exist, creates new sheet with monthly calendar
4. Finds today's row in the calendar
5. Updates First In (check-in) or Last Out (check-out)
6. Calculates and updates Total Hours, Late time, Overtime

### Automatic Sheet Creation
- New sheets are created automatically when:
  - First time a user checks in during a new month
  - A new user is recognized by the system
- Each sheet contains all days of that month (pre-filled)
- Weekends (Sat/Sun) are highlighted in gray

## Example Output

### Linh's Sheet - January 2026
```
                    Linh - January 2026

Date       | Day | First In | Last Out | Total Hours | Status   | Late | OT
-----------|-----|----------|----------|-------------|----------|------|--------
2026-01-01 | Wed | 08:15:00 | 17:30:00 | 9h 15m      | ON TIME  | 0m   | 30m
2026-01-02 | Thu | 08:45:00 | 17:00:00 | 8h 15m      | LATE     | 15m  | 0m
2026-01-03 | Fri |          |          |             |          |      |
2026-01-04 | Sat |          |          |             |          |      |      [Gray]
2026-01-05 | Sun |          |          |             |          |      |      [Gray]
2026-01-06 | Mon | 08:20:00 | 18:00:00 | 9h 40m      | ON TIME  | 0m   | 1h 0m
...
```

## Technical Details

### Code Changes
- **attendance_tracker.py**:
  - `_create_attendance_file()`: Creates template with hidden Template sheet
  - `_get_or_create_user_sheet()`: Gets or creates user's monthly sheet with pre-filled calendar
  - `record_event()`: Updated to work with per-user sheets
  - `get_user_status()`: Reads from all user sheets to get current status
  - `get_today_attendance()`: Aggregates today's attendance from all user sheets

### Thread Safety
- Excel file operations are protected with `_excel_lock`
- Safe for concurrent access from web app and offline attendance system

### Backwards Compatibility
- Old sheets (if present) are preserved but not used
- New attendance data goes to new per-user sheets only

## Testing

Run the test script to verify:
```bash
python3 test_new_excel_format.py
```

This will:
1. Create multiple test users
2. Record check-ins and check-outs
3. Verify Excel structure
4. Show sheet contents

## Migration Notes

If you have existing attendance data in the old format:
1. The old "Attendance" sheet will remain in the file
2. New attendance will be recorded in the new per-user format
3. You can manually copy historical data if needed
4. Or simply start fresh with the new format

## Summary

✓ One sheet per user per month
✓ Pre-filled monthly calendar (all days visible)
✓ Easy to track attendance patterns
✓ Color-coded status (Late=Red, On Time=Green, OT=Orange)
✓ Weekends highlighted
✓ Automatic sheet creation for new users/months
✓ Thread-safe for concurrent access
