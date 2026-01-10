# Offline Attendance Mode

## Overview
Complete attendance system that works **without WiFi or internet connection**.

## Features
✓ Face recognition for check-in/check-out
✓ Real-time display on ST7789 LCD (240x240)
✓ Local data storage (Excel files)
✓ No network required
✓ Automatic cooldown (5 minutes between check-ins)
✓ Recent events display

## Quick Start

### Option 1: Auto-detect WiFi
```bash
./start_attendance.sh
```
Automatically detects WiFi and chooses the best mode.

### Option 2: Force Offline Mode
```bash
./run_offline.sh
```

### Option 3: Manual Launch
```bash
python3 offline_attendance.py
```

## LCD Display Features

The ST7789 display shows:
- **Header**: "ATTENDANCE" with current time
- **Status**: CHECK IN / CHECK OUT / COOLDOWN / READY
- **Event Info**: Name, time, confidence
- **Recent Events**: Last 3 check-ins displayed

## Display Layout

```
┌─────────────────────────────┐
│ ATTENDANCE        10:30:15  │  <- Header
├─────────────────────────────┤
│    ┌─────────────────┐      │
│    │   CHECK IN      │      │  <- Status Badge
│    └─────────────────┘      │
│                             │
│ Name: Linh                  │  <- Event Details
│ Time: 10:30:15              │
│                             │
│ Recent:                     │  <- Recent Events
│  10:25 John                 │
│  10:20 Sarah                │
│  10:15 Mike                 │
└─────────────────────────────┘
```

## Data Storage

All data is stored locally in:
- `data/attendance.xlsx` - Main attendance records
- `data/status_log.csv` - Status changes log
- `data/debug_log.csv` - Debug information

## Controls

- **Press 'q'**: Quit the system
- **Ctrl+C**: Emergency stop

## Configuration

Edit `config.py` to customize:
- `CHECK_IN_COOLDOWN`: Time between check-ins (default: 300 seconds)
- `CAMERA_WIDTH`, `CAMERA_HEIGHT`: Camera resolution
- `RECOGNITION_TOLERANCE`: Face recognition strictness
- `PROCESS_EVERY_N_FRAMES`: Performance tuning

## Troubleshooting

### Display Not Working
```bash
python3 diagnose_display.py
```

### No Camera
- Check camera connection
- Ensure camera is enabled: `sudo raspi-config`
- Test with: `libcamera-hello` (for Pi Camera)

### Face Not Recognized
1. Ensure person is enrolled: `python3 enroll_face.py`
2. Check lighting conditions
3. Reduce `RECOGNITION_TOLERANCE` in config.py

## System Requirements

- Raspberry Pi 3/4/5
- Pi Camera or USB webcam
- ST7789 SPI display (optional but recommended)
- Python 3.7+

## Dependencies

All installed via:
```bash
pip3 install -r requirements.txt --break-system-packages
```

Required packages:
- opencv-python
- face_recognition
- Pillow
- st7789
- openpyxl
- numpy

## Performance

- **FPS**: ~15-20 fps (Pi 3), ~25-30 fps (Pi 4/5)
- **Recognition Time**: ~0.5-1 second per face
- **Memory**: ~200-300 MB
- **Storage**: ~10 KB per day (Excel file)

## Comparison: Online vs Offline

| Feature | Online (Web App) | Offline |
|---------|------------------|---------|
| WiFi Required | Yes | No |
| Display | Browser | ST7789 LCD |
| Remote Access | Yes | No |
| Data Storage | Local + Web | Local only |
| Power Usage | Higher | Lower |
| Speed | Slower | Faster |

## Tips

1. **Better Recognition**: Enroll multiple photos per person
2. **Battery Life**: Disable camera preview for longer operation
3. **Storage**: Export data regularly to free space
4. **Performance**: Increase `PROCESS_EVERY_N_FRAMES` on slower devices

## Export Data

View attendance data:
```bash
python3 main.py --summary
```

## Advanced Usage

Run without LCD display:
```bash
python3 offline_attendance.py --no-display
```

Use access control mode:
```bash
python3 main.py --mode access
```

## Auto-start on Boot

Add to `/etc/rc.local`:
```bash
cd /home/bienth/Documents/dev-camera-pi-3
./run_offline.sh &
```

Or create systemd service (recommended).
