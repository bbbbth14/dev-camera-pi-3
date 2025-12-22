# Face Recognition System - Feature Summary

## 🎯 Two Applications Available

### 1. Web Application (`./run_web.sh`)
- **Best for:** Headless systems, remote access, any browser
- **Access:** http://localhost:5000 or http://[your-pi-ip]:5000
- **Works without:** X11/display server

### 2. Desktop GUI (`./run_app.sh`)
- **Best for:** Systems with display connected
- **Requires:** X11/display environment
- **Native:** Tkinter-based desktop application

---

## ✨ Common Features (Both Apps)

### Face Recognition
- ✅ Real-time face detection with OpenCV
- ✅ LBPH (Local Binary Patterns Histograms) recognition
- ✅ Live camera preview with face rectangles
- ✅ Green box for recognized faces, red for unknown
- ✅ Name labels displayed on video

### Enrollment System
- ✅ **Auto-capture:** Just look at the camera
- ✅ **Fast capture:** 5 sample images in ~1-2 seconds
- ✅ **Visual feedback:** Green rectangles show face detection
- ✅ **Progress bar:** Shows 0/5 to 5/5 capture progress
- ✅ **Automatic training:** System retrains after enrollment

### Attendance Tracking
- ✅ **Two-mode toggle:** CHECK IN → CHECK OUT → CHECK IN...
- ✅ **First check-in time:** Records initial arrival
- ✅ **Last check-out time:** Records final departure
- ✅ **Total duration:** Calculates first IN to last OUT
- ✅ **Example:** In 08:00 → Out 18:30 = 10h 30m total

### IN/OUT Monitor
- ✅ **Live status:** Shows all enrolled users
- ✅ **Status badges:** Green (IN) or Gray (OUT)
- ✅ **Time display:** 
  - When IN: "In at: 14:30:15"
  - When OUT: "In: 08:00:00 → Out: 18:30:00 • Total: 10h 30m"
- ✅ **Delete function:** Remove users with confirmation

### Data Logging
- ✅ **Attendance file:** `data/attendance.csv`
  - Records every CHECK_IN and CHECK_OUT event
  - Format: Name, Date, Time, Event, Confidence
  
- ✅ **Status log:** `data/status_log.csv`
  - Logged immediately after each check-in/out
  - Format: Timestamp, Name, Status, Check_In_Time, Check_Out_Time, Duration
  - Perfect for analysis in Excel/Google Sheets

### Activity Log
- ✅ Real-time event logging
- ✅ Shows last 20 events
- ✅ Timestamps all activities
- ✅ Color-coded console output

---

## 📊 Data Files

### Generated Files:
```
data/
├── attendance.csv          # All check-in/out events
├── status_log.csv         # Current status snapshots
├── faces/
│   └── encodings.pkl      # Trained face data
└── images/
    ├── UserName1/         # 5 sample images per user
    ├── UserName2/
    └── ...
```

---

## 🎮 Usage Examples

### Enroll New User:
1. Click "Enroll New Face"
2. Enter name
3. Click "Start Auto-Capture"
4. Look at camera (captures 5 images automatically)
5. Click "Save & Train"

### Track Attendance:
1. Click "Start Attendance Mode"
2. Person looks at camera → Automatic CHECK IN
3. Person looks at camera again → Automatic CHECK OUT
4. View status in IN/OUT Monitor
5. Check logs in `data/status_log.csv`

### Delete User:
1. Find user in IN/OUT Monitor
2. Click "🗑 Delete" button
3. Confirm deletion
4. System automatically retrains

---

## 🔧 Technical Details

### Face Recognition:
- **Algorithm:** LBPH (Local Binary Patterns Histograms)
- **Threshold:** 70 (adjustable in code)
- **Detection:** Haar Cascade
- **Samples per user:** 5 images
- **Recognition cooldown:** 3 seconds (prevents duplicate entries)

### Camera Support:
- **Pi Camera:** Via `rpicam-still` command
- **USB Camera:** OpenCV VideoCapture fallback
- **Resolution:** 640x480 (configurable)
- **Frame rate:** 30 FPS

### Performance:
- **Processing:** Every 2 frames (configurable)
- **Fast capture:** 5 frames between samples
- **Rectangle thickness:** 3px for visibility
- **Font size:** 0.7 for readability

---

## 📝 Configuration

Edit `config.py` to customize:
- Camera resolution
- Recognition threshold
- Processing frame rate
- Directory paths
- And more...

---

## 🚀 Quick Start

**Web App (Recommended for headless):**
```bash
./run_web.sh
# Open browser to http://localhost:5000
```

**Desktop App (Requires display):**
```bash
./run_app.sh
# GUI window opens automatically
```

---

## 📄 Log File Analysis

View attendance data:
```bash
# Recent status updates
tail -20 data/status_log.csv

# All attendance events
cat data/attendance.csv

# Open in Excel for analysis
```

---

## ✅ Synchronized Features

Both apps now have identical functionality:
- ✅ Same recognition algorithm
- ✅ Same enrollment process (5 samples)
- ✅ Same attendance tracking logic
- ✅ Same logging to files
- ✅ Same rectangle drawing (3px, correct coordinates)
- ✅ Same check-in/out toggle behavior
- ✅ Compatible data files

---

**Last Updated:** December 22, 2025
**Version:** 2.0 - Synchronized Desktop & Web Apps
