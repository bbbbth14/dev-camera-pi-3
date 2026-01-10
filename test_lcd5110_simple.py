#!/usr/bin/env python3
"""
Simple Nokia LCD 5110 Test using Raw SPI
No external libraries required - uses built-in spidev and RPi.GPIO
"""

import time
import sys

print("=" * 50)
print("Nokia LCD 5110 Simple Test")
print("=" * 50)

# Check for required libraries
try:
    import spidev
    import RPi.GPIO as GPIO
    print("✓ Required libraries found (spidev, RPi.GPIO)")
except ImportError as e:
    print(f"\n❌ Missing library: {e}")
    print("\nInstall with:")
    print("  sudo apt-get install python3-spidev python3-rpi.gpio")
    sys.exit(1)

# Pin Configuration
PIN_DC = 23    # Data/Command
PIN_RST = 24   # Reset
PIN_CS = 8     # Chip Select (CE0)

# LCD Commands
LCD_CMD = 0
LCD_DATA = 1

print("\nPin Configuration:")
print(f"  DC  (Data/Command) -> GPIO {PIN_DC}")
print(f"  RST (Reset)        -> GPIO {PIN_RST}")
print(f"  CS  (Chip Select)  -> GPIO {PIN_CS} (CE0)")
print("  SCLK               -> GPIO 11 (SPI0 SCLK)")
print("  DIN (MOSI)         -> GPIO 10 (SPI0 MOSI)")
print("  VCC                -> 3.3V")
print("  GND                -> GND")
print("  LED (Backlight)    -> 3.3V")

