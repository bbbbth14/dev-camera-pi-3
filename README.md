# Face Detection & Recognition System for Raspberry Pi

A lightweight face detection and recognition system optimized for Raspberry Pi 3, featuring real-time camera preview and efficient face recognition using OpenCV.

## Features
- ✅ Real-time face detection with live camera preview
- ✅ Face recognition using OpenCV LBPH (Local Binary Patterns Histograms)
- ✅ Check-in/check-out attendance tracking
- ✅ Access control with granted/denied logging
- ✅ Support for Raspberry Pi Camera Module via `rpicam-still`
- ✅ USB webcam fallback support
- ✅ Visual feedback with face detection boxes and labels
- ✅ No compilation required - fast installation
- ✅ Interactive menu system

## Hardware Requirements
- Raspberry Pi 3 Model B or newer
- Raspberry Pi Camera Module (or USB webcam)
- Display (for live preview) or VNC/X11 forwarding
- Power supply
- Optional: Relay module for controlling locks/doors

## Quick Start

### 1. Clone and Setup
```bash
cd ~/Documents
git clone https://github.com/bbbbth14/dev-camera-pi-3.git
cd dev-camera-pi-3
```

### 2. Install Dependencies
```bash
# Install system packages
sudo apt-get update
sudo apt-get install -y python3-opencv python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install opencv-contrib-python numpy pillow picamera2
```

### 3. Run the System
```bash
./start.sh
```

## Interactive Menu

The system provides an easy-to-use menu:

```
Face Recognition System - Quick Start
=====================================

Choose an option:
1. Enroll a new face
2. Run attendance system (check-in/check-out)
3. Run access control system (door/box unlock)
4. Show today's summary
5. List enrolled faces
6. Test camera
7. Exit
```

## Usage Examples

### Enroll a New Face
```bash
# Option 1 from menu, or:
source venv/bin/activate
python3 enroll_face.py --name "John Doe"
# Camera will automatically capture 5 samples with live preview
```

### Run Attendance System
```bash
# Option 2 from menu, or:
source venv/bin/activate
python3 main.py --mode attendance
# Press 'q' to quit, 's' to show summary
```

### Access Control Mode
```bash
# Option 3 from menu, or:
source venv/bin/activate
python3 main.py --mode access
# Grants/denies access based on recognized faces
```

### List Enrolled Faces
```bash
source venv/bin/activate
python3 enroll_face.py --list
```

### Test Camera
```bash
# Option 6 from menu
# Shows 5-second live preview with face detection
```

## Project Structure
```
dev-camera-pi-3/
├── README.md
├── requirements.txt
├── config.py                 # Configuration settings
├── camera_wrapper.py         # Universal camera interface (NEW)
├── face_detector.py          # Face detection module
├── face_recognizer.py        # Face recognition (OpenCV LBPH)
├── attendance_tracker.py     # Check-in/check-out tracking
├── enroll_face.py           # Script to register new faces
├── main.py                  # Main application
├── test_system.py           # System verification script (NEW)
├── start.sh                 # Interactive launcher (NEW)
├── install_picamera.sh      # Pi Camera setup helper (NEW)
└── data/
    ├── faces/               # Stored face encodings
    ├── attendance.csv       # Attendance records
    └── images/              # Captured images
```

## Live Preview Features

When running the system, you'll see:

- **Green rectangles** around detected faces
- **Name labels** with confidence scores
- **System information** overlay (mode, timestamp)
- **Real-time updates** as faces are recognized
- **Keyboard controls** ('q' to quit, 's' for summary)

## Configuration

Edit `config.py` to customize:

```python
# Camera settings
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
USE_PI_CAMERA = True  # Set to False for USB webcam

# Face detection settings
DETECTION_SCALE_FACTOR = 1.1
DETECTION_MIN_NEIGHBORS = 5

# Performance
PROCESS_EVERY_N_FRAMES = 2  # Process every 2nd frame

# Display
SHOW_PREVIEW = True
```

## Technical Details

### Face Recognition Method
- **Algorithm**: OpenCV LBPH (Local Binary Patterns Histograms)
- **Advantages**: 
  - Fast on Raspberry Pi 3
  - No compilation required
  - Good accuracy for controlled environments
  - Lightweight and efficient

### Camera Support
- **Primary**: Raspberry Pi Camera via `rpicam-still` command
- **Fallback**: USB webcam via OpenCV
- **Automatic detection**: System tries Pi Camera first, then USB

### Performance
- Processes every 2nd frame by default
- ~640x480 resolution recommended
- Face recognition in <100ms per frame on Pi 3

## Testing

Run the comprehensive test suite:
```bash
source venv/bin/activate
python3 test_system.py
```

This verifies:
- Face detector initialization
- Face recognizer initialization  
- OpenCV modules availability
- Camera functionality (if available)

## Troubleshooting

### Camera Issues
- **Pi Camera not working?** 
  - Run: `rpicam-still --version` to verify rpicam tools
  - Check camera ribbon cable connection
  
- **No display window?**
  - Ensure you're running on desktop environment (not SSH only)
  - Try VNC or use `ssh -X` for X11 forwarding

### Performance Issues
- Increase `PROCESS_EVERY_N_FRAMES` in config.py
- Reduce `CAMERA_WIDTH` and `CAMERA_HEIGHT`

### Installation Issues
```bash
# If virtual environment has issues:
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install opencv-contrib-python numpy pillow
```

## Differences from Original

This version has been optimized for Raspberry Pi 3:

- ❌ Removed `face_recognition` library (requires slow dlib compilation)
- ❌ Removed `dlib` dependency
- ✅ Added OpenCV LBPH face recognizer (fast, pre-compiled)
- ✅ Added universal camera wrapper for rpicam-still support
- ✅ Added live camera preview with face detection visualization
- ✅ Added interactive menu system
- ✅ Added comprehensive testing tools

## Data Storage

- **Face encodings**: `data/faces/encodings.pkl`
- **Attendance log**: `data/attendance.csv`
- **Sample images**: `data/images/{person_name}/`

## Security Notes

- Face encodings are stored locally
- Attendance data saved in CSV format
- No cloud connectivity required
- Can be enhanced with encryption if needed

## Contributing

Feel free to submit issues and pull requests at:
https://github.com/bbbbth14/dev-camera-pi-3

## License
MIT License
