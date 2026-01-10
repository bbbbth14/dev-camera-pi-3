#!/usr/bin/env python3
"""
Try lower SPI speed - some displays can't handle 80MHz
"""
import st7789
from PIL import Image, ImageDraw, ImageFont
import time

speeds = [
    (10 * 1000000, "10 MHz - Very Slow"),
    (20 * 1000000, "20 MHz - Slow"),
    (40 * 1000000, "40 MHz - Medium"),
    (80 * 1000000, "80 MHz - Fast"),
]

print("="*60)
print("Testing different SPI speeds...")
print("="*60)
print()

for speed, desc in speeds:
    print(f"Testing {desc}...")
    
    try:
        display = st7789.ST7789(
            rotation=90,
            port=0,
            cs=0,
            dc=25,
            backlight=18,
            rst=24,
            spi_speed_hz=speed
        )
        
        # Draw test image
        img = Image.new('RGB', (240, 240), color=(0, 255, 0))  # Green
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
        except:
            font = ImageFont.load_default()
        
        draw.text((60, 100), desc.split('-')[0].strip(), 
                 font=font, fill=(255, 255, 255))
        
        display.display(img)
        
        print(f"  → Image sent")
        print(f"  → Check display for GREEN screen")
        print()
        time.sleep(3)
        
    except Exception as e:
        print(f"  → Failed: {e}")
        print()

print("Test complete. Did any speed show an image?")
