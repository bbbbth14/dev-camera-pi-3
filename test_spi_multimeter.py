#!/usr/bin/env python3
"""
SPI Pin Tester for Multimeter
Continuously sends data to SPI to create measurable signals
"""

import time
import spidev
from PIL import Image
import st7789

print("="*70)
print("SPI PIN TESTER - FOR MULTIMETER MEASUREMENT")
print("="*70)
print()

print("This script will continuously send data to the ST7789 display.")
print("Use your multimeter to measure voltage on the pins.")
print()
print("Press Ctrl+C to stop")
print()
print("-"*70)

# Initialize SPI and display
try:
    display = st7789.ST7789(
        rotation=90,
        port=0,
        cs=0,
        dc=25,
        backlight=18,
        rst=24,
        spi_speed_hz=10 * 1000000  # Slow speed for easier measurement
    )
    print("✓ Display initialized")
    print()
except Exception as e:
    print(f"✗ Failed to initialize: {e}")
    exit(1)

print("NOW MEASURING SPI ACTIVITY...")
print()
print("Use your multimeter in DC Voltage mode:")
print()
print("1. Set multimeter to DC Voltage (20V range)")
print("2. Connect BLACK probe to Raspberry Pi GND (Pin 6, 9, 14, etc.)")
print("3. Touch RED probe to pins below and note the readings:")
print()

colors = [
    (255, 0, 0),    # Red
    (0, 255, 0),    # Green
    (0, 0, 255),    # Blue
    (255, 255, 0),  # Yellow
    (255, 0, 255),  # Magenta
    (0, 255, 255),  # Cyan
]

color_idx = 0

try:
    iteration = 0
    while True:
        iteration += 1
        
        # Cycle through colors
        color = colors[color_idx % len(colors)]
        color_idx += 1
        
        # Create and display image (this sends SPI data)
        img = Image.new('RGB', (240, 240), color=color)
        display.display(img)
        
        if iteration % 10 == 1:
            print(f"\n[Iteration {iteration}] Sending data...")
            print(f"  Color: RGB{color}")
            print()
            print("  MEASURE THESE PINS NOW:")
            print("  ┌─────────────────────────────────────────────┐")
            print("  │ Pin │ GPIO │ Signal │ Expected Reading     │")
            print("  ├─────────────────────────────────────────────┤")
            print("  │ 23  │  11  │  SCL   │ Fluctuating 0-3.3V  │")
            print("  │ 19  │  10  │  SDA   │ Fluctuating 0-3.3V  │")
            print("  │ 24  │   8  │  CS    │ Toggles 0V/3.3V     │")
            print("  │ 22  │  25  │  DC    │ Toggles 0V/3.3V     │")
            print("  │ 18  │  24  │  RST   │ Steady ~3.3V        │")
            print("  │ 12  │  18  │  BL    │ Steady ~3.3V        │")
            print("  └─────────────────────────────────────────────┘")
        
        time.sleep(0.5)  # Half second delay

except KeyboardInterrupt:
    print("\n\n" + "="*70)
    print("MEASUREMENT COMPLETE")
    print("="*70)
    print()
    print("DIAGNOSIS:")
    print()
    print("Pin 23 (SCL) readings:")
    print("  ✓ Fluctuating voltage → SPI clock is working")
    print("  ✗ Stuck at 0V or 3.3V → Problem with SCL connection")
    print()
    print("Pin 19 (SDA) readings:")
    print("  ✓ Fluctuating voltage → SPI data is working")
    print("  ✗ Stuck at 0V or 3.3V → Problem with SDA connection")
    print()
    print("If BOTH SCL and SDA are fluctuating:")
    print("  → SPI is working correctly")
    print("  → Problem is with display or other connections")
    print()
    print("If SCL or SDA stuck at constant voltage:")
    print("  → That pin has a wiring problem")
    print("  → Check connection from Pi to display")
    print()
