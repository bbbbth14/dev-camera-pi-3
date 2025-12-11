# Face Detection & Recognition System for Raspberry Pi

A face detection and recognition system for check-in/check-out and access control using Raspberry Pi 3 Model B V1.2.

## Features
- Real-time face detection using OpenCV
- Face recognition for registered users
- Check-in/check-out tracking
- Access control functionality
- Support for Raspberry Pi Camera Module

## Hardware Requirements
- Raspberry Pi 3 Model B V1.2
- Raspberry Pi Camera Module (or USB webcam)
- Power supply
- Optional: Relay module for controlling locks/doors

## Installation

### 1. Update System
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 2. Install System Dependencies
```bash
sudo apt-get install -y python3-pip python3-dev cmake libopenblas-dev liblapack-dev libjpeg-dev
sudo apt-get install -y libatlas-base-dev gfortran
sudo apt-get install -y python3-opencv
```

### 3. Enable Camera (if using Pi Camera)
```bash
sudo raspi-config
# Navigate to Interface Options -> Camera -> Enable
```

### 4. Install Python Dependencies
```bash
pip3 install -r requirements.txt
```

## Project Structure
```
cameraPI/
├── README.md
├── requirements.txt
├── config.py                 # Configuration settings
├── face_detector.py          # Face detection module
├── face_recognizer.py        # Face recognition module
├── attendance_tracker.py     # Check-in/check-out tracking
├── enroll_face.py           # Script to register new faces
├── main.py                  # Main application
└── data/
    ├── faces/               # Stored face encodings
    ├── attendance.csv       # Attendance records
    └── images/              # Captured images
```

## Usage

### 1. Enroll New Faces
```bash
python3 enroll_face.py --name "John Doe"
```

### 2. Run Check-in/Check-out System
```bash
python3 main.py
```

### 3. Run Access Control Mode
```bash
python3 main.py --mode access
```

## Configuration
Edit `config.py` to customize:
- Camera settings
- Detection confidence threshold
- Recognition tolerance
- GPIO pins for relay control
- Data storage paths

## Troubleshooting
- If camera doesn't work, check connections and enable camera in raspi-config
- For performance issues on Pi 3, reduce camera resolution in config.py
- Install dlib from source if face_recognition installation fails

## License
MIT License
