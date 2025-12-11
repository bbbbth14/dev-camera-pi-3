#!/bin/bash

# Installation script for Face Recognition System on Raspberry Pi
# Run this script with: bash install.sh

echo "================================================"
echo "Face Recognition System - Installation Script"
echo "================================================"
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "WARNING: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Step 1: Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

echo ""
echo "Step 2: Installing system dependencies..."
sudo apt-get install -y python3-pip python3-dev cmake
sudo apt-get install -y libopenblas-dev liblapack-dev libjpeg-dev
sudo apt-get install -y libatlas-base-dev gfortran
sudo apt-get install -y python3-opencv
sudo apt-get install -y libhdf5-dev libhdf5-serial-dev
sudo apt-get install -y libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5
sudo apt-get install -y libharfbuzz0b libwebp6 libtiff5 libjasper1
sudo apt-get install -y libilmbase23 libopenexr23 libgstreamer1.0-0
sudo apt-get install -y libavcodec58 libavformat58 libswscale5

echo ""
echo "Step 3: Upgrading pip..."
pip3 install --upgrade pip

echo ""
echo "Step 4: Installing Python packages..."
echo "This may take 15-30 minutes on Raspberry Pi 3..."

# Install numpy first (required for other packages)
pip3 install numpy==1.24.3

# Install OpenCV
pip3 install opencv-python==4.8.1.78
pip3 install opencv-contrib-python==4.8.1.78

# Install dlib (this takes the longest)
echo "Installing dlib (this may take 10-20 minutes)..."
pip3 install dlib==19.24.0

# Install face_recognition
pip3 install face-recognition==1.3.0

# Install other dependencies
pip3 install Pillow==10.0.0

# Install picamera2 for Pi Camera support
echo ""
echo "Step 5: Installing Pi Camera support..."
sudo apt-get install -y python3-picamera2

echo ""
echo "Step 6: Enabling camera interface..."
echo "Please enable the camera interface if not already enabled:"
echo "  sudo raspi-config"
echo "  Navigate to: Interface Options -> Camera -> Enable"
read -p "Press Enter to continue after enabling the camera..."

echo ""
echo "Step 7: Creating data directories..."
mkdir -p data/faces
mkdir -p data/images

echo ""
echo "================================================"
echo "Installation Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Reboot your Raspberry Pi: sudo reboot"
echo "2. Enroll faces: python3 enroll_face.py --name 'Your Name'"
echo "3. Run the system: python3 main.py"
echo ""
echo "For more information, see README.md"
