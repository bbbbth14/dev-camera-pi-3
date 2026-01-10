#!/bin/bash
echo "===================================="
echo "Nokia LCD 5110 Setup Script"
echo "===================================="

# Enable SPI
echo ""
echo "Step 1: Enabling SPI interface..."
sudo raspi-config nonint do_spi 0
echo "✓ SPI enabled"

# Install Python dependencies
echo ""
echo "Step 2: Installing Python libraries..."
sudo pip3 install adafruit-circuitpython-pcd8544
sudo pip3 install pillow
echo "✓ Libraries installed"

echo ""
echo "===================================="
echo "Setup Complete!"
echo "===================================="
echo ""
echo "To test your LCD 5110, run:"
echo "  python3 test_lcd5110.py"
echo ""
