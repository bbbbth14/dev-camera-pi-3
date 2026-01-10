#!/usr/bin/env python3
"""
ST7789 Display Wiring Checker
Verifies SPI configuration and pins
"""

import sys

print("="*60)
print("ST7789 DISPLAY WIRING VERIFICATION")
print("="*60)
print()

# Check SPI enabled
print("1. Checking SPI status...")
import os
spi_devices = ['/dev/spidev0.0', '/dev/spidev0.1']
spi_enabled = any(os.path.exists(dev) for dev in spi_devices)

if spi_enabled:
    print("   ✓ SPI is ENABLED")
    for dev in spi_devices:
        if os.path.exists(dev):
            print(f"     - {dev} exists")
else:
    print("   ✗ SPI is NOT ENABLED")
    print("     Run: sudo raspi-config → Interface Options → SPI")
    sys.exit(1)

print()
print("2. ST7789 Pin Mapping:")
print("="*60)
print()
print("HARDWARE SPI PINS (Cannot be changed - hardwired):")
print("-"*60)
print("  Display Pin  │  Raspberry Pi Connection")
print("-"*60)
print("  SCL/SCK/CLK  │  GPIO 11 → Physical Pin 23 (SPI0 SCLK)")
print("  SDA/MOSI/DIN │  GPIO 10 → Physical Pin 19 (SPI0 MOSI)")
print()
print("IMPORTANT: These MUST be connected to GPIO 10 and GPIO 11!")
print("          Do NOT use any other GPIO pins for SCL/SDA!")
print()
print()
print("SOFTWARE CONTROL PINS (Can be customized):")
print("-"*60)
print("  Display Pin  │  Current Config  │  Physical Pin")
print("-"*60)
print("  CS           │  GPIO 8  (CE0)   │  Pin 24")
print("  DC/RS        │  GPIO 25         │  Pin 22")
print("  RST/RES      │  GPIO 24         │  Pin 18")
print("  BL/BLK       │  GPIO 18         │  Pin 12")
print()
print()
print("POWER PINS:")
print("-"*60)
print("  VCC/VIN      │  3.3V            │  Pin 1 or 17")
print("  GND          │  Ground          │  Pin 6, 9, 14, 20, 25, 30, 34, 39")
print()
print("="*60)
print()

# Try to import and initialize display
print("3. Testing display initialization...")
try:
    import st7789
    from PIL import Image, ImageDraw, ImageFont
    
    display = st7789.ST7789(
        rotation=90,
        port=0,       # SPI0 - uses GPIO 10 (MOSI) and GPIO 11 (SCLK) automatically
        cs=0,         # CE0 = GPIO 8
        dc=25,        # GPIO 25
        backlight=18, # GPIO 18
        rst=24,       # GPIO 24
        spi_speed_hz=80 * 1000000
    )
    
    print("   ✓ Display initialized")
    print(f"     Resolution: {display.width}x{display.height}")
    print()
    
    # Test display output
    print("4. Testing display output...")
    print("   Drawing test pattern...")
    
    # Create a simple test image with large text
    img = Image.new('RGB', (240, 240), color=(255, 0, 0))  # Red background
    draw = ImageDraw.Draw(img)
    
    # Add white text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
    except:
        font = ImageFont.load_default()
    
    draw.text((30, 90), "TEST", font=font, fill=(255, 255, 255))
    
    # Display it
    display.display(img)
    
    print("   ✓ Test image sent to display")
    print()
    print("="*60)
    print("CHECK YOUR DISPLAY NOW!")
    print("="*60)
    print()
    print("You should see:")
    print("  • RED background")
    print("  • White 'TEST' text in the center")
    print()
    print("If you see:")
    print("  ✓ Backlight ON + Image → Wiring is CORRECT")
    print("  ✗ Backlight ON only → SCL/SDA wiring issue!")
    print()
    print("Common wiring mistakes:")
    print("  • SCL connected to wrong pin (must be GPIO 11 / Pin 23)")
    print("  • SDA connected to wrong pin (must be GPIO 10 / Pin 19)")
    print("  • Loose connection on SCL or SDA")
    print("  • SCL and SDA swapped")
    print()
    
    import time
    print("Display will stay on for 10 seconds...")
    time.sleep(10)
    
    # Clear display
    img = Image.new('RGB', (240, 240), color=(0, 0, 0))
    display.display(img)
    print("✓ Test complete")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    print()
    print("Troubleshooting:")
    print("  1. Verify SPI is enabled")
    print("  2. Check all wire connections")
    print("  3. Verify SCL → GPIO 11 (Pin 23)")
    print("  4. Verify SDA → GPIO 10 (Pin 19)")
    sys.exit(1)

print()
print("="*60)
print("WIRING CHECKLIST:")
print("="*60)
print()
print("□ VCC  → 3.3V (Pin 1 or 17)")
print("□ GND  → Ground (Pin 6, 9, 14, etc.)")
print("□ SCL  → GPIO 11 (Pin 23) ★ CRITICAL ★")
print("□ SDA  → GPIO 10 (Pin 19) ★ CRITICAL ★")
print("□ CS   → GPIO 8  (Pin 24)")
print("□ DC   → GPIO 25 (Pin 22)")
print("□ RST  → GPIO 24 (Pin 18)")
print("□ BL   → GPIO 18 (Pin 12)")
print()
print("="*60)
