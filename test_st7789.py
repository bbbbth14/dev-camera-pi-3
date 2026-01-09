#!/usr/bin/env python3
"""
Test script for ST7789 SPI Display
Tests basic functionality, colors, and text display
"""

import time
import st7789
from PIL import Image, ImageDraw, ImageFont

# Display configuration
# Common ST7789 configurations:
# - 240x240 (square display)
# - 240x320 (rectangular display)

def test_display():
    """Test ST7789 display with various patterns and colors"""
    
    print("Initializing ST7789 display...")
    
    # Create display instance
    # Adjust these parameters based on your specific display:
    # - width, height: Display resolution (240x240 or 240x320)
    # - rotation: 0, 90, 180, or 270 degrees
    # - port, cs, dc, backlight, rst: SPI and GPIO pins
    
    try:
        display = st7789.ST7789(
            rotation=90,  # Adjust rotation (0, 90, 180, 270)
            port=0,       # SPI port (SPI0)
            cs=0,         # Chip select CE0 (GPIO 8, Pin 24)
            dc=25,        # Data/Command pin (GPIO 25, Pin 22)
            backlight=18, # Backlight pin (GPIO 18, Pin 12)
            rst=24,       # Reset pin (GPIO 24, Pin 18)
            spi_speed_hz=80 * 1000000  # 80 MHz SPI speed
        )
        
        print("✓ Display initialized successfully!")
        print(f"  Resolution: {display.width}x{display.height}")
        
    except Exception as e:
        print(f"✗ Failed to initialize display: {e}")
        print("\nTroubleshooting:")
        print("1. Check SPI is enabled: sudo raspi-config → Interface Options → SPI")
        print("2. Verify wiring connections")
        print("3. Check GPIO pins match your setup")
        return False
    
    # Get display dimensions
    WIDTH = display.width
    HEIGHT = display.height
    
    print("\n" + "="*50)
    print("Starting Display Tests")
    print("="*50)
    
    # Test 1: Solid Colors
    print("\n[Test 1/6] Testing solid colors...")
    colors = [
        ("RED", (255, 0, 0)),
        ("GREEN", (0, 255, 0)),
        ("BLUE", (0, 0, 255)),
        ("YELLOW", (255, 255, 0)),
        ("CYAN", (0, 255, 255)),
        ("MAGENTA", (255, 0, 255)),
        ("WHITE", (255, 255, 255)),
        ("BLACK", (0, 0, 0))
    ]
    
    for name, color in colors:
        print(f"  Displaying {name}...")
        img = Image.new('RGB', (WIDTH, HEIGHT), color=color)
        display.display(img)
        time.sleep(0.5)
    
    print("✓ Color test complete")
    
    # Test 2: Gradient
    print("\n[Test 2/6] Testing gradient...")
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    
    for x in range(WIDTH):
        color = int((x / WIDTH) * 255)
        draw.line([(x, 0), (x, HEIGHT)], fill=(color, 0, 255 - color))
    
    display.display(img)
    time.sleep(2)
    print("✓ Gradient test complete")
    
    # Test 3: Geometric Shapes
    print("\n[Test 3/6] Testing geometric shapes...")
    img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Circle
    draw.ellipse([10, 10, 100, 100], fill=(255, 0, 0), outline=(255, 255, 255))
    # Rectangle
    draw.rectangle([120, 10, 230, 100], fill=(0, 255, 0), outline=(255, 255, 255))
    # Triangle (polygon)
    draw.polygon([(60, 120), (10, 220), (110, 220)], fill=(0, 0, 255), outline=(255, 255, 255))
    # Line
    draw.line([(120, 120), (230, 220)], fill=(255, 255, 0), width=5)
    
    display.display(img)
    time.sleep(2)
    print("✓ Shapes test complete")
    
    # Test 4: Text Display
    print("\n[Test 4/6] Testing text display...")
    img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 50, 100))
    draw = ImageDraw.Draw(img)
    
    # Try to load a font, fallback to default if not available
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    draw.text((10, 10), "ST7789 Display", font=font_large, fill=(255, 255, 255))
    draw.text((10, 50), "Test Successful!", font=font_small, fill=(0, 255, 0))
    draw.text((10, 80), f"Resolution: {WIDTH}x{HEIGHT}", font=font_small, fill=(255, 255, 0))
    draw.text((10, 110), "Raspberry Pi 3", font=font_small, fill=(255, 100, 255))
    draw.text((10, HEIGHT - 30), "SPI Display Working!", font=font_small, fill=(0, 255, 255))
    
    display.display(img)
    time.sleep(3)
    print("✓ Text test complete")
    
    # Test 5: Pattern
    print("\n[Test 5/6] Testing checkerboard pattern...")
    img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    square_size = 20
    for y in range(0, HEIGHT, square_size):
        for x in range(0, WIDTH, square_size):
            if (x // square_size + y // square_size) % 2 == 0:
                draw.rectangle([x, y, x + square_size, y + square_size], fill=(255, 255, 255))
    
    display.display(img)
    time.sleep(2)
    print("✓ Pattern test complete")
    
    # Test 6: Animation
    print("\n[Test 6/6] Testing animation (bouncing ball)...")
    ball_x, ball_y = WIDTH // 2, HEIGHT // 2
    ball_dx, ball_dy = 5, 3
    ball_radius = 15
    
    for _ in range(50):  # 50 frames
        img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 50))
        draw = ImageDraw.Draw(img)
        
        # Draw ball
        draw.ellipse([ball_x - ball_radius, ball_y - ball_radius,
                     ball_x + ball_radius, ball_y + ball_radius],
                    fill=(255, 50, 50), outline=(255, 255, 255))
        
        # Update position
        ball_x += ball_dx
        ball_y += ball_dy
        
        # Bounce off edges
        if ball_x <= ball_radius or ball_x >= WIDTH - ball_radius:
            ball_dx = -ball_dx
        if ball_y <= ball_radius or ball_y >= HEIGHT - ball_radius:
            ball_dy = -ball_dy
        
        display.display(img)
        time.sleep(0.02)
    
    print("✓ Animation test complete")
    
    # Final message
    print("\n" + "="*50)
    print("All tests completed successfully!")
    print("="*50)
    
    img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 100, 0))
    draw = ImageDraw.Draw(img)
    draw.text((WIDTH//2 - 80, HEIGHT//2 - 20), "ALL TESTS", font=font_large, fill=(255, 255, 255))
    draw.text((WIDTH//2 - 60, HEIGHT//2 + 20), "PASSED!", font=font_large, fill=(0, 255, 0))
    display.display(img)
    
    return True


def quick_test():
    """Quick test - just display a simple message"""
    print("Running quick test...")
    
    try:
        display = st7789.ST7789(
            rotation=90,
            port=0,
            cs=0,         # CE0 (GPIO 8, Pin 24)
            dc=25,        # GPIO 25, Pin 22
            backlight=18, # GPIO 18, Pin 12
            rst=24,       # GPIO 24, Pin 18
            spi_speed_hz=80 * 1000000
        )
        
        img = Image.new('RGB', (display.width, display.height), color=(0, 0, 255))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except:
            font = ImageFont.load_default()
        
        draw.text((20, display.height//2 - 20), "DISPLAY OK!", font=font, fill=(255, 255, 255))
        display.display(img)
        
        print("✓ Quick test successful!")
        return True
        
    except Exception as e:
        print(f"✗ Quick test failed: {e}")
        return False


if __name__ == "__main__":
    print("="*50)
    print("ST7789 Display Test Script")
    print("="*50)
    print("\nOptions:")
    print("1. Full test suite (recommended)")
    print("2. Quick test")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3) [default: 1]: ").strip() or "1"
    
    if choice == "1":
        test_display()
    elif choice == "2":
        quick_test()
    else:
        print("Exiting...")
