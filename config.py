"""
Configuration settings for Face Detection System
"""

import os

# Project paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
FACES_DIR = os.path.join(DATA_DIR, 'faces')
IMAGES_DIR = os.path.join(DATA_DIR, 'images')
ATTENDANCE_FILE = os.path.join(DATA_DIR, 'attendance.xlsx')

# Create directories if they don't exist
for directory in [DATA_DIR, FACES_DIR, IMAGES_DIR]:
    os.makedirs(directory, exist_ok=True)

# Camera settings
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FRAMERATE = 30
USE_PI_CAMERA = True  # Set to False for USB webcam

# Face detection settings
DETECTION_SCALE_FACTOR = 1.1
DETECTION_MIN_NEIGHBORS = 5
DETECTION_MIN_SIZE = (30, 30)

# Face recognition settings
RECOGNITION_TOLERANCE = 0.6  # Lower is more strict (0.4-0.6 recommended)
MODEL = 'hog'  # Use 'hog' for Pi (faster), 'cnn' for better accuracy (slower)

# Check-in/check-out settings
CHECK_IN_COOLDOWN = 300  # Seconds before allowing another check-in (5 minutes)

# GPIO settings for access control (optional)
USE_GPIO = False  # Enable if using relay for door/box control
RELAY_PIN = 17  # GPIO pin number for relay
UNLOCK_DURATION = 3  # Seconds to keep door/box unlocked

# Display settings
SHOW_PREVIEW = True  # Show camera preview window
PREVIEW_SCALE = 0.5  # Scale factor for preview window (0.5 = 50%)

# Performance settings
PROCESS_EVERY_N_FRAMES = 2  # Process every Nth frame for better performance
