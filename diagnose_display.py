#!/usr/bin/env python3
"""
ST7789 Display Diagnostic Tool
Checks hardware, software, and configuration issues
"""

import sys
import time

def check_spi():
    """Check if SPI is enabled"""
    print("1. Checking SPI interface...")
    try:
        import os
        if os.path.exists('/dev/spidev0.0'):
            print("   ✓ SPI is enabled (/dev/spidev0.0 exists)")
            return True
        else:
            print("   ✗ SPI not found")
            print("   → Run: sudo raspi-config → Interface Options → SPI")
            return False
    except Exception as e:
        print(f"   ✗ Error checking SPI: {e}")
        return False

def check_libraries():
    """Check required libraries"""
    print("\n2. Checking Python libraries...")
    
    libs = ['st7789', 'PIL', 'spidev', 'gpiod']
    all_ok = True
    
    for lib in libs:
        try:
            if lib == 'PIL':
                from PIL import Image
            else:
                __import__(lib)
            print(f"   ✓ {lib} installed")
        except ImportError:
            print(f"   ✗ {lib} NOT installed")
            all_ok = False
    
    return all_ok

def check_gpio_permissions():
    """Check GPIO access permissions"""
    print("\n3. Checking GPIO permissions...")
    try:
        import gpiod
        print("   ✓ gpiod accessible")
        return True
    except Exception as e:
        print(f"   ✗ GPIO access error: {e}")
        print("   → You may need to add user to gpio group:")
        print("   → sudo usermod -a -G gpio $USER")
        return False

def test_display_init():
    """Test display initialization"""
    print("\n4. Testing display initialization...")
    try:
        import st7789
        display = st7789.ST7789(
            rotation=90,
            port=0,
            cs=0,
            dc=25,
            backlight=18,
            rst=24,
            spi_speed_hz=80 * 1000000
        )
        print(f"   ✓ Display initialized successfully")
        print(f"   → Size: {display.width}x{display.height}")
        return display
    except Exception as e:
        print(f"   ✗ Failed to initialize: {e}")
        return None

def test_display_output(display):
    """Test visible output"""
    print("\n5. Testing visible output...")
    print("   Running color sequence test...")
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        colors = [
            ((255, 255, 255), "WHITE"),
            ((255, 0, 0), "RED"),
            ((0, 255, 0), "GREEN"),
            ((0, 0, 255), "BLUE"),
            ((255, 255, 0), "YELLOW"),
        ]
        
        print("\n   WATCH YOUR DISPLAY NOW!")
        print("   Colors will change every 2 seconds")
        print()
        
        for color, name in colors:
            img = Image.new('RGB', (display.width, display.height), color=color)
            draw = ImageDraw.Draw(img)
            
            # Add text
            try:
                font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 40)
            except:
                font = ImageFont.load_default()
            
            # Contrasting text color
            text_color = (0, 0, 0) if name == "WHITE" or name == "YELLOW" else (255, 255, 255)
            draw.text((30, 100), name, font=font, fill=text_color)
            
            display.display(img)
            print(f"   → Showing {name}")
            time.sleep(2)
        
        # Final black screen
        img = Image.new('RGB', (display.width, display.height), color=(0, 0, 0))
        display.display(img)
        
        print()
        response = input("   Did you see the colors change? (y/n): ").strip().lower()
        
        if response == 'y':
            print("   ✓ Display is working correctly!")
            return True
        else:
            print("   ✗ Display not showing content")
            return False
            
    except Exception as e:
        print(f"   ✗ Error during output test: {e}")
        return False

def test_different_rotations(display):
    """Test different rotations"""
    print("\n6. Testing different rotations...")
    print("   If display appears blank, it might be the wrong rotation")
    print()
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        import st7789
        
        rotations = [0, 90, 180, 270]
        
        for rot in rotations:
            print(f"   Testing rotation: {rot}°")
            
            # Reinitialize with new rotation
            test_disp = st7789.ST7789(
                rotation=rot,
                port=0,
                cs=0,
                dc=25,
                backlight=18,
                rst=24,
                spi_speed_hz=80 * 1000000
            )
            
            # Show colored screen with rotation label
            img = Image.new('RGB', (test_disp.width, test_disp.height), color=(0, 100, 200))
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30)
            except:
                font = ImageFont.load_default()
            
            draw.text((20, test_disp.height//2 - 20), f"{rot}°", font=font, fill=(255, 255, 255))
            test_disp.display(img)
            
            time.sleep(3)
        
        print("\n   Which rotation looked correct?")
        print("   (Current default is 90°)")
        
    except Exception as e:
        print(f"   ✗ Error during rotation test: {e}")

def check_hardware_connections():
    """Display wiring information"""
    print("\n7. Hardware Connection Check")
    print("   =====================================")
    print("   Expected ST7789 wiring:")
    print("   =====================================")
    print("   VCC     → 3.3V (Pin 1 or 17)")
    print("   GND     → Ground (Pin 6, 9, 14, etc.)")
    print("   SCL/SCK → GPIO 11 (Pin 23) [SPI0 SCLK]")
    print("   SDA/MOSI→ GPIO 10 (Pin 19) [SPI0 MOSI]")
    print("   RES/RST → GPIO 24 (Pin 18)")
    print("   DC/RS   → GPIO 25 (Pin 22)")
    print("   CS      → GPIO 8  (Pin 24) [CE0]")
    print("   BL/BLK  → GPIO 18 (Pin 12)")
    print("   =====================================")
    print()
    print("   Double-check:")
    print("   • All pins are firmly connected")
    print("   • No loose wires")
    print("   • Display is powered (backlight on)")
    print()

def main():
    """Run all diagnostics"""
    print("="*60)
    print("ST7789 DISPLAY DIAGNOSTIC TOOL")
    print("="*60)
    print()
    
    results = {}
    
    # Run checks
    results['spi'] = check_spi()
    results['libraries'] = check_libraries()
    results['gpio'] = check_gpio_permissions()
    
    # Try to initialize display
    display = test_display_init()
    results['init'] = display is not None
    
    if display:
        # Test output
        results['output'] = test_display_output(display)
        
        if not results['output']:
            test_different_rotations(display)
    
    # Show hardware info
    check_hardware_connections()
    
    # Summary
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    
    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{check.upper():<15} {status}")
    
    print("="*60)
    
    if all(results.values()):
        print("\n✓ All checks passed! Display should be working.")
    else:
        print("\n✗ Some checks failed. Review the output above.")
        print("\nCommon issues:")
        print("1. Wrong rotation setting")
        print("2. Loose wire connections")
        print("3. SPI not enabled")
        print("4. Incorrect GPIO pin configuration")
        print("5. Display contrast too low (hardware issue)")

if __name__ == "__main__":
    main()
