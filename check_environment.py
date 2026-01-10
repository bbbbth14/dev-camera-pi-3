#!/usr/bin/env python3
"""
ST7789 Environment Checker
Verifies all software requirements are met
"""

import sys
import os

print("="*70)
print("ST7789 ENVIRONMENT VERIFICATION")
print("="*70)
print()

issues = []
warnings = []

# 1. Check SPI enabled
print("1. Checking SPI Interface...")
if os.path.exists('/dev/spidev0.0'):
    print("   ✓ SPI is enabled (/dev/spidev0.0 exists)")
else:
    print("   ✗ SPI is NOT enabled")
    issues.append("Enable SPI: sudo raspi-config → Interface Options → SPI")

# 2. Check kernel modules
print("\n2. Checking SPI kernel modules...")
try:
    with open('/proc/modules', 'r') as f:
        modules = f.read()
    
    if 'spi_bcm' in modules:
        print("   ✓ spi_bcm2835 module loaded")
    else:
        print("   ⚠ spi_bcm2835 not loaded")
        warnings.append("SPI kernel module may not be loaded")
    
    if 'spidev' in modules:
        print("   ✓ spidev module loaded")
    else:
        print("   ⚠ spidev not loaded")
except:
    print("   ⚠ Could not check modules")

# 3. Check Python packages
print("\n3. Checking Python packages...")
packages = {
    'st7789': 'ST7789 driver',
    'PIL': 'Pillow (image library)',
    'spidev': 'SPI device interface',
    'numpy': 'NumPy',
}

for pkg, name in packages.items():
    try:
        if pkg == 'PIL':
            from PIL import Image
        else:
            __import__(pkg)
        print(f"   ✓ {name}")
    except ImportError:
        print(f"   ✗ {name} - NOT INSTALLED")
        issues.append(f"Install {pkg}: pip3 install {pkg} --break-system-packages")

# 4. Check SPI permissions
print("\n4. Checking SPI device permissions...")
try:
    import stat
    st = os.stat('/dev/spidev0.0')
    mode = st.st_mode
    print(f"   /dev/spidev0.0 permissions: {oct(stat.S_IMODE(mode))}")
    
    # Check if readable/writable
    if os.access('/dev/spidev0.0', os.R_OK | os.W_OK):
        print("   ✓ SPI device is readable and writable")
    else:
        print("   ✗ No permission to access SPI device")
        issues.append("Add user to spi group: sudo usermod -a -G spi $USER")
except Exception as e:
    print(f"   ⚠ Could not check permissions: {e}")

# 5. Check SPI configuration
print("\n5. Checking SPI configuration...")
try:
    import spidev
    spi = spidev.SpiDev()
    spi.open(0, 0)
    
    print(f"   ✓ Can open SPI device")
    print(f"   Max speed: {spi.max_speed_hz} Hz")
    print(f"   Mode: {spi.mode}")
    print(f"   Bits per word: {spi.bits_per_word}")
    
    spi.close()
except Exception as e:
    print(f"   ✗ Cannot open SPI device: {e}")
    issues.append("SPI device cannot be opened")

# 6. Test actual ST7789 initialization
print("\n6. Testing ST7789 initialization...")
try:
    import st7789
    from PIL import Image, ImageDraw
    
    display = st7789.ST7789(
        rotation=90,
        port=0,
        cs=0,
        dc=25,
        backlight=18,
        rst=24,
        spi_speed_hz=80 * 1000000
    )
    
    print(f"   ✓ ST7789 initialized successfully")
    print(f"   Display size: {display.width}x{display.height}")
    
    # Try to send data to display
    print("\n7. Testing data transfer to display...")
    img = Image.new('RGB', (240, 240), color=(255, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 190, 190], fill=(255, 255, 255))
    
    display.display(img)
    print("   ✓ Data sent to display")
    print("\n   CHECK YOUR DISPLAY NOW:")
    print("   You should see a RED screen with WHITE square")
    print("   (This will stay for 5 seconds)")
    
    import time
    time.sleep(5)
    
    # Clear
    img = Image.new('RGB', (240, 240), color=(0, 0, 0))
    display.display(img)
    
except Exception as e:
    print(f"   ✗ ST7789 initialization failed: {e}")
    issues.append(f"ST7789 error: {e}")

# 8. Check boot config
print("\n8. Checking boot configuration...")
try:
    with open('/boot/firmware/config.txt', 'r') as f:
        config = f.read()
    
    if 'dtparam=spi=on' in config:
        print("   ✓ SPI enabled in /boot/firmware/config.txt")
    else:
        print("   ⚠ SPI not explicitly enabled in config.txt")
        warnings.append("Add 'dtparam=spi=on' to /boot/firmware/config.txt")
except FileNotFoundError:
    try:
        with open('/boot/config.txt', 'r') as f:
            config = f.read()
        if 'dtparam=spi=on' in config:
            print("   ✓ SPI enabled in /boot/config.txt")
        else:
            print("   ⚠ SPI not explicitly enabled in config.txt")
    except:
        print("   ⚠ Could not check boot config")

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

if not issues and not warnings:
    print("\n✓ ALL CHECKS PASSED - Software environment is correct!")
    print("\nIf display still shows only backlight:")
    print("  → Problem is HARDWARE wiring (SCL/SDA pins)")
    print("  → Double-check Pin 19 (SDA) and Pin 23 (SCL)")
else:
    if issues:
        print("\n✗ CRITICAL ISSUES FOUND:")
        for issue in issues:
            print(f"  • {issue}")
    
    if warnings:
        print("\n⚠ WARNINGS:")
        for warning in warnings:
            print(f"  • {warning}")

print("\n" + "="*70)
