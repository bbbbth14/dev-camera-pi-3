#!/usr/bin/env python3
"""
Compare test_st7789 vs display_attendance rendering
"""

import time
import st7789
from PIL import Image, ImageDraw, ImageFont

print("="*60)
print("ST7789 DISPLAY COMPARISON TEST")
print("="*60)
print()

# Initialize display
print("1. Initializing display...")
display = st7789.ST7789(
    rotation=90,
    port=0,
    cs=0,
    dc=25,
    backlight=18,
    rst=24,
    spi_speed_hz=80 * 1000000
)
print(f"   ✓ Display ready: {display.width}x{display.height}")
print()

# Test 1: Simple solid colors (like test_st7789.py)
print("2. Test simple colors (like test_st7789.py)")
print("   Watch your display...")
colors = [
    ((255, 0, 0), "RED"),
    ((0, 255, 0), "GREEN"),
    ((0, 0, 255), "BLUE"),
]

for color, name in colors:
    img = Image.new('RGB', (display.width, display.height), color=color)
    display.display(img)
    print(f"   → {name}")
    time.sleep(2)

print()

# Test 2: Replicate display_attendance style
print("3. Test attendance-style display")
print("   This mimics display_attendance.py layout...")

# Colors from display_attendance.py
BG_COLOR = (0, 30, 60)
HEADER_BG = (0, 50, 100)
TEXT_COLOR = (255, 255, 255)
STATUS_IN_COLOR = (46, 204, 113)
TIME_COLOR = (255, 255, 100)
BORDER_COLOR = (100, 150, 200)

# Create image like display_attendance
img = Image.new('RGB', (display.width, display.height), color=BG_COLOR)
draw = ImageDraw.Draw(img)

# Load fonts
try:
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    font_name = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
except:
    font_title = ImageFont.load_default()
    font_name = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Header background
draw.rectangle([0, 0, display.width, 35], fill=HEADER_BG)
draw.text((10, 8), "Attendance", font=font_title, fill=TEXT_COLOR)
draw.text((display.width - 60, 10), "10:00", font=font_small, fill=TIME_COLOR)
draw.line([0, 35, display.width, 35], fill=BORDER_COLOR, width=2)

# User card
card_y = 40
draw.rectangle([5, card_y, display.width - 5, card_y + 40], 
              fill=(20, 60, 40), outline=(46, 204, 113))
draw.text((10, card_y + 5), "Linh", font=font_name, fill=TEXT_COLOR)
draw.rectangle([display.width - 80, card_y + 5, display.width - 10, card_y + 22], 
              fill=STATUS_IN_COLOR)
draw.text((display.width - 75, card_y + 7), "SUCCESS", font=font_small, fill=(255, 255, 255))
draw.text((10, card_y + 24), "Time: 09:18:51", font=font_small, fill=TIME_COLOR)

# Display it
display.display(img)
print("   ✓ Attendance layout displayed")
print()
print("   You should see:")
print("   - Dark blue header with 'Attendance'")
print("   - Green card with 'Linh' and 'SUCCESS' badge")
print("   - Yellow time text")
print()

time.sleep(10)

# Test 3: Very simple high-contrast test
print("4. Final test: High contrast")
img = Image.new('RGB', (display.width, display.height), color=(255, 255, 255))
draw = ImageDraw.Draw(img)

try:
    big_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
except:
    big_font = ImageFont.load_default()

draw.text((30, 100), "WORKING", font=big_font, fill=(0, 0, 0))
display.display(img)
print("   → White screen with 'WORKING' text")
time.sleep(5)

# Clear
img = Image.new('RGB', (display.width, display.height), color=(0, 0, 0))
display.display(img)

print()
print("="*60)
print("TEST COMPLETE")
print("="*60)
print()
print("QUESTIONS:")
print("1. Did you see the RED, GREEN, BLUE colors? (Test 2)")
print("2. Did you see the attendance layout with Linh? (Test 3)")
print("3. Did you see the white 'WORKING' text? (Test 4)")
print()
print("If YES to all: Display driver is working correctly!")
print("If NO to some: There may be a rendering or timing issue")
print()