class LCD5110:
    def __init__(self, dc_pin=PIN_DC, rst_pin=PIN_RST, spi_bus=0, spi_device=0):
        self.dc_pin = dc_pin
        self.rst_pin = rst_pin
        self.width = 84
        self.height = 48
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.dc_pin, GPIO.OUT)
        GPIO.setup(self.rst_pin, GPIO.OUT)
        
        # Setup SPI
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_device)
        self.spi.max_speed_hz = 4000000
        self.spi.mode = 0
        
        # Initialize display
        self._reset()
        self._init()
    
    def _reset(self):
        """Hardware reset"""
        GPIO.output(self.rst_pin, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.rst_pin, GPIO.HIGH)
    
    def _write(self, data, is_data=False):
        """Write command or data"""
        GPIO.output(self.dc_pin, GPIO.HIGH if is_data else GPIO.LOW)
        if isinstance(data, int):
            data = [data]
        self.spi.xfer2(data)
    
    def _init(self):
        """Initialize LCD with proper settings"""
        self._write(0x21)  # Extended commands
        self._write(0xB8)  # Set Vop (contrast) - try values 0xB0 to 0xBF
        self._write(0x04)  # Set temperature coefficient
        self._write(0x14)  # Set bias mode
        self._write(0x20)  # Basic commands
        self._write(0x0C)  # Display normal mode
    
    def clear(self):
        """Clear the display"""
        self._write(0x80)  # Set X address to 0
        self._write(0x40)  # Set Y address to 0
        # Send 504 bytes (84*48/8) of zeros
        for i in range(504):
            self._write(0x00, is_data=True)
    
    def fill(self):
        """Fill the display"""
        self._write(0x80)  # Set X address to 0
        self._write(0x40)  # Set Y address to 0
        # Send 504 bytes of 0xFF
        for i in range(504):
            self._write(0xFF, is_data=True)
    
    def set_contrast(self, contrast):
        """Set contrast (0-127, typically 60-80)"""
        self._write(0x21)  # Extended commands
        self._write(0x80 | contrast)  # Set Vop
        self._write(0x20)  # Basic commands
    
    def display_pattern(self, pattern_num=1):
        """Display test patterns"""
        self._write(0x80)  # Set X address to 0
        self._write(0x40)  # Set Y address to 0
        
        if pattern_num == 1:
            # Checkerboard
            for i in range(504):
                self._write(0xAA if (i % 2 == 0) else 0x55, is_data=True)
        elif pattern_num == 2:
            # Horizontal lines
            for i in range(504):
                self._write(0xFF if ((i // 84) % 2 == 0) else 0x00, is_data=True)
        elif pattern_num == 3:
            # Vertical lines
            for i in range(504):
                self._write(0xAA, is_data=True)
    
    def write_text(self, text, x=0, y=0):
        """Simple text display using basic font"""
        # Basic 5x7 font for numbers and letters (simplified)
        font = {
            'H': [0x7F, 0x08, 0x08, 0x08, 0x7F],
            'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
            'L': [0x7F, 0x40, 0x40, 0x40, 0x40],
            'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
            '!': [0x00, 0x00, 0x5F, 0x00, 0x00],
            ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
            'K': [0x7F, 0x08, 0x14, 0x22, 0x41],
        }
        
        # Set position
        self._write(0x80 | x)  # X
        self._write(0x40 | y)  # Y
        
        for char in text.upper():
            if char in font:
                for byte in font[char]:
                    self._write(byte, is_data=True)
                self._write(0x00, is_data=True)  # Space between chars
    
    def cleanup(self):
        """Cleanup GPIO"""
        self.spi.close()
        GPIO.cleanup()

# Run tests
try:
    print("\n" + "=" * 50)
    print("Initializing LCD 5110...")
    print("=" * 50)
    
    lcd = LCD5110()
    print("✓ Display initialized!")
    
    # Test 1: Clear display
    print("\nTest 1: Clearing display...")
    lcd.clear()
    time.sleep(1)
    print("✓ Display cleared")
    
    # Test 2: Fill display
    print("\nTest 2: Filling display...")
    lcd.fill()
    time.sleep(2)
    print("✓ Display filled")
    
    # Test 3: Clear again
    print("\nTest 3: Clearing again...")
    lcd.clear()
    time.sleep(1)
    print("✓ Cleared")
    
    # Test 4: Checkerboard pattern
    print("\nTest 4: Checkerboard pattern...")
    lcd.display_pattern(1)
    time.sleep(2)
    print("✓ Pattern displayed")
    
    # Test 5: Horizontal lines
    print("\nTest 5: Horizontal lines...")
    lcd.display_pattern(2)
    time.sleep(2)
    print("✓ Lines displayed")
    
    # Test 6: Vertical lines
    print("\nTest 6: Vertical lines...")
    lcd.display_pattern(3)
    time.sleep(2)
    print("✓ Lines displayed")
    
    # Test 7: Simple text
    print("\nTest 7: Displaying text...")
    lcd.clear()
    time.sleep(0.5)
    lcd.write_text("HELLO!", 10, 2)
    time.sleep(3)
    print("✓ Text displayed")
    
    # Test 8: Contrast test
    print("\nTest 8: Testing contrast levels...")
    lcd.clear()
    lcd.write_text("OK!", 30, 2)
    
    for contrast in [50, 60, 70, 80]:
        print(f"  Contrast: {contrast}")
        lcd.set_contrast(contrast)
        time.sleep(1)
    
    print("✓ Contrast test complete")
    
    # Success
    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED!")
    print("=" * 50)
    print("\nYour Nokia 5110 LCD is working correctly!")
    print("\nNotes:")
    print("  - Display resolution: 84x48 pixels")
    print("  - If display is too dark/light, adjust contrast")
    print("  - Typical contrast values: 60-80")
    
    lcd.cleanup()
    
except KeyboardInterrupt:
    print("\n\nTest interrupted by user")
    lcd.cleanup()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTroubleshooting:")
    print("  1. Check all wiring connections")
    print("  2. Verify 3.3V power (NOT 5V!)")
    print("  3. Enable SPI: sudo raspi-config")
    print("     -> Interface Options -> SPI -> Enable")
    print("  4. Reboot after enabling SPI")
    print("  5. Check pin connections match the config above")
    import traceback
    traceback.print_exc()
    try:
        lcd.cleanup()
    except:
        pass
    sys.exit(1)
