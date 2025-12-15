#!/bin/bash
# Install libcamera for Raspberry Pi Camera support
# Run this if you're using the Raspberry Pi Camera Module

echo "Installing libcamera for Raspberry Pi Camera..."
sudo apt-get update
sudo apt-get install -y python3-libcamera python3-picamera2

echo ""
echo "Installation complete!"
echo "The Pi Camera should now work with the system."
