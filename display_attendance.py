#!/usr/bin/env python3
"""
Display Check-in/Check-out Times on ST7789 Screen
Shows real-time attendance status from the face recognition system
"""

import time
import argparse
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import os
import csv
from attendance_tracker import AttendanceTracker

from st7789_raw_driver import RawST7789, phys_to_bcm

# Display configuration
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 240

# Colors
BG_COLOR = (0, 30, 60)
HEADER_BG = (0, 50, 100)
TEXT_COLOR = (255, 255, 255)
STATUS_IN_COLOR = (46, 204, 113)  # Green
STATUS_OUT_COLOR = (149, 165, 166)  # Gray
TIME_COLOR = (255, 255, 100)
BORDER_COLOR = (100, 150, 200)


class AttendanceDisplay:
    """Display attendance information on ST7789 screen"""
    
    def __init__(self, args: argparse.Namespace):
        """Initialize display"""
        print("Initializing ST7789 display...")

        # Prefer the raw backend (this matches the init that worked for your panel).
        # Defaults are the known-good wiring:
        #   CS=CE0, DC=physical pin 22 (GPIO25), RST=physical pin 18 (GPIO24)
        # Backlight can be tied to 3.3V and does not need GPIO control.
        try:
            dc_gpio = phys_to_bcm(args.dc_phys) if args.dc_phys is not None else args.dc
            rst_gpio = None if args.no_rst else (phys_to_bcm(args.rst_phys) if args.rst_phys is not None else args.rst)

            self.display = RawST7789(
                port=args.port,
                cs=args.cs,
                dc=dc_gpio,
                rst=rst_gpio,
                speed=args.speed,
                spi_mode=args.spi_mode,
                width=args.width,
                height=args.height,
                offset_left=args.offset_left,
                offset_top=args.offset_top,
                rotation=args.rotation,
                invert=args.invert,
            )
            self._raw_backend = True
        except Exception as e:
            print(f"[WARNING] Raw ST7789 init failed: {e}")
            print("[INFO] Falling back to `st7789` library...")
            import st7789

            self.display = st7789.ST7789(
                width=args.width,
                height=args.height,
                rotation=args.rotation,
                port=args.port,
                cs=args.cs,
                dc=(phys_to_bcm(args.dc_phys) if args.dc_phys is not None else args.dc),
                rst=(phys_to_bcm(args.rst_phys) if args.rst_phys is not None else args.rst),
                spi_speed_hz=args.speed,
                offset_left=args.offset_left,
                offset_top=args.offset_top,
                invert=args.invert,
            )
            self._raw_backend = False
        
        # Load fonts
        try:
            self.font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            self.font_name = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            self.font_info = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            self.font_time = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
            self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            self.font_title = ImageFont.load_default()
            self.font_name = ImageFont.load_default()
            self.font_info = ImageFont.load_default()
            self.font_time = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
        
        self.tracker = AttendanceTracker()
        print("✓ Display initialized")
    
    def draw_header(self, draw):
        """Draw header section"""
        # Header background
        draw.rectangle([0, 0, DISPLAY_WIDTH, 35], fill=HEADER_BG)
        
        # Title
        draw.text((10, 8), "Attendance", font=self.font_title, fill=TEXT_COLOR)
        
        # Current time
        current_time = datetime.now().strftime("%H:%M")
        draw.text((DISPLAY_WIDTH - 60, 10), current_time, font=self.font_info, fill=TIME_COLOR)
        
        # Border line
        draw.line([0, 35, DISPLAY_WIDTH, 35], fill=BORDER_COLOR, width=2)
    
    def draw_user_status(self, draw, y_position, name, status_info):
        """Draw individual user status - simplified view"""
        # User card background
        card_height = 40
        draw.rectangle([5, y_position, DISPLAY_WIDTH - 5, y_position + card_height], 
                      fill=(20, 60, 40), outline=(46, 204, 113))
        
        # Name
        draw.text((10, y_position + 5), name[:15], font=self.font_name, fill=TEXT_COLOR)
        
        # SUCCESS badge
        draw.rectangle([DISPLAY_WIDTH - 80, y_position + 5, DISPLAY_WIDTH - 10, y_position + 22], 
                      fill=STATUS_IN_COLOR)
        draw.text((DISPLAY_WIDTH - 75, y_position + 7), "SUCCESS", font=self.font_small, fill=(255, 255, 255))
        
        # Time (last activity time)
        time_text = status_info.get('last_time', 'N/A')
        draw.text((10, y_position + 24), f"Time: {time_text}", font=self.font_time, fill=TIME_COLOR)
    
    def update_display(self):
        """Update display with current attendance data"""
        # Create new image
        img = Image.new('RGB', (DISPLAY_WIDTH, DISPLAY_HEIGHT), color=BG_COLOR)
        draw = ImageDraw.Draw(img)
        
        # Draw header
        self.draw_header(draw)
        
        # Get user status
        user_status = self.tracker.get_user_status()
        
        if not user_status:
            # No users message
            draw.text((DISPLAY_WIDTH // 2 - 40, DISPLAY_HEIGHT // 2), 
                     "No users yet", font=self.font_info, fill=(150, 150, 150))
        else:
            # Display users (max 5 visible at once)
            y_pos = 40
            count = 0
            max_users = 5
            
            # Sort by most recent activity
            def _sort_key(item):
                info = item[1] or {}
                # last_time can exist but be None -> keep key always comparable
                return info.get('last_time') or ''

            sorted_users = sorted(user_status.items(), key=_sort_key, reverse=True)
            
            for name, status_info in sorted_users[:max_users]:
                self.draw_user_status(draw, y_pos, name, status_info)
                y_pos += 45
                count += 1
            
            # Show total if more users exist
            if len(user_status) > max_users:
                remaining = len(user_status) - max_users
                draw.text((10, DISPLAY_HEIGHT - 15), 
                         f"+{remaining} more", font=self.font_small, fill=(150, 150, 150))
        
        # Display update time
        update_time = datetime.now().strftime("%H:%M:%S")
        draw.text((DISPLAY_WIDTH - 60, DISPLAY_HEIGHT - 15), 
                 update_time, font=self.font_small, fill=(100, 100, 100))
        
        # Update display
        self.display.display(img)
    
    def run(self, update_interval=2):
        """Run display loop"""
        print(f"\nStarting attendance display...")
        print(f"Update interval: {update_interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.update_display()
                time.sleep(update_interval)
                
        except KeyboardInterrupt:
            print("\n\nStopping display...")
            
            # Show goodbye message
            img = Image.new('RGB', (DISPLAY_WIDTH, DISPLAY_HEIGHT), color=(0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((DISPLAY_WIDTH // 2 - 50, DISPLAY_HEIGHT // 2 - 10), 
                     "Display Off", font=self.font_title, fill=TEXT_COLOR)
            self.display.display(img)
            
            print("✓ Display stopped")


def main():
    """Main entry point"""
    print("="*50)
    print("ST7789 Attendance Display")
    print("="*50)

    parser = argparse.ArgumentParser(description="ST7789 Attendance Display")
    parser.add_argument("--update-interval", type=float, default=2.0)

    # SPI
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--cs", type=int, default=0, choices=[0, 1])
    parser.add_argument("--speed", type=int, default=4_000_000)
    parser.add_argument("--spi-mode", type=int, default=0, choices=[0, 1, 2, 3])

    # Panel
    parser.add_argument("--width", type=int, default=240)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--offset-left", type=int, default=0)
    parser.add_argument("--offset-top", type=int, default=0)
    parser.add_argument("--rotation", type=int, default=90, choices=[0, 90, 180, 270])

    inv = parser.add_mutually_exclusive_group()
    inv.add_argument("--invert", dest="invert", action="store_true")
    inv.add_argument("--no-invert", dest="invert", action="store_false")
    parser.set_defaults(invert=True)

    # GPIO
    parser.add_argument("--dc", type=int, default=25, help="BCM GPIO")
    parser.add_argument("--rst", type=int, default=24, help="BCM GPIO")
    parser.add_argument("--no-rst", action="store_true")
    parser.add_argument("--dc-phys", type=int, default=22, help="physical pin for DC (default: 22)")
    parser.add_argument("--rst-phys", type=int, default=18, help="physical pin for RST (default: 18)")

    args = parser.parse_args()

    display = AttendanceDisplay(args)
    display.run(update_interval=args.update_interval)


if __name__ == "__main__":
    main()
