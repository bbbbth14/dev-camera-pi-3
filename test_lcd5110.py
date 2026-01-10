#!/usr/bin/env python3
"""
Test script for Nokia 5110 LCD Display
This will test the LCD 5110 connection and display functionality
"""

import time
import sys

print("=" * 50)
print("Nokia LCD 5110 Test Script")
print("=" * 50)

# Try to import the library
try:
    import adafruit_pcd8544
    import board
    import busio
    import digitalio
    from PIL import Image, ImageDraw, ImageFont
    LIBRARY = "adafruit_pcd8544"
    print(f"✓ Using {LIBRARY} library")
except ImportError:
    print("\n⚠ Adafruit PCD8544 library not found")
    print("\nTo install, run:")
    print("  sudo pip3 install adafruit-circuitpython-pcd8544")
    print("  sudo pip3 install pillow")
    sys.exit(1)

print("\nDisplay Specifications:")
print("  - Resolution: 84x48 pixels")
print("  - Type: Monochrome LCD")
print("  - Interface: SPI")

# Pin configuration
print("\n" + "=" * 50)
print("Default Pin Configuration:")
print("=" * 50)
print("  SCLK  (CLK)  -> GPIO 11 (SPI0 SCLK)")
print("  DIN   (MOSI) -> GPIO 10 (SPI0 MOSI)")
print("  DC    (Data) -> GPIO 23")
print("  RST   (Reset)-> GPIO 24")
print("  CS    (CE)   -> GPIO 8  (SPI0 CE0)")
print("  LED   (BL)   -> 3.3V (or GPIO for PWM control)")
print("  VCC          -> 3.3V")
print("  GND          -> GND")
print("=" * 50)

print("\nAttempting to initialize display...")

try:
    # Initialize SPI
    spi = busio.SPI(board.SCLK, MOSI=board.MOSI)
    
    # Setup control pins
    dc = digitalio.DigitalInOut(board.D23)    # Data/Command
    cs = digitalio.DigitalInOut(board.CE0)    # Chip Select
    reset = digitalio.DigitalInOut(board.D24) # Reset
    
    # Initialize the display
    display = adafruit_pcd8544.PCD8544(spi, dc, cs, reset)
    
    print("✓ Display initialized successfully!")
    
    # Set contrast (0-127, typically 60-80 works well)
    display.contrast = 70
    print("✓ Contrast set to 70")
    
    # Test 1: Fill screen
    print("\nTest 1: Filling screen...")
    display.fill(1)
    display.show()
    time.sleep(2)
    
    print("✓ Screen filled")
    
    # Test 2: Clear screen
    print("\nTest 2: Clearing screen...")
    display.fill(0)
    display.show()
    time.sleep(1)
    print("✓ Screen cleared")
    
    # Test 3: Draw some shapes
    print("\nTest 3: Drawing shapes...")
    image = Image.new('1', (display.width, display.height))
    draw = ImageDraw.Draw(image)
    
    # Rectangle
    draw.rectangle((0, 0, display.width-1, display.height-1), outline=1)
    draw.rectangle((2, 2, display.width-3, display.height-3), outline=1)
    
    # Lines
    draw.line((10, 10, 74, 38), fill=1)
    draw.line((74, 10, 10, 38), fill=1)
    
    display.image(image)
    display.show()
    time.sleep(2)
    print("✓ Shapes drawn")
    
    # Test 4: Display text
    print("\nTest 4: Displaying text...")
    image = Image.new('1', (display.width, display.height))
    draw = ImageDraw.Draw(image)
    
    # Try to use default font
    draw.text((0, 0), "Nokia 5110", fill=1)
    draw.text((0, 10), "LCD Test", fill=1)
    draw.text((0, 20), "84x48 px", fill=1)
    draw.text((0, 30), "OK!", fill=1)
    
    display.image(image)
    display.show()
    time.sleep(3)
    print("✓ Text displayed")
    
    # Test 5: Invert display
    print("\nTest 5: Testing invert...")
    display.invert = True
    time.sleep(1)
    display.invert = False
    time.sleep(1)
    print("✓ Invert test complete")
    
    # Test 6: Animation
    print("\nTest 6: Simple animation...")
    for i in range(10):
        image = Image.new('1', (display.width, display.height))
        draw = ImageDraw.Draw(image)
        
        # Moving circle
        x = int(i * 7.4)  # 74 / 10
        draw.ellipse((x, 14, x+20, 34), outline=1, fill=0)
        
        display.image(image)
        display.show()
        time.sleep(0.1)
    
    print("✓ Animation complete")
    
    # Final success message
    print("\n" + "=" * 50)
    image = Image.new('1', (display.width, display.height))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, display.width-1, display.height-1), outline=1)
    draw.text((10, 10), "SUCCESS!", fill=1)
    draw.text((15, 25), "LCD OK", fill=1)
    display.image(image)
    display.show()
    
    print("✅ ALL TESTS PASSED!")
    print("=" * 50)
    print("\nYour Nokia 5110 LCD is working correctly!")
    print("\nTips:")
    print("  - Adjust contrast if display is too dark/light")
    print("  - Current contrast: 70 (range: 0-127)")
    print("  - Optimal range: 60-80")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTroubleshooting:")
    print("  1. Check all wiring connections")
    print("  2. Verify 3.3V power (NOT 5V!)")
    print("  3. Enable SPI: sudo raspi-config -> Interface Options -> SPI")
    print("  4. Check pin numbers match your setup")
    print("  5. Try adjusting contrast value (60-80)")
    sys.exit(1)
