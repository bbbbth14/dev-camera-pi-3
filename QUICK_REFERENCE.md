# Face Recognition System - Quick Reference Guide

## Setup Commands

### First-time Setup
```bash
# Run installation script
bash install.sh

# Enable camera (if using Pi Camera)
sudo raspi-config
# Navigate to: Interface Options -> Camera -> Enable

# Reboot
sudo reboot
```

### Manual Installation
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3-pip python3-dev cmake libopenblas-dev libatlas-base-dev

# Install Python packages
pip3 install -r requirements.txt
```

## Usage Commands

### Enroll New Faces
```bash
# Enroll a person (captures 5 samples)
python3 enroll_face.py --name "John Doe"

# Enroll with custom number of samples
python3 enroll_face.py --name "Jane Smith" --samples 10

# List all enrolled faces
python3 enroll_face.py --list

# Remove a face
python3 enroll_face.py --remove "John Doe"
```

### Run the System

#### Attendance Mode (Check-in/Check-out)
```bash
# Start attendance system
python3 main.py --mode attendance

# Or simply
python3 main.py
```

#### Access Control Mode (Door/Box Control)
```bash
# Start access control
python3 main.py --mode access
```

### Reports and Summaries
```bash
# Show today's summary
python3 main.py --summary

# Export attendance report
python3 main.py --export report.csv
```

### Testing
```bash
# Test face detection
python3 face_detector.py

# Test face recognition
python3 face_recognizer.py

# Test attendance tracker
python3 attendance_tracker.py
```

### Quick Start Menu
```bash
# Use the interactive menu
bash start.sh
```

## Keyboard Shortcuts (while running)

- `q` - Quit the application
- `s` - Show today's summary
- `SPACE` - Capture sample (during enrollment)
- `ESC` - Cancel enrollment

## Configuration

Edit `config.py` to customize:

### Camera Settings
```python
CAMERA_WIDTH = 640           # Camera resolution width
CAMERA_HEIGHT = 480          # Camera resolution height
USE_PI_CAMERA = True         # True for Pi Camera, False for USB
```

### Recognition Settings
```python
RECOGNITION_TOLERANCE = 0.6  # Lower = stricter (0.4-0.6)
MODEL = 'hog'                # 'hog' (faster) or 'cnn' (accurate)
PROCESS_EVERY_N_FRAMES = 2   # Process every Nth frame
```

### Access Control
```python
USE_GPIO = True              # Enable GPIO for relay
RELAY_PIN = 17               # GPIO pin number
UNLOCK_DURATION = 3          # Seconds to unlock
```

### Attendance Settings
```python
CHECK_IN_COOLDOWN = 300      # Seconds between check-ins (5 min)
```

## Troubleshooting

### Camera not working
```bash
# Check if camera is enabled
vcgencmd get_camera

# Should show: supported=1 detected=1

# Enable camera
sudo raspi-config
# Interface Options -> Camera -> Enable

# Reboot
sudo reboot
```

### Import errors
```bash
# Reinstall packages
pip3 install --upgrade -r requirements.txt

# Install system dependencies
sudo apt-get install -y python3-opencv libatlas-base-dev
```

### Slow performance
- Reduce camera resolution in `config.py`
- Increase `PROCESS_EVERY_N_FRAMES` to 3 or 4
- Use 'hog' model instead of 'cnn'
- Disable preview: `SHOW_PREVIEW = False`

### GPIO not working
```bash
# Install RPi.GPIO
pip3 install RPi.GPIO

# Run with sudo for GPIO access
sudo python3 main.py --mode access
```

## File Structure
```
cameraPI/
├── config.py                 # Configuration
├── face_detector.py          # Face detection
├── face_recognizer.py        # Face recognition
├── attendance_tracker.py     # Attendance tracking
├── enroll_face.py           # Enrollment script
├── main.py                  # Main application
├── install.sh               # Installation script
├── start.sh                 # Quick start menu
├── requirements.txt         # Python dependencies
├── README.md                # Full documentation
├── QUICK_REFERENCE.md       # This file
└── data/
    ├── faces/               # Face encodings
    │   └── encodings.pkl
    ├── images/              # Captured images
    └── attendance.csv       # Attendance log
```

## Hardware Setup

### Raspberry Pi Camera Module
1. Connect camera ribbon cable to CSI port
2. Enable camera in raspi-config
3. Set `USE_PI_CAMERA = True` in config.py

### USB Webcam
1. Connect USB webcam
2. Set `USE_PI_CAMERA = False` in config.py

### Relay Module (for access control)
1. Connect relay to GPIO pin (default: pin 17)
2. Connect power and ground
3. Set `USE_GPIO = True` in config.py
4. Configure `RELAY_PIN` in config.py
5. Run with sudo: `sudo python3 main.py --mode access`

## Tips

- **Better Recognition**: Enroll multiple samples in different lighting
- **Performance**: Lower resolution for faster processing on Pi 3
- **Accuracy**: Adjust `RECOGNITION_TOLERANCE` (lower = stricter)
- **Privacy**: Images stored in `data/images/` can be deleted
- **Backup**: Save `data/faces/encodings.pkl` to preserve enrollments

## Common Use Cases

### Office Check-in System
```bash
python3 main.py --mode attendance
```
- Employees check in/out by showing face
- 5-minute cooldown prevents duplicate check-ins
- View summary with 's' key

### Smart Lock/Box
```bash
sudo python3 main.py --mode access
```
- Unlock door/box when authorized face detected
- Automatic lock after 3 seconds
- Logs all access attempts

### Kiosk Mode (autostart on boot)
```bash
# Add to /etc/rc.local
cd /home/bienth/cameraPI
python3 main.py --mode attendance &
```
