#!/usr/bin/env python3
"""
Display Check-in/Check-out Times on ST7789 Screen
Shows real-time attendance status from the face recognition system
"""

import time
import st7789
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import os
import csv
from attendance_tracker import AttendanceTracker

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
    
    def __init__(self):
        """Initialize display"""
        print("Initializing ST7789 display...")
        
        # Initialize display with correct pins
        self.display = st7789.ST7789(
            rotation=90,
            port=0,
            cs=0,         # CE0 (GPIO 8, Pin 24)
            dc=25,        # GPIO 25, Pin 22
            backlight=18, # GPIO 18, Pin 12
            rst=24,       # GPIO 24, Pin 18
            spi_speed_hz=80 * 1000000
        )
        
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
            sorted_users = sorted(user_status.items(), 
                                key=lambda x: x[1].get('last_time', ''), reverse=True)
            
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
    
    display = AttendanceDisplay()
    display.run(update_interval=2)


if __name__ == "__main__":
    main()
